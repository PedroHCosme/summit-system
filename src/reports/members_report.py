"""Gerador de relatorio de membros com foco em retencao."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from src.data.db import create_session
from src.reports._common import get_reports_dir, get_template_env
from src.reports.analytics import (
    SEGMENTO_MUITO_ATIVO,
    SEGMENTO_REATIVACAO_URGENTE,
    SEGMENTO_RISCO_ALTO,
    SEGMENTO_RISCO_MODERADO,
    ReportAnalyticsService,
    period_bounds,
)


def _to_date(value: Optional[datetime | date], fallback: date) -> date:
    if value is None:
        return fallback
    return value.date() if isinstance(value, datetime) else value


def _render_script(script_template: str, row: dict) -> str:
    payload = {
        "nome": row.get("nome") or "membro",
        "plano": row.get("plano") or "plano atual",
        "dias_desde_ultimo_checkin": row.get("dias_desde_ultimo_checkin", 0),
    }
    return script_template.format(**payload)


def generate_members_report(
    db_session: Optional[Session] = None,
    order_by: str = "nome_asc",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    period_label: str = "Geral",
) -> str:
    """
    Gera relatorio de membros orientado a retencao.

    Mantem o entrypoint existente para preservar compatibilidade com callers.
    """
    del order_by  # Ordenacao agora segue prioridade de retencao.

    close_session = False
    if db_session is None:
        db_session = create_session()
        close_session = True

    try:
        today = date.today()
        sd = _to_date(start_date, today.replace(day=1))
        ed = _to_date(end_date, today)

        analytics = ReportAnalyticsService(db_session)
        retention = analytics.compute_member_features(sd, ed)

        action_queues = retention["action_queues"]
        scripts = retention["outreach_scripts"]
        for queue_key, rows in action_queues.items():
            script_template = scripts.get(queue_key, "")
            for row in rows:
                row["script_preview"] = _render_script(script_template, row)

        clientes_perdendo = (
            action_queues.get(SEGMENTO_REATIVACAO_URGENTE, [])
            + action_queues.get(SEGMENTO_RISCO_ALTO, [])
            + action_queues.get(SEGMENTO_RISCO_MODERADO, [])
        )
        clientes_ativos = action_queues.get(SEGMENTO_MUITO_ATIVO, [])

        segment_items = retention["segment_distribution"]["items"]
        segment_chart_json = json.dumps(
            {
                "labels": [item["label"] for item in segment_items],
                "values": [item["count"] for item in segment_items],
            }
        )
        risk_funnel_json = json.dumps(
            {
                "labels": ["Risco moderado", "Risco alto", "Reativacao urgente"],
                "values": [
                    len(action_queues.get(SEGMENTO_RISCO_MODERADO, [])),
                    len(action_queues.get(SEGMENTO_RISCO_ALTO, [])),
                    len(action_queues.get(SEGMENTO_REATIVACAO_URGENTE, [])),
                ],
            }
        )

        report_title = f"Relatorio de Membros - {period_label}" if period_label else "Relatorio de Membros"
        start_dt, end_dt = period_bounds(sd, ed)
        period_display = f"{start_dt.strftime('%d/%m/%Y')} a {end_dt.strftime('%d/%m/%Y')}"

        context = {
            "title": report_title,
            "subtitle": "Central de Retencao de Membros",
            "period_display": period_display,
            "generate_date": datetime.now().strftime("%d/%m/%Y as %H:%M"),
            "current_year": datetime.now().year,
            "executive_summary": retention["executive_summary"],
            "segment_distribution": retention["segment_distribution"],
            "action_queues": action_queues,
            "outreach_scripts": scripts,
            "retention_recommendations": retention["retention_recommendations"],
            "comparison_previous_period": retention["comparison_previous_period"],
            "list_data": retention["list_data"],
            "clientes_perdendo": clientes_perdendo,
            "clientes_muito_ativos": clientes_ativos,
            "segment_chart_json": segment_chart_json,
            "risk_funnel_json": risk_funnel_json,
        }

        env = get_template_env()
        template = env.get_template("members_report.html")
        html_output = template.render(**context)

        reports_dir = get_reports_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"relatorio_membros_{timestamp}.html"
        filepath = reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as report_file:
            report_file.write(html_output)

        return str(filepath)
    finally:
        if close_session:
            db_session.close()

