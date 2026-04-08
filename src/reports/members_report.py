"""Gerador de relatorio de membros."""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import func
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader

from src.data.db import create_session
from src.data.models import Membro, Frequencia
from src.services.plan_service import PlanService
from src.core.plan_status import (
    PENDENTE,
    calcular_status_plano,
    calcular_status_membro,
    STATUS_PLANO_EM_DIA,
    STATUS_PLANO_VENCIDO,
    STATUS_PLANO_SEM_VENCIMENTO,
    STATUS_MEMBRO_ATIVO,
    STATUS_MEMBRO_INATIVO,
)
from src.utils.date_utils import parse_date_to_date


def _get_reports_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def _get_template_env() -> Environment:
    project_root = Path(__file__).parent.parent.parent
    templates_dir = project_root / "src" / "templates" / "reports"
    return Environment(loader=FileSystemLoader(str(templates_dir)))


def generate_members_report(
    db_session: Optional[Session] = None,
    order_by: str = "nome_asc",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period_label: str = "Geral"
) -> str:
    """
    Gera relatorio completo de membros.

    - Status do plano (EM DIA / VENCIDO / SEM VENCIMENTO): baseado em data
    - Status do membro (ATIVO / INATIVO): baseado em frequencia de check-ins
    - Membros PENDENTE sao excluidos de todos os calculos
    """
    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True

    try:
        # Metadados de planos para calculos de status
        plan_service = PlanService(db_session=db_session)
        planos_dict = plan_service.get_plans_as_dict()

        # Converter datas do periodo
        sd: Optional[date] = None
        ed: Optional[date] = None
        if start_date is not None:
            sd = start_date.date() if isinstance(start_date, datetime) else start_date
        if end_date is not None:
            ed = end_date.date() if isinstance(end_date, datetime) else end_date

        # Subquery: ultimo check-in por membro
        ultimo_checkin_sq = (
            db_session.query(
                Frequencia.member_id,
                func.max(Frequencia.checkin_datetime).label("ultimo_checkin"),
            )
            .group_by(Frequencia.member_id)
            .subquery()
        )

        # Query principal: membros + ultimo check-in, excluindo PENDENTE
        query = (
            db_session.query(Membro, ultimo_checkin_sq.c.ultimo_checkin)
            .outerjoin(ultimo_checkin_sq, Membro.id == ultimo_checkin_sq.c.member_id)
            .filter(Membro.estado_plano != PENDENTE)
        )

        if order_by == "nome_asc":
            query = query.order_by(Membro.nome.asc())
        elif order_by == "nome_desc":
            query = query.order_by(Membro.nome.desc())

        resultados = query.all()

        # Contadores
        total = len(resultados)
        planos_em_dia = 0
        planos_vencidos = 0
        planos_sem_vencimento = 0
        membros_ativos_freq = 0
        membros_inativos_freq = 0
        novos_no_periodo = 0
        churned = 0

        planos_contagem: Dict[str, int] = {}
        list_data: List[Dict[str, Any]] = []

        for membro, ultimo_checkin in resultados:
            plano_nome = membro.plano or "Sem Plano"
            plano_info = planos_dict.get(plano_nome, {})
            is_quota = plano_info.get("is_quota", False)
            valor_por_checkin = plano_info.get("valor_por_checkin", 0.0)

            # --- Status do Plano (baseado em data de vencimento) ---
            sp = calcular_status_plano(
                vencimento_plano=membro.vencimento_plano,
                estado_plano_db=membro.estado_plano,
                is_quota=is_quota,
                valor_por_checkin=valor_por_checkin,
            )

            if sp == STATUS_PLANO_EM_DIA:
                planos_em_dia += 1
            elif sp == STATUS_PLANO_VENCIDO:
                planos_vencidos += 1
            else:
                planos_sem_vencimento += 1

            # --- Status do Membro (baseado em frequencia de check-ins) ---
            sm = calcular_status_membro(
                plano_nome=plano_nome,
                ultimo_checkin=ultimo_checkin,
                voucher_credits=membro.voucher_credits or 0,
                is_quota=is_quota,
                valor_por_checkin=valor_por_checkin,
            )

            if sm == STATUS_MEMBRO_ATIVO:
                membros_ativos_freq += 1
            else:
                membros_inativos_freq += 1

            # --- Metricas do periodo selecionado ---
            if sd is not None and ed is not None:
                if membro.data_cadastro and sd <= membro.data_cadastro <= ed:
                    novos_no_periodo += 1
                if (membro.vencimento_plano
                        and sd <= membro.vencimento_plano <= ed
                        and sp == STATUS_PLANO_VENCIDO):
                    churned += 1

            # --- Formatacao para o template ---
            venc_display = "Sem vencimento"
            dias_restantes = None
            if membro.vencimento_plano:
                d_obj = parse_date_to_date(str(membro.vencimento_plano))
                if d_obj:
                    venc_display = d_obj.strftime("%d/%m/%Y")
                    dias_restantes = (d_obj - date.today()).days

            ultimo_ci_display = "Nunca"
            if ultimo_checkin:
                try:
                    uc = ultimo_checkin.date() if hasattr(ultimo_checkin, "date") else ultimo_checkin
                    ultimo_ci_display = uc.strftime("%d/%m/%Y")
                except Exception:
                    ultimo_ci_display = str(ultimo_checkin)[:10]

            planos_contagem[plano_nome] = planos_contagem.get(plano_nome, 0) + 1

            list_data.append({
                "nome": membro.nome or "Sem Nome",
                "plano": plano_nome,
                "status_plano": sp,
                "status_membro": sm,
                "vencimento_plano": venc_display,
                "dias_restantes": dias_restantes,
                "ultimo_checkin": ultimo_ci_display,
            })

        # Taxa de retencao (membros ativos em relacao aos que poderiam ter churnado)
        denom_retencao = membros_ativos_freq + churned
        retention_pct = (membros_ativos_freq / denom_retencao * 100) if denom_retencao > 0 else 0.0

        planos_labels = list(planos_contagem.keys())
        planos_values = list(planos_contagem.values())

        report_title = f"Relatorio de Membros - {period_label}" if period_label else "Relatorio de Membros"

        context = {
            "title": report_title,
            "generate_date": datetime.now().strftime('%d/%m/%Y as %H:%M'),
            "current_year": datetime.now().year,
            "stats": {
                "total": total,
                "planos_em_dia": planos_em_dia,
                "planos_vencidos": planos_vencidos,
                "planos_sem_vencimento": planos_sem_vencimento,
                "membros_ativos_freq": membros_ativos_freq,
                "membros_inativos_freq": membros_inativos_freq,
                "novos_no_periodo": novos_no_periodo,
                "churned": churned,
                "retention_pct": round(retention_pct, 1),
            },
            "list_data": list_data,
            "status_chart_json": json.dumps({
                "labels": ["Em Dia", "Vencidos", "Sem Vencimento"],
                "values": [planos_em_dia, planos_vencidos, planos_sem_vencimento],
            }),
            "atividade_chart_json": json.dumps({
                "labels": ["Frequentando", "Inativos"],
                "values": [membros_ativos_freq, membros_inativos_freq],
            }),
            "planos_chart_json": json.dumps({
                "labels": planos_labels,
                "values": planos_values,
            }),
        }

        env = _get_template_env()
        template = env.get_template("members_report.html")
        html_output = template.render(**context)

        reports_dir = _get_reports_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_membros_{timestamp}.html"
        filepath = reports_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_output)

        return str(filepath)

    finally:
        if close_session:
            db_session.close()
