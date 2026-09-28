"""Resumo Semanal: numeros-chave de uma Semana numa tela so (termos em CONTEXT.md)."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.core.plan_status import PENDENTE
from src.core.plan_utils import ASSINANTE, CATEGORIAS, GYM_TOTALPASS, PACOTE, categoria_do_plano
from src.data.models import Frequencia, Membro, Pagamento
from src.utils.utils import create_whatsapp_link

N_SEMANAS = 12
LIMIAR_CANDIDATO = 8       # check-ins Gym/Totalpass na janela de 4 Semanas
MIN_CHECKINS_CELULA = 5    # celula do mapa de calor so vira destaque com esse volume
HORAS = list(range(7, 23))
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
DIAS_EXTENSO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
FAIXAS = [("até 17", 0, 17), ("18–24", 18, 24), ("25–34", 25, 34), ("35–44", 35, 44), ("45+", 45, 200)]
PAGANTES = {ASSINANTE, PACOTE}   # lado "que paga" de uma Conversao ou Perda
KPIS = ("checkins", "pct_gt", "receita")


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
        Pagamento.data_pagamento, Pagamento.valor, Pagamento.tipo_transacao, Pagamento.nova_data_vencimento
    ).filter(Pagamento.data_pagamento.isnot(None)).all()
    return membros, checkins, pagamentos


def _receita_competencia_assinante(pagamentos, seg: date) -> float:
    fim = seg + timedelta(days=7)
    total = 0.0
    for data_pag, valor, tipo, vence in pagamentos:
        if not vence or "treino" in (tipo or "").lower():
            continue
        inicio = data_pag.date()
        dias = max((vence - inicio).days, 1)
        sobreposicao = (min(vence, fim) - max(inicio, seg)).days
        if sobreposicao > 0:
            total += valor * sobreposicao / dias
    return total


def _mapa_de_calor(janela):
    total, gt = Counter(), Counter()
    for _, dt, categoria, _ in janela:
        if dt.weekday() < 6 and dt.hour in HORAS:  # domingo e madrugada ficam fora do mapa
            total[dt.weekday(), dt.hour] += 1
            gt[dt.weekday(), dt.hour] += categoria == GYM_TOTALPASS
    celulas = [[[total[d, h], gt[d, h]] for h in HORAS] for d in range(6)]
    destaques = sorted(
        (k for k, n in total.items() if n >= MIN_CHECKINS_CELULA),
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


def _vencidos(membros, da_semana, hoje: date):
    ids = {c[0] for c in da_semana if c[2] == ASSINANTE}
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


def _perfil(membros, janela, seg: date):
    categoria_por_membro = {c[0]: c[2] for c in janela}
    perfil = {}
    for categoria in (GYM_TOTALPASS, ASSINANTE):
        grupo = [membros[i] for i, c in categoria_por_membro.items() if c == categoria]
        perfil[categoria] = {
            "idade": Counter(_faixa(m.data_nascimento, seg) for m in grupo),
            "genero": Counter(m.genero or "Não informado" for m in grupo),
        }
    return perfil


def _nomes(membros, ids):
    return sorted(membros[i].nome for i in ids)


def _semana(seg: date, hoje: date, membros, checkins, pagamentos) -> dict:
    fim = seg + timedelta(days=7)
    inicio_janela = seg - timedelta(days=21)
    da_semana = [c for c in checkins if seg <= c[1].date() < fim]
    janela = [c for c in checkins if inicio_janela <= c[1].date() < fim]

    por_categoria = Counter(c[2] for c in da_semana)
    total, gt, assinantes = len(da_semana), por_categoria[GYM_TOTALPASS], por_categoria[ASSINANTE]
    pag_semana = [p for p in pagamentos if seg <= p[0].date() < fim]
    receita_gt = sum(p[1] for p in pag_semana if p[2] in ("Gympass", "Totalpass"))

    por_dia = {categoria: [0] * 6 for categoria in CATEGORIAS}
    for _, dt, categoria, _ in da_semana:
        if dt.weekday() < 6:  # domingo conta no total, mas nao ganha coluna
            por_dia[categoria][dt.weekday()] += 1

    return {
        "segunda": seg.isoformat(),
        "rotulo": f"{seg:%d/%m} – {seg + timedelta(days=5):%d/%m}",
        "checkins": total,
        "pct_gt": round(100 * gt / total, 1) if total else 0.0,
        "receita": round(sum(p[1] for p in pag_semana), 2),
        "valor_visita_gt": round(receita_gt / gt, 2) if gt else 0.0,
        "valor_visita_assinante": (
            round(_receita_competencia_assinante(pagamentos, seg) / assinantes, 2) if assinantes else 0.0),
        "por_dia": {categoria: v for categoria, v in por_dia.items() if any(v)},
        **_mapa_de_calor(janela),
        "conversoes": _nomes(membros, {c[0] for c in da_semana if c[3] == GYM_TOTALPASS and c[2] in PAGANTES}),
        "perdas": _nomes(membros, {c[0] for c in da_semana if c[3] in PAGANTES and c[2] == GYM_TOTALPASS}),
        "candidatos": _candidatos(membros, janela),
        "vencidos": _vencidos(membros, da_semana, hoje),
        "perfil": _perfil(membros, janela, seg),
    }


def montar_semanas(session: Session, hoje: date) -> list:
    """As 12 ultimas Semanas fechadas, da mais recente [0] para a mais antiga."""
    membros, checkins, pagamentos = _carregar(session)
    ultima = semana_fechada(hoje)
    # +4 Semanas so para os comparativos da Semana mais antiga
    semanas = [_semana(ultima - timedelta(weeks=i), hoje, membros, checkins, pagamentos)
               for i in range(N_SEMANAS + 4)]
    for i, s in enumerate(semanas[:N_SEMANAS]):
        s["anterior"] = {k: semanas[i + 1][k] for k in KPIS}
        s["media4"] = {k: round(sum(semanas[i + j][k] for j in range(1, 5)) / 4, 1) for k in KPIS}
    return semanas[:N_SEMANAS]
