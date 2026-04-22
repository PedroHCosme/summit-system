"""Gerador de relatorio financeiro com foco em retencao e decisao."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader

from src.reports.analytics import (
    SEGMENTO_MUITO_ATIVO,
    SEGMENTO_REATIVACAO_URGENTE,
    SEGMENTO_RISCO_ALTO,
    ReportAnalyticsService,
    period_bounds,
    previous_period_bounds,
)
from src.services.member_service import MemberService
from src.services.payment_service import PaymentService


_PALAVRAS_TREINO = ("TREINO", "PERSONAL", " PT ")
_PALAVRAS_MENSALIDADE = (
    "RENOVA",
    "VOUCHER",
    "COMPRA",
    "MENSAL",
    "TRIMEST",
    "SEMEST",
    "ANUAL",
    "ESCOLINHA",
)


def _categoria_dre(tipo: str) -> str:
    t = (tipo or "").upper()
    if any(k in t for k in _PALAVRAS_TREINO):
        return "treino"
    if any(k in t for k in _PALAVRAS_MENSALIDADE):
        return "mensalidades"
    return "avulsos"


def _get_reports_dir() -> Path:
    project_root = Path(__file__).parent.parent.parent
    reports_dir = project_root / "relatorios"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def _get_template_env() -> Environment:
    project_root = Path(__file__).parent.parent.parent
    templates_dir = project_root / "src" / "templates" / "reports"
    return Environment(loader=FileSystemLoader(str(templates_dir)))


def _safe_delta_pct(current: float, previous: float) -> float:
    if previous <= 0:
        return 0.0
    return round(((current - previous) / previous) * 100, 1)


def _build_financial_recommendations(
    risk_metrics: Dict[str, Any],
    segment_revenue: List[Dict[str, Any]],
    comparison: Dict[str, Any],
) -> List[Dict[str, str]]:
    recs: List[Dict[str, str]] = []
    receita_risco = risk_metrics.get("receita_em_risco", 0.0)
    receita_total = risk_metrics.get("receita_realizada", 0.0)
    if receita_total > 0 and receita_risco / receita_total > 0.35:
        recs.append(
            {
                "titulo": "Ativar operacao de blindagem de receita",
                "descricao": "Receita em risco acima de 35% da receita realizada no periodo.",
                "impacto": "alto",
                "esforco": "rapido",
            }
        )

    muito_ativo = next((s for s in segment_revenue if s["segment"] == SEGMENTO_MUITO_ATIVO), None)
    if muito_ativo and muito_ativo["pct_receita"] > 45:
        recs.append(
            {
                "titulo": "Programa de fidelidade para base premium",
                "descricao": "Concentracao alta de receita em membros muito ativos. Reduzir risco de concentracao.",
                "impacto": "medio",
                "esforco": "medio",
            }
        )

    if comparison.get("delta_ticket_pct", 0.0) < -8:
        recs.append(
            {
                "titulo": "Revisar mix de produtos e ticket medio",
                "descricao": "Ticket medio caiu de forma relevante vs periodo anterior.",
                "impacto": "medio",
                "esforco": "estrutural",
            }
        )

    if comparison.get("delta_risk_revenue_pct", 0.0) > 10:
        recs.append(
            {
                "titulo": "Contato prioritario para risco alto e urgente",
                "descricao": "Receita em risco aumentou frente ao periodo anterior.",
                "impacto": "alto",
                "esforco": "rapido",
            }
        )

    if not recs:
        recs.append(
            {
                "titulo": "Manter monitoramento semanal de risco financeiro",
                "descricao": "Indicadores estaveis no periodo atual. Sustentar rotina de acompanhamento.",
                "impacto": "baixo",
                "esforco": "rapido",
            }
        )

    return recs[:5]


def generate_finance_report(
    period: str,
    start_date: datetime,
    end_date: datetime,
    payment_service: Optional[PaymentService] = None,
    member_service: Optional[MemberService] = None,
) -> str:
    """
    Gera relatorio financeiro retention-first mantendo entrypoint atual.
    """
    from src.data.db import create_session

    close_session = False
    session = None

    if payment_service is None or member_service is None:
        session = create_session()
        payment_service = PaymentService(db_session=session)
        member_service = MemberService(db_session=session)
        close_session = True

    try:
        start_dt, end_dt = period_bounds(start_date, end_date)
        prev_start_dt, prev_end_dt = previous_period_bounds(start_date, end_date)
        period_days = max((end_dt.date() - start_dt.date()).days + 1, 1)

        summary = payment_service.get_summary(start_dt, end_dt)
        prev_summary = payment_service.get_summary(prev_start_dt, prev_end_dt)
        breakdown = payment_service.get_breakdown(start_dt, end_dt)
        transactions = payment_service.get_transactions(start_dt, end_dt, limit=5000)

        analytics = ReportAnalyticsService(member_service.session)
        retention_current = analytics.compute_member_features(start_dt, end_dt)
        retention_previous = analytics.compute_member_features(prev_start_dt, prev_end_dt)

        member_features = retention_current["member_features"]
        prev_features = retention_previous["member_features"]

        # DRE e auditoria
        mensalidades = 0.0
        treino_receita = 0.0
        avulsos_receita = 0.0
        categorias_auditoria: Dict[str, str] = {}
        for item in breakdown:
            categoria = _categoria_dre(item.tipo_transacao)
            categorias_auditoria[item.tipo_transacao or "Outros"] = categoria
            if categoria == "mensalidades":
                mensalidades += item.total_valor
            elif categoria == "treino":
                treino_receita += item.total_valor
            else:
                avulsos_receita += item.total_valor

        dre = {
            "mensalidades": mensalidades,
            "treino": treino_receita,
            "avulsos": avulsos_receita,
        }
        dre_total = mensalidades + treino_receita + avulsos_receita
        diferenca = round(summary.total_receita - dre_total, 2)
        auditoria = {
            "receita_bruta": summary.total_receita,
            "dre_total": round(dre_total, 2),
            "diferenca": diferenca,
            "balanceado": abs(diferenca) < 0.01,
            "categorias": sorted(
                [{"tipo": k, "categoria": v} for k, v in categorias_auditoria.items()],
                key=lambda row: (row["categoria"], row["tipo"]),
            ),
        }

        # Receita por segmento de retencao
        receita_total_membros = sum(feature.valor_receita_periodo for feature in member_features)
        segment_totais: Dict[str, float] = {}
        for feature in member_features:
            segment_totais[feature.segmento] = segment_totais.get(feature.segmento, 0.0) + feature.valor_receita_periodo

        segment_revenue = []
        for item in retention_current["segment_distribution"]["items"]:
            total_segmento = segment_totais.get(item["segment"], 0.0)
            pct_receita = (total_segmento / receita_total_membros * 100) if receita_total_membros > 0 else 0.0
            segment_revenue.append(
                {
                    "segment": item["segment"],
                    "label": item["label"],
                    "receita": round(total_segmento, 2),
                    "pct_receita": round(pct_receita, 1),
                }
            )

        # Receita em risco e recuperavel
        receita_em_risco = sum(
            f.valor_mensal_estimado
            for f in member_features
            if f.segmento in (SEGMENTO_RISCO_ALTO, SEGMENTO_REATIVACAO_URGENTE)
        )
        receita_recuperavel = sum(
            f.valor_mensal_estimado * (0.5 if f.segmento == SEGMENTO_RISCO_ALTO else 0.35)
            for f in member_features
            if f.segmento in (SEGMENTO_RISCO_ALTO, SEGMENTO_REATIVACAO_URGENTE)
        )
        receita_em_risco_prev = sum(
            f.valor_mensal_estimado
            for f in prev_features
            if f.segmento in (SEGMENTO_RISCO_ALTO, SEGMENTO_REATIVACAO_URGENTE)
        )
        risk_revenue_metrics = {
            "receita_realizada": round(summary.total_receita, 2),
            "receita_em_risco": round(receita_em_risco, 2),
            "receita_recuperavel": round(receita_recuperavel, 2),
        }

        # Ranking de fontes de receita (tipo + metodo + plano)
        metodos_map: Dict[str, float] = {}
        for tx in transactions:
            metodo = tx.get("metodo_pagamento") or "Nao informado"
            metodos_map[metodo] = metodos_map.get(metodo, 0.0) + float(tx.get("valor") or 0.0)

        planos_map: Dict[str, float] = {}
        for feature in member_features:
            planos_map[feature.plano] = planos_map.get(feature.plano, 0.0) + feature.valor_receita_periodo

        total_receita_rank = max(summary.total_receita, 1.0)
        ranking_pool: List[Dict[str, Any]] = []
        for item in breakdown:
            ranking_pool.append(
                {
                    "categoria": "Tipo",
                    "nome": item.tipo_transacao or "Outros",
                    "valor": round(item.total_valor, 2),
                    "pct": round(item.total_valor / total_receita_rank * 100, 1),
                }
            )
        for metodo, valor in metodos_map.items():
            ranking_pool.append(
                {
                    "categoria": "Metodo",
                    "nome": metodo,
                    "valor": round(valor, 2),
                    "pct": round(valor / total_receita_rank * 100, 1),
                }
            )
        for plano, valor in planos_map.items():
            ranking_pool.append(
                {
                    "categoria": "Plano",
                    "nome": plano,
                    "valor": round(valor, 2),
                    "pct": round(valor / total_receita_rank * 100, 1),
                }
            )
        ranking_pool = [row for row in ranking_pool if row["valor"] > 0]
        ranking_pool.sort(key=lambda row: row["valor"], reverse=True)
        top_fontes_receita = ranking_pool[:8]
        menores_fontes_receita = sorted(ranking_pool, key=lambda row: row["valor"])[:8]

        # Comparativo com periodo anterior
        comparison_previous_period = {
            "start_date": prev_start_dt.strftime("%d/%m/%Y"),
            "end_date": prev_end_dt.strftime("%d/%m/%Y"),
            "period_days": period_days,
            "delta_receita_pct": _safe_delta_pct(summary.total_receita, prev_summary.total_receita),
            "delta_transacoes_pct": _safe_delta_pct(summary.total_transacoes, prev_summary.total_transacoes),
            "delta_ticket_pct": _safe_delta_pct(summary.ticket_medio, prev_summary.ticket_medio),
            "delta_risk_revenue_pct": _safe_delta_pct(receita_em_risco, receita_em_risco_prev),
        }

        retention_recommendations = _build_financial_recommendations(
            risk_metrics=risk_revenue_metrics,
            segment_revenue=segment_revenue,
            comparison=comparison_previous_period,
        )

        # Lista operacional (transacoes)
        extrato_formatado = []
        for tx in transactions[:250]:
            dt_value = tx.get("data_pagamento")
            data_fmt = "—"
            if dt_value:
                try:
                    if isinstance(dt_value, str):
                        data_fmt = datetime.fromisoformat(dt_value.replace("Z", "+00:00")).strftime("%d/%m/%Y")
                    else:
                        data_fmt = dt_value.strftime("%d/%m/%Y")
                except Exception:
                    data_fmt = str(dt_value)[:10]
            extrato_formatado.append(
                {
                    "data": data_fmt,
                    "membro": tx.get("member_nome") or "Sistema / Avulso",
                    "plano": tx.get("tipo_transacao") or "Produto/Avulso",
                    "metodo": tx.get("metodo_pagamento") or "Nao Informado",
                    "status": "PAGO",
                    "total": float(tx.get("valor") or 0.0),
                }
            )

        # Graficos de alta acao
        segment_chart_json = json.dumps(
            {
                "labels": [item["label"] for item in segment_revenue],
                "values": [item["receita"] for item in segment_revenue],
            }
        )
        risk_vs_revenue_json = json.dumps(
            {
                "labels": ["Receita realizada", "Receita em risco", "Receita recuperavel"],
                "values": [
                    risk_revenue_metrics["receita_realizada"],
                    risk_revenue_metrics["receita_em_risco"],
                    risk_revenue_metrics["receita_recuperavel"],
                ],
            }
        )

        context = {
            "title": f"Balanco Financeiro - {period}",
            "subtitle": "Economia de Retencao e Resultado Operacional",
            "generate_date": datetime.now().strftime("%d/%m/%Y as %H:%M"),
            "current_year": datetime.now().year,
            "executive_summary": {
                "receita_bruta": round(summary.total_receita, 2),
                "ticket_medio": round(summary.ticket_medio, 2),
                "total_transacoes": summary.total_transacoes,
                "receita_em_risco": risk_revenue_metrics["receita_em_risco"],
            },
            "segment_distribution": retention_current["segment_distribution"],
            "action_queues": retention_current["action_queues"],
            "outreach_scripts": retention_current["outreach_scripts"],
            "retention_recommendations": retention_recommendations,
            "risk_revenue_metrics": risk_revenue_metrics,
            "comparison_previous_period": comparison_previous_period,
            "segment_revenue": segment_revenue,
            "top_fontes_receita": top_fontes_receita,
            "menores_fontes_receita": menores_fontes_receita,
            "dre": dre,
            "auditoria": auditoria,
            "transacoes": extrato_formatado,
            "segment_chart_json": segment_chart_json,
            "risk_vs_revenue_json": risk_vs_revenue_json,
        }

        env = _get_template_env()
        template = env.get_template("finance_report.html")
        html_output = template.render(**context)

        reports_dir = _get_reports_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_period = period.replace("/", "_").replace(" ", "_")
        filename = f"relatorio_financeiro_{safe_period}_{timestamp}.html"
        filepath = reports_dir / filename

        with open(filepath, "w", encoding="utf-8") as report_file:
            report_file.write(html_output)

        return str(filepath)
    finally:
        if close_session and session is not None:
            session.close()

