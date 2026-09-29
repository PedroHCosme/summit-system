"""Resumo Mensal: o motor do Resumo Semanal com janela de Mes, mais 4 blocos so do Mes.

Mes = calendario fechado, dia 1 ao ultimo dia (termos em CONTEXT.md).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from src.core.plan_utils import ASSINANTE, CATEGORIAS, categoria_do_plano
from src.data.db import create_session
from src.reports.weekly_summary import _carregar, _comparar, _kpis, _periodo, gerar_html
from src.utils.utils import create_whatsapp_link

N_MESES = 12
N_MEDIA_MESES = 3
MIN_CELULA_MES = 5   # o Mes tem ~4x os check-ins da Semana, entao o limite do semanal (3) subiria para 5
MESES = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")
TERMOS = {
    "periodo": "Mês", "prefixo": "", "receita": "Receita do Mês",
    "por_dia": "Check-ins por dia da semana (soma do mês)", "mapa": "Lotação (mês inteiro)",
    "media": "média 3 meses", "vazio": "Ninguém neste mês", "mensal": True,
}


def _mes_anterior(primeiro_dia: date) -> date:
    return (primeiro_dia - timedelta(days=1)).replace(day=1)


def _proximo_mes(primeiro_dia: date) -> date:
    return (primeiro_dia.replace(day=28) + timedelta(days=4)).replace(day=1)


def mes_fechado(hoje: date) -> date:
    """Dia 1 do ultimo Mes fechado (o Mes de `hoje` ainda esta aberto)."""
    return _mes_anterior(hoje.replace(day=1))


def _evolucao(ini: date, fim: date, checkins, pagamentos) -> list:
    """Blocos segunda-domingo recortados ao Mes: check-ins, % Gym/Totalpass e Receita de cada um."""
    blocos, dia = [], ini
    while dia < fim:
        ate = min(dia + timedelta(days=7 - dia.weekday()), fim)
        no_bloco = [c for c in checkins if dia <= c[1].date() < ate]
        pag_bloco = [p for p in pagamentos if dia <= p[0].date() < ate]
        blocos.append({"rotulo": f"{dia:%d/%m} – {ate - timedelta(days=1):%d/%m}",
                       **_kpis(no_bloco, pag_bloco)})
        dia = ate
    return blocos


def _novos(membros, checkins, ini: date, fim: date) -> dict:
    """Cadastros do Mes por Categoria de Cliente; voltou = 2 ou mais check-ins ate o fim do Mes."""
    total_de_checkins = Counter(c[0] for c in checkins if c[1].date() < fim)
    por_categoria = {}
    for m in membros.values():
        if m.data_cadastro and ini <= m.data_cadastro < fim:
            categoria = categoria_do_plano(m.plano)
            item = por_categoria.setdefault(categoria, {"categoria": categoria, "total": 0, "voltaram": 0})
            item["total"] += 1
            item["voltaram"] += total_de_checkins[m.id] >= 2
    itens = [por_categoria[c] for c in CATEGORIAS if c in por_categoria]
    return {"total": sum(i["total"] for i in itens), "voltaram": sum(i["voltaram"] for i in itens),
            "por_categoria": itens}


def _renovacoes(membros, pagamentos, ini: date, fim: date) -> dict:
    """Assinantes com vencimento no Mes; renovou = existe pagamento com vencimento posterior."""
    vencimentos = defaultdict(list)
    for _, _, tipo, vence, mid in pagamentos:
        if vence and mid in membros and "treino" not in (tipo or "").lower():
            vencimentos[mid].append(vence)
    venciam = []  # (membro, vencimento no Mes, renovou)
    for mid, lista in vencimentos.items():
        m = membros[mid]
        no_mes = [v for v in lista if ini <= v < fim]
        if no_mes and categoria_do_plano(m.plano) == ASSINANTE:
            v = max(no_mes)
            venciam.append((m, v, any(outro > v for outro in lista)))
    nao = sorted(((m, v) for m, v, renovou in venciam if not renovou), key=lambda t: (t[1], t[0].nome))
    return {
        "venciam": len(venciam),
        "renovaram": sum(renovou for _, _, renovou in venciam),
        "nao_renovaram": [
            {"nome": m.nome, "plano": m.plano, "vencimento": v.strftime("%d/%m/%Y"),
             "whatsapp": create_whatsapp_link(m.whatsapp or "")}
            for m, v in nao
        ],
    }


def _inativos(membros, checkins, ini: date, fim: date, ini_anterior: date) -> list:
    """Treinaram no Mes anterior e nao vieram neste."""
    vieram = {c[0] for c in checkins if ini <= c[1].date() < fim}
    anterior = Counter(c[0] for c in checkins if ini_anterior <= c[1].date() < ini)
    lista = [
        {"nome": membros[mid].nome, "checkins": n, "whatsapp": create_whatsapp_link(membros[mid].whatsapp or "")}
        for mid, n in anterior.items() if mid not in vieram
    ]
    return sorted(lista, key=lambda i: (-i["checkins"], i["nome"]))


def montar_meses(session: Session, hoje: date) -> list:
    """Os 12 ultimos Meses fechados, do mais recente [0] para o mais antigo."""
    membros, checkins, pagamentos = _carregar(session)
    limites, ini = [], mes_fechado(hoje)
    # +3 Meses so para os comparativos do Mes mais antigo
    for _ in range(N_MESES + N_MEDIA_MESES):
        limites.append((ini, _proximo_mes(ini)))
        ini = _mes_anterior(ini)
    periodos = [
        _periodo(i, f, f"{MESES[i.month - 1]}/{i.year}", hoje, membros, checkins, pagamentos, MIN_CELULA_MES)
        for i, f in limites
    ]
    meses = _comparar(periodos, N_MESES, N_MEDIA_MESES)
    for mes, (ini, fim) in zip(meses, limites):
        mes.update({
            "evolucao": _evolucao(ini, fim, checkins, pagamentos),
            "novos": _novos(membros, checkins, ini, fim),
            "renovacoes": _renovacoes(membros, pagamentos, ini, fim),
            "inativos": _inativos(membros, checkins, ini, fim, _mes_anterior(ini)),
        })
    return meses


def generate_monthly_summary(db_session: Optional[Session] = None, hoje: Optional[date] = None) -> str:
    """Gera o HTML do Resumo Mensal e devolve o caminho do arquivo."""
    hoje = hoje or date.today()
    session = db_session or create_session()
    try:
        meses = montar_meses(session, hoje)
    finally:
        if db_session is None:
            session.close()
    return gerar_html(meses, title="Resumo Mensal",
                      subtitle="Gym/Totalpass, lotação, retenção e ações do mês",
                      termos=TERMOS, prefixo="resumo_mensal")
