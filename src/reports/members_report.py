"""Gerador de relatório de membros."""

from __future__ import annotations

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader

from src.data.db import create_session
from src.data.models import Membro
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

def calculate_dias_restantes(vencimento_str: Optional[str]) -> int:
    """Calcula dias restantes até o vencimento."""
    if not vencimento_str:
        return 0
    
    venc_date = parse_date_to_date(vencimento_str)
    if not venc_date:
        return 0
        
    hoje = date.today()
    delta = venc_date - hoje
    return delta.days

def determine_status_simples(estado_plano: str, vencimento_str: str) -> str:
    """Retorna um status consolidado (ATIVO, INATIVO, PERÍODO DE GRAÇA)"""
    estado_upper = estado_plano.upper() if estado_plano else "ATIVO"
    
    # Se o sistema já marcou como período de graça
    if "GRAÇA" in estado_upper:
        return "PERÍODO DE GRAÇA"
        
    # Calcular baseado nas regras reais
    dias = calculate_dias_restantes(vencimento_str)
    
    # Tolerância de 5 dias após vencimento
    if dias >= 0:
        return "ATIVO"
    elif dias >= -5:
        return "PERÍODO DE GRAÇA"
    else:
        return "INATIVO"

def generate_members_report(
    db_session: Optional[Session] = None,
    order_by: str = "nome_asc",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period_label: str = "Geral"
) -> str:
    """
    Gera relatório completo de membros ordenado conforme parâmetro.
    """
    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True
        
    try:
        # Extrair todos os membros do ORM (sem paginação, relatórios são plenos)
        query = db_session.query(Membro)
        
        # Ordenação básica do backend 
        # A ordenação avançada e filtragem pode ocorrer no Jinja/JS
        if order_by == "nome_asc":
            query = query.order_by(Membro.nome.asc())
        elif order_by == "nome_desc":
            query = query.order_by(Membro.nome.desc())
        
        membros = query.all()
        
        # Converter start_date/end_date para date objects se necessário
        sd = None
        ed = None
        if start_date is not None:
            sd = start_date.date() if isinstance(start_date, datetime) else start_date
        if end_date is not None:
            ed = end_date.date() if isinstance(end_date, datetime) else end_date

        # Estatísticas
        total = len(membros)
        ativos = 0
        inativos = 0
        graca = 0
        novos_no_periodo = 0
        churned = 0

        planos_contagem = {}

        list_data = []

        for m in membros:
            venc_str = m.vencimento_plano
            # Converter a Date para formatar bonitinho
            if venc_str:
                d_obj = parse_date_to_date(str(venc_str))
                if d_obj:
                    venc_str = d_obj.strftime("%d/%m/%Y")
            else:
                venc_str = "Sem Plano"

            status_calc = determine_status_simples(m.estado_plano, str(m.vencimento_plano))
            dias_restantes = calculate_dias_restantes(str(m.vencimento_plano))

            # Incrementar estatísticas
            if status_calc == "ATIVO": ativos += 1
            elif status_calc == "INATIVO": inativos += 1
            elif status_calc == "PERÍODO DE GRAÇA": graca += 1

            # Métricas do período
            if sd is not None and ed is not None:
                # Novos no período: data_cadastro dentro do intervalo
                if m.data_cadastro and sd <= m.data_cadastro <= ed:
                    novos_no_periodo += 1

                # Churn: vencimento dentro do período E status INATIVO
                if m.vencimento_plano and sd <= m.vencimento_plano <= ed and status_calc == "INATIVO":
                    churned += 1

            p_nome = m.plano if m.plano else "Sem Plano"
            if p_nome not in planos_contagem:
                planos_contagem[p_nome] = 0
            planos_contagem[p_nome] += 1

            list_data.append({
                "nome": m.nome or "Sem Nome",
                "plano": p_nome,
                "status": status_calc,
                "vencimento_plano": venc_str,
                "dias_restantes": dias_restantes
            })

        # Taxa de retenção
        if sd is not None and ed is not None:
            denom = ativos + churned
            retention_pct = (ativos / denom) * 100 if denom > 0 else 0.0
        else:
            retention_pct = 0.0

        # Preparar dados para o Gráfico de Planos
        planos_labels = list(planos_contagem.keys())
        planos_values = list(planos_contagem.values())

        # Preparar dicionário de contexto Jinja
        report_title = f"Relatório de Membros — {period_label}" if period_label else "Relatório Geral de Membros"

        context = {
            "title": report_title,
            "generate_date": datetime.now().strftime('%d/%m/%Y às %H:%M'),
            "current_year": datetime.now().year,
            "stats": {
                "total": total,
                "ativos": ativos,
                "inativos": inativos,
                "graca": graca,
                "novos_no_periodo": novos_no_periodo,
                "churned": churned,
                "retention_pct": retention_pct
            },
            "list_data": list_data,
            "status_chart_json": json.dumps({
                "labels": ["Ativos", "Inativos", "Período de Graça"],
                "values": [ativos, inativos, graca]
            }),
            "planos_chart_json": json.dumps({
                "labels": planos_labels,
                "values": planos_values
            })
        }
        
        # Renderização do Jinja
        env = _get_template_env()
        template = env.get_template("members_report.html")
        html_output = template.render(**context)
        
        # Salvar arquivo HTML
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
