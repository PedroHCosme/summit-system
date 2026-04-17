"""Gerador de relatório financeiro."""

from __future__ import annotations

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from jinja2 import Environment, FileSystemLoader

from src.services.payment_service import PaymentService
from src.services.member_service import MemberService
from src.services.plan_service import PlanService


# =============================================================================
# Classificacao DRE — mapeamento de tipo_transacao para categoria
# =============================================================================

# Palavras-chave que identificam receita de TREINO PERSONAL
_PALAVRAS_TREINO = ("TREINO", "PERSONAL", " PT ")

# Palavras-chave que identificam MENSALIDADES / RENOVACOES / VOUCHERS
_PALAVRAS_MENSALIDADE = (
    "RENOVA",   # Renovação Plano Mensal, Renovação Plano Trimestral...
    "VOUCHER",  # Compra Voucher Pacote 10
    "COMPRA",   # Compra de plano genérico
    "MENSAL",   # Mensal, Mens. c/ Treino
    "TRIMEST",  # Trimestral
    "SEMEST",   # Semestral
    "ANUAL",    # Anual
    "ESCOLINHA",
)


def _categoria_dre(tipo: str) -> str:
    """
    Classifica tipo_transacao em categoria do DRE.

    Returns:
        "treino" | "mensalidades" | "avulsos"
    """
    t = (tipo or "").upper()
    if any(k in t for k in _PALAVRAS_TREINO):
        return "treino"
    if any(k in t for k in _PALAVRAS_MENSALIDADE):
        return "mensalidades"
    # Diária, Gympass, Totalpass, Check-in, e qualquer outro
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

def generate_finance_report(
    period: str,
    start_date: datetime,
    end_date: datetime,
    payment_service: Optional[PaymentService] = None,
    member_service: Optional[MemberService] = None
) -> str:
    """
    Gera relatório financeiro (DRE/DFC) do período especificado usando Jinja2.
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
        # Carregar planos do banco (fonte de verdade — não config.py)
        plan_service = PlanService(db_session=member_service.session)
        planos_precos = plan_service.get_plan_prices()
        planos_checkin = plan_service.get_checkin_payment_plans()

        # Obter dados operacionais através dos Serviços já tipados do sistema
        summary = payment_service.get_summary(start_date, end_date)
        breakdown = payment_service.get_breakdown(start_date, end_date)
        transactions = payment_service.get_transactions(start_date, end_date, limit=200)

        # =====================================================================
        # (a) Comparativo com período anterior
        # =====================================================================
        period_duration = end_date - start_date
        prev_end = start_date - timedelta(days=1)
        prev_start = prev_end - period_duration

        comparativo = None
        try:
            prev_summary = payment_service.get_summary(prev_start, prev_end)
            receita_anterior = prev_summary.total_receita
            transacoes_anterior = prev_summary.total_transacoes

            delta_receita_pct = (
                ((summary.total_receita - receita_anterior) / receita_anterior * 100)
                if receita_anterior > 0 else 0.0
            )
            delta_transacoes_pct = (
                ((summary.total_transacoes - transacoes_anterior) / transacoes_anterior * 100)
                if transacoes_anterior > 0 else 0.0
            )

            comparativo = {
                "receita_anterior": receita_anterior,
                "delta_receita_pct": round(delta_receita_pct, 1),
                "transacoes_anterior": transacoes_anterior,
                "delta_transacoes_pct": round(delta_transacoes_pct, 1),
            }
        except Exception:
            comparativo = None

        # =====================================================================
        # (b) Taxa de inadimplência — excluindo PENDENTE
        # =====================================================================
        inadimplencia = None
        try:
            members = member_service.get_all_excluding_pending()
            total_membros = len(members)
            inativos = sum(1 for m in members if m.estado_plano == 'INATIVO')
            taxa_pct = (inativos / total_membros * 100) if total_membros > 0 else 0.0

            inadimplencia = {
                "total_membros": total_membros,
                "inativos": inativos,
                "taxa_pct": round(taxa_pct, 1),
            }
        except Exception:
            inadimplencia = None

        # =====================================================================
        # (c) Projeção de receita mensal (usando preços do banco)
        # =====================================================================
        projecao_receita = 0.0
        try:
            ativos = [m for m in members if m.estado_plano == 'ATIVO']
            period_duration = end_date - start_date
            dias_periodo = max(period_duration.days, 1)
            for m in ativos:
                plano_nome = m.plano or ""
                preco = planos_precos.get(plano_nome, 0.0)
                projecao_receita += preco
                # Planos per-checkin: estimar com base na média do período
                if plano_nome in planos_checkin:
                    preco_checkin = planos_checkin[plano_nome]
                    if summary.total_transacoes > 0:
                        checkins_por_dia = summary.total_transacoes / dias_periodo
                        projecao_receita += preco_checkin * checkins_por_dia * 30
                    else:
                        projecao_receita += preco_checkin * 8  # fallback conservador
            projecao_receita = round(projecao_receita, 2)
        except Exception:
            projecao_receita = 0.0

        # Processar Extrato Formatado
        extrato_formatado = []

        for t in transactions: # transactions é List[Dict[str, Any]]
            membro_nome = t.get("member_nome") or "Sistema / Avulso"

            # Formatar Data
            data_fmt = "—"
            dt_val = t.get("data_pagamento")
            if dt_val:
                try:
                    # dt_val pode ser string ou datetime a depender de como tá modelado
                    if isinstance(dt_val, str):
                        d_obj = datetime.fromisoformat(dt_val.replace('Z', '+00:00'))
                        data_fmt = d_obj.strftime("%d/%m/%Y")
                    else:
                        data_fmt = dt_val.strftime("%d/%m/%Y")
                except Exception:
                    data_fmt = str(dt_val)

            extrato_formatado.append({
                "data": data_fmt,
                "membro": membro_nome,
                "plano": t.get("tipo_transacao") or "Produto/Avulso",
                "metodo": t.get("metodo_pagamento") or "Não Informado",
                "status": "PAGO", # Simulando sucesso retroativo
                "total": t.get("valor", 0.0)
            })

        # KPIs Básicos
        v_total = summary.total_receita
        t_count = summary.total_transacoes
        t_medio = summary.ticket_medio

        kpis = {
            "receita_bruta": v_total,
            "ticket_medio": t_medio,
            "total_transacoes": t_count,
            # Descontos nao sao rastreados no modelo Pagamento — campo removido do DRE
            "receita_liquida": v_total,
        }

        # DRE Simplificado — classificacao robusta por tipo_transacao
        mensalidades = 0.0
        treino_receita = 0.0
        avulsos_receita = 0.0

        categorias_auditoria: Dict[str, str] = {}  # tipo_transacao -> categoria
        for b in breakdown:
            cat = _categoria_dre(b.tipo_transacao)
            categorias_auditoria[b.tipo_transacao or "Outros"] = cat
            if cat == "treino":
                treino_receita += b.total_valor
            elif cat == "mensalidades":
                mensalidades += b.total_valor
            else:
                avulsos_receita += b.total_valor

        dre = {
            "mensalidades": mensalidades,
            "treino": treino_receita,
            "avulsos": avulsos_receita,
        }

        # Auditoria: DRE total deve bater com receita bruta do servico
        dre_total = mensalidades + treino_receita + avulsos_receita
        diferenca = round(v_total - dre_total, 2)
        auditoria = {
            "receita_bruta": v_total,
            "dre_total": round(dre_total, 2),
            "diferenca": diferenca,
            "balanceado": abs(diferenca) < 0.01,
            "categorias": sorted(
                [{"tipo": k, "categoria": v} for k, v in categorias_auditoria.items()],
                key=lambda x: (x["categoria"], x["tipo"])
            ),
        }

        # Gráficos — agregar por método usando breakdown completo do serviço
        metodos_map: Dict[str, float] = {}
        for t in transactions:
            m = t.get("metodo_pagamento") or "Outros"
            metodos_map[m] = metodos_map.get(m, 0.0) + t.get("valor", 0.0)

        metodos_labels = list(metodos_map.keys())
        metodos_values = list(metodos_map.values())

        planos_labels = [b.tipo_transacao or "Outros" for b in breakdown]
        planos_values = [b.total_valor for b in breakdown]

        context = {
            "title": f"Balanço Financeiro — {period}",
            "subtitle": "Demonstrativo de Resultados e Análise de Receita",
            "generate_date": datetime.now().strftime('%d/%m/%Y às %H:%M'),
            "current_year": datetime.now().year,
            "kpis": kpis,
            "dre": dre,
            "auditoria": auditoria,
            "transacoes": extrato_formatado,
            "comparativo": comparativo,
            "inadimplencia": inadimplencia,
            "projecao_receita": projecao_receita,
            "chart_json": json.dumps({
                "methods": {"labels": metodos_labels, "values": metodos_values},
                "plans":   {"labels": planos_labels,  "values": planos_values},
            }),
        }
        
        # Renderizar com Jinja2
        env = _get_template_env()
        template = env.get_template("finance_report.html")
        html_output = template.render(**context)
        
        # Salvar arquivo HTML
        reports_dir = _get_reports_dir()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Adicionar o período à string sanitizada para o arquivo
        safe_period = period.replace("/", "_").replace(" ", "_")
        filename = f"relatorio_financeiro_{safe_period}_{timestamp}.html"
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_output)
            
        return str(filepath)
    
    finally:
        if close_session and session is not None:
            session.close()
