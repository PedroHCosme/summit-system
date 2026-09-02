"""Gerador de relatório de frequência."""

from __future__ import annotations

import os
import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, desc, case, extract, cast, Integer
from sqlalchemy.orm import Session

from src.data.db import create_session
from src.data.models import Frequencia, Membro
from src.core.plan_status import PENDENTE
from src.reports._common import get_reports_dir, get_template_env

def generate_frequency_report(
    db_session: Optional[Session] = None,
    days: int = 30,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> str:
    """
    Gera relatório de frequência dos últimos N dias.
    """
    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True

    try:
        # Período de análise
        if start_date is not None and end_date is not None:
            # Recalculate days from the actual date range for percentage calculations
            days = max((end_date - start_date).days, 1)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        # Filtro base
        base_query = db_session.query(Frequencia).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        )

        # Estatísticas gerais
        total_checkins = base_query.count()
        unique_members = db_session.query(func.count(func.distinct(Frequencia.member_id))).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).scalar() or 0
        
        avg_daily = total_checkins / days if days > 0 else 0

        # Dia mais movimentado
        busiest_day_row = db_session.query(
            func.date(Frequencia.checkin_datetime).label("dia"),
            func.count(Frequencia.id).label("total")
        ).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by(func.date(Frequencia.checkin_datetime)).order_by(desc("total")).first()

        _busiest_raw = busiest_day_row.dia if busiest_day_row else None
        busiest_day_total = busiest_day_row.total if busiest_day_row else 0
        if _busiest_raw:
            try:
                busiest_day_date = datetime.strptime(str(_busiest_raw), "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                busiest_day_date = str(_busiest_raw)
        else:
            busiest_day_date = "N/A"

        # Top 10 membros
        top_members_rows = db_session.query(
            Membro.nome,
            Membro.plano,
            func.count(Frequencia.id).label("total")
        ).join(Membro, Frequencia.member_id == Membro.id).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by(Frequencia.member_id, Membro.nome, Membro.plano).order_by(desc("total")).limit(10).all()

        top_members = []
        for mem in top_members_rows:
            percentage = (mem.total / days) * 100 if days > 0 else 0
            top_members.append({
                "nome": mem.nome,
                "plano": mem.plano,
                "total": mem.total,
                "percentage": percentage
            })

        # Frequência por dia da semana (Extração de Dia Semanal no SQLite (0=Dom, 1=Seg...))
        # Para compatibilidade multi-banco (SQLite -> strftime('%w'))
        weekday_rows = db_session.query(
            cast(func.strftime('%w', Frequencia.checkin_datetime), Integer).label("dia_semana"),
            func.count(Frequencia.id).label("total")
        ).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by("dia_semana").order_by(desc("total")).all()

        weekday_map = {0: "Domingo", 1: "Segunda", 2: "Terça", 3: "Quarta", 4: "Quinta", 5: "Sexta", 6: "Sábado"}
        weekday_stats = []
        for row in weekday_rows:
            pct = (row.total / total_checkins * 100) if total_checkins > 0 else 0
            weekday_stats.append({
                "nome": weekday_map.get(row.dia_semana, str(row.dia_semana)),
                "total": row.total,
                "percentage": pct
            })

        # Frequência por Plano
        plan_rows = db_session.query(
            Membro.plano,
            func.count(Frequencia.id).label("total")
        ).join(Membro, Frequencia.member_id == Membro.id).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by(Membro.plano).order_by(desc("total")).all()

        plan_stats = []
        for row in plan_rows:
            pct = (row.total / total_checkins * 100) if total_checkins > 0 else 0
            plan_stats.append({
                "nome": row.plano,
                "total": row.total,
                "percentage": pct
            })

        # Extraindo dados para o Gráfico de Linha (Últimos N Dias agrupados por dia)
        trend_rows = db_session.query(
            func.date(Frequencia.checkin_datetime).label("dia"),
            func.count(Frequencia.id).label("total")
        ).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).group_by(func.date(Frequencia.checkin_datetime)).order_by("dia").all()

        chart_labels = []
        chart_values = []
        
        # Opcional: preencher os buracos dos dias sem nenhum check-in 
        # (Para o chart ficar contínuo nos buracos de finais de semana ou fechamento)
        current_date_iter = start_date.date()
        end_date_iter = end_date.date()
        trend_dict = {row.dia: row.total for row in trend_rows}
        
        while current_date_iter <= end_date_iter:
            date_str = current_date_iter.strftime('%Y-%m-%d')
            display_str = current_date_iter.strftime('%d/%m')
            
            chart_labels.append(display_str)
            chart_values.append(trend_dict.get(date_str, 0))
            
            current_date_iter += timedelta(days=1)

        # Membros em Risco de Churn: plano ATIVO mas sem check-in no periodo
        # Excluir PENDENTE (cadastro nao aprovado)
        checked_in_ids_sq = db_session.query(Frequencia.member_id).filter(
            Frequencia.checkin_datetime >= start_date,
            Frequencia.checkin_datetime <= end_date
        ).distinct()

        # Subquery: ultimo check-in global de cada membro (fora do periodo)
        ultimo_ci_sq = (
            db_session.query(
                Frequencia.member_id,
                func.max(Frequencia.checkin_datetime).label("ultimo_checkin"),
            )
            .group_by(Frequencia.member_id)
            .subquery()
        )

        at_risk_rows = (
            db_session.query(Membro.nome, Membro.plano, Membro.whatsapp, ultimo_ci_sq.c.ultimo_checkin)
            .outerjoin(ultimo_ci_sq, Membro.id == ultimo_ci_sq.c.member_id)
            .filter(
                Membro.estado_plano == 'ATIVO',
                Membro.estado_plano != PENDENTE,
                ~Membro.id.in_(checked_in_ids_sq),
            )
            .order_by(Membro.nome)
            .all()
        )

        at_risk_members = []
        for m in at_risk_rows:
            ultimo_ci_display = "Nunca"
            if m.ultimo_checkin:
                try:
                    uc = m.ultimo_checkin.date() if hasattr(m.ultimo_checkin, "date") else m.ultimo_checkin
                    ultimo_ci_display = uc.strftime("%d/%m/%Y")
                except Exception:
                    ultimo_ci_display = str(m.ultimo_checkin)[:10]
            at_risk_members.append({
                "nome": m.nome,
                "plano": m.plano,
                "whatsapp": m.whatsapp or "",
                "ultimo_checkin": ultimo_ci_display,
            })

        # Preparar dicionário de contexto para o Jinja
        context = {
            "title": "Relatório de Frequência",
            "subtitle": f"Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} ({days} dias)",
            "generate_date": datetime.now().strftime('%d/%m/%Y às %H:%M'),
            "current_year": datetime.now().year,
            "stats": {
                "total_checkins": total_checkins,
                "unique_members": unique_members,
                "avg_daily": avg_daily,
                "busiest_day_date": busiest_day_date,
                "busiest_day_total": busiest_day_total
            },
            "top_members": top_members,
            "weekday_stats": weekday_stats,
            "plan_stats": plan_stats,
            "at_risk_members": at_risk_members,
            "chart_data_json": json.dumps({
                "labels": chart_labels,
                "values": chart_values
            })
        }

        # Renderizar com Jinja2
        env = get_template_env()
        template = env.get_template("frequency_report.html")
        html_output = template.render(**context)

        # Salvar arquivo HTML
        reports_dir = get_reports_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"relatorio_frequencia_{timestamp}.html"
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        return str(filepath)
        
    finally:
        if close_session:
            db_session.close()
