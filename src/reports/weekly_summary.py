"""Resumo Semanal: numeros-chave de uma Semana numa tela so (termos em CONTEXT.md).

O motor (`_periodo`) tambem serve ao Resumo Mensal (monthly_summary.py).
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.plan_status import PENDENTE
from src.core.plan_utils import ASSINANTE, CATEGORIAS, GYM_TOTALPASS, PACOTE, categoria_do_plano
from src.data.db import create_session
from src.data.models import Frequencia, Membro, Pagamento
from src.reports._common import get_reports_dir, get_template_env
from src.utils.utils import create_whatsapp_link

N_SEMANAS = 12
N_MEDIA_SEMANAS = 4
LIMIAR_CANDIDATO = 8       # check-ins Gym/Totalpass na janela de 4 Semanas
MIN_CELULA_SEMANA = 3      # celula do mapa so vira destaque com esse volume (uma Semana tem poucos check-ins)
JANELA_DIAS = 28           # Candidatos e Perfil: 4 Semanas terminando no fim do periodo
HORAS = list(range(7, 23))
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
DIAS_EXTENSO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
FAIXAS = [("até 17", 0, 17), ("18–24", 18, 24), ("25–34", 25, 34), ("35–44", 35, 44), ("45+", 45, 200)]
PAGANTES = {ASSINANTE, PACOTE}   # lado "que paga" de uma Conversao ou Perda
KPIS = ("checkins", "pct_gt", "receita")
TERMOS = {
    "periodo": "Semana", "prefixo": "Semana ", "receita": "Receita da Semana",
    "por_dia": "Check-ins por dia", "mapa": "Lotação (desta semana)",
    "media": "média 4 sem.", "vazio": "Ninguém nesta semana", "mensal": False,
}


def semana_fechada(hoje: date) -> date:
    """Segunda-feira da ultima Semana fechada (a Semana vai de segunda a domingo)."""
    return hoje - timedelta(days=hoje.weekday() + 7)


def _carregar(session: Session):
    # ponytail: carrega todo o historico em memoria (~8 mil check-ins/ano); filtrar por janela se passar de 100 mil
    membros = {
        m.id: m
        for m in session.query(Membro).filter(
            or_(Membro.estado_plano.is_(None), Membro.estado_plano != PENDENTE)
        )
    }
    ultima_categoria = {}
    checkins = []  # (member_id, datetime, categoria, categoria do check-in anterior do membro)
    consulta = (
        session.query(Frequencia.member_id, Frequencia.checkin_datetime,
                      func.coalesce(Frequencia.plano, Membro.plano))
        .join(Membro, Frequencia.member_id == Membro.id)
        .order_by(Frequencia.checkin_datetime)
    )
    for mid, dt, plano in consulta:
        if mid not in membros:
            continue
        categoria = categoria_do_plano(plano)
        checkins.append((mid, dt, categoria, ultima_categoria.get(mid)))
        ultima_categoria[mid] = categoria
    pagamentos = session.query(
        Pagamento.data_pagamento, Pagamento.valor, Pagamento.tipo_transacao,
        Pagamento.nova_data_vencimento, Pagamento.member_id,
    ).filter(Pagamento.data_pagamento.isnot(None)).all()
    return membros, checkins, pagamentos


def _receita_competencia_assinante(pagamentos, ini: date, fim: date) -> float:
    total = 0.0
    for data_pag, valor, tipo, vence, _ in pagamentos:
        if not vence or "treino" in (tipo or "").lower():
            continue
        inicio = data_pag.date()
        dias = max((vence - inicio).days, 1)
        sobreposicao = (min(vence, fim) - max(inicio, ini)).days
        if sobreposicao > 0:
            total += valor * sobreposicao / dias
    return total


def _mapa_de_calor(no_periodo, min_celula: int):
    total, gt = Counter(), Counter()
    for _, dt, categoria, _ in no_periodo:
        if dt.weekday() < 6 and dt.hour in HORAS:  # domingo e madrugada ficam fora do mapa
            total[dt.weekday(), dt.hour] += 1
            gt[dt.weekday(), dt.hour] += categoria == GYM_TOTALPASS
    celulas = [[[total[d, h], gt[d, h]] for h in HORAS] for d in range(6)]
    destaques = sorted(
        (k for k, n in total.items() if n >= min_celula),
        key=lambda k: (-gt[k] / total[k], -total[k]),
    )[:2]
    frases = [
        f"{DIAS_EXTENSO[d]} {h}h: {round(100 * gt[d, h] / total[d, h])}% Gym/Totalpass ({gt[d, h]} de {total[d, h]})"
        for d, h in destaques
    ]
    return {"calor": celulas, "destaques": frases}


def _candidatos(membros, janela):
    contagem = Counter(c[0] for c in janela if c[2] == GYM_TOTALPASS)
    ultima_categoria = {c[0]: c[2] for c in janela}  # janela esta em ordem cronologica
    lista = [
        {"nome": membros[mid].nome, "checkins": n,
         "whatsapp": create_whatsapp_link(membros[mid].whatsapp or "")}
        for mid, n in contagem.items()
        if n >= LIMIAR_CANDIDATO and ultima_categoria[mid] == GYM_TOTALPASS
    ]
    return sorted(lista, key=lambda c: (-c["checkins"], c["nome"]))


def _vencidos(membros, no_periodo, hoje: date):
    ids = {c[0] for c in no_periodo if c[2] == ASSINANTE}
    vencidos = sorted(
        (m for m in (membros[i] for i in ids)
         if categoria_do_plano(m.plano) == ASSINANTE and m.vencimento_plano and m.vencimento_plano < hoje),
        key=lambda m: m.vencimento_plano,
    )
    return [
        {"nome": m.nome, "plano": m.plano, "vencimento": m.vencimento_plano.strftime("%d/%m/%Y"),
         "whatsapp": create_whatsapp_link(m.whatsapp or "")}
        for m in vencidos
    ]


def _faixa(nascimento, referencia: date) -> str:
    if not nascimento:
        return "Sem data"
    idade = referencia.year - nascimento.year - (
        (referencia.month, referencia.day) < (nascimento.month, nascimento.day))
    return next((nome for nome, menor, maior in FAIXAS if menor <= idade <= maior), "Sem data")


def _perfil(membros, janela, referencia: date):
    categoria_por_membro = {c[0]: c[2] for c in janela}
    perfil = {}
    for categoria in (GYM_TOTALPASS, ASSINANTE):
        grupo = [membros[i] for i, c in categoria_por_membro.items() if c == categoria]
        perfil[categoria] = {
            "idade": Counter(_faixa(m.data_nascimento, referencia) for m in grupo),
            "genero": Counter(m.genero or "Não informado" for m in grupo),
        }
    return perfil


def _nomes(membros, ids):
    return sorted(membros[i].nome for i in ids)


def _kpis(no_periodo, pag_periodo) -> dict:
    """Check-ins, % Gym/Totalpass e Receita (caixa) de um recorte ja filtrado."""
    gt = sum(c[2] == GYM_TOTALPASS for c in no_periodo)
    return {
        "checkins": len(no_periodo),
        "pct_gt": round(100 * gt / len(no_periodo), 1) if no_periodo else 0.0,
        "receita": round(sum(p[1] for p in pag_periodo), 2),
    }


def _periodo(ini: date, fim: date, rotulo: str, hoje: date, membros, checkins, pagamentos,
             min_celula: int) -> dict:
    """Numeros de [ini, fim): uma Semana ou um Mes."""
    janela = [c for c in checkins if fim - timedelta(days=JANELA_DIAS) <= c[1].date() < fim]
    no_periodo = [c for c in checkins if ini <= c[1].date() < fim]

    por_categoria = Counter(c[2] for c in no_periodo)
    gt, assinantes = por_categoria[GYM_TOTALPASS], por_categoria[ASSINANTE]
    pag_periodo = [p for p in pagamentos if ini <= p[0].date() < fim]
    receita_gt = sum(p[1] for p in pag_periodo if p[2] in ("Gympass", "Totalpass"))

    por_dia = {categoria: [0] * 6 for categoria in CATEGORIAS}
    for _, dt, categoria, _ in no_periodo:
        if dt.weekday() < 6:  # domingo conta no total, mas nao ganha coluna
            por_dia[categoria][dt.weekday()] += 1

    return {
        "inicio": ini.isoformat(),
        "rotulo": rotulo,
        **_kpis(no_periodo, pag_periodo),
        "valor_visita_gt": round(receita_gt / gt, 2) if gt else 0.0,
        "valor_visita_assinante": (
            round(_receita_competencia_assinante(pagamentos, ini, fim) / assinantes, 2) if assinantes else 0.0),
        "por_dia": {categoria: v for categoria, v in por_dia.items() if any(v)},
        **_mapa_de_calor(no_periodo, min_celula),
        "conversoes": _nomes(membros, {c[0] for c in no_periodo if c[3] == GYM_TOTALPASS and c[2] in PAGANTES}),
        "perdas": _nomes(membros, {c[0] for c in no_periodo if c[3] in PAGANTES and c[2] == GYM_TOTALPASS}),
        "candidatos": _candidatos(membros, janela),
        "vencidos": _vencidos(membros, no_periodo, hoje),
        "perfil": _perfil(membros, janela, ini),
    }


def _comparar(periodos: list, n: int, n_media: int) -> list:
    """Anexa `anterior` e `media` (dos n_media periodos anteriores) aos n primeiros; periodos[0] e o mais recente."""
    for i, p in enumerate(periodos[:n]):
        p["anterior"] = {k: periodos[i + 1][k] for k in KPIS}
        p["media"] = {k: round(sum(periodos[i + j][k] for j in range(1, n_media + 1)) / n_media, 1) for k in KPIS}
    return periodos[:n]


def montar_semanas(session: Session, hoje: date) -> list:
    """As 12 ultimas Semanas fechadas, da mais recente [0] para a mais antiga."""
    membros, checkins, pagamentos = _carregar(session)
    ultima = semana_fechada(hoje)
    periodos = []
    # +4 Semanas so para os comparativos da Semana mais antiga
    for i in range(N_SEMANAS + N_MEDIA_SEMANAS):
        seg = ultima - timedelta(weeks=i)
        rotulo = f"{seg:%d/%m} – {seg + timedelta(days=5):%d/%m}"
        periodos.append(_periodo(seg, seg + timedelta(days=7), rotulo, hoje,
                                 membros, checkins, pagamentos, MIN_CELULA_SEMANA))
    return _comparar(periodos, N_SEMANAS, N_MEDIA_SEMANAS)


def gerar_html(periodos: list, *, title: str, subtitle: str, termos: dict, prefixo: str) -> str:
    """Renderiza a tela unica com os periodos embutidos e devolve o caminho do arquivo."""
    dados = {"periodos": periodos, "dias": DIAS, "horas": HORAS,
             "faixas": [f[0] for f in FAIXAS] + ["Sem data"], "termos": termos}
    agora = datetime.now()
    html = get_template_env().get_template("weekly_summary.html").render(
        title=title,
        subtitle=subtitle,
        termos=termos,
        generate_date=agora.strftime("%d/%m/%Y às %H:%M"),
        current_year=agora.year,
        # "</" escapado: nomes vem do cadastro web e nao podem fechar o <script>
        dados_json=json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"),
    )
    caminho = get_reports_dir() / f"{prefixo}_{agora:%Y%m%d_%H%M%S}.html"
    caminho.write_text(html, encoding="utf-8")
    return str(caminho)


def generate_weekly_summary(db_session: Optional[Session] = None, hoje: Optional[date] = None) -> str:
    """Gera o HTML do Resumo Semanal e devolve o caminho do arquivo."""
    hoje = hoje or date.today()
    session = db_session or create_session()
    try:
        semanas = montar_semanas(session, hoje)
    finally:
        if db_session is None:
            session.close()
    return gerar_html(semanas, title="Resumo Semanal", subtitle="Gym/Totalpass, lotação e ações da semana",
                      termos=TERMOS, prefixo="resumo_semanal")
