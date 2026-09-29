"""Resumo Mensal: Meses fechados e os 4 blocos so do Mes (novos, renovacoes, evolucao, inativos)."""
from datetime import date, datetime, time
from pathlib import Path

import pytest

from src.data.models import Frequencia, Membro, Pagamento
from src.reports.monthly_summary import generate_monthly_summary, mes_fechado, montar_meses

HOJE = date(2026, 10, 5)  # ultimo Mes fechado: setembro/2026


@pytest.mark.parametrize("hoje, primeiro_dia", [
    (date(2026, 9, 28), date(2026, 8, 1)),   # setembro ainda nao fechou
    (date(2026, 10, 1), date(2026, 9, 1)),   # dia 1: o mes passado fechou
    (date(2027, 1, 15), date(2026, 12, 1)),  # virada de ano
])
def test_mes_fechado(hoje, primeiro_dia):
    assert mes_fechado(hoje) == primeiro_dia


def _membro(s, nome, plano, cadastro=None, estado=None):
    m = Membro(nome=nome, plano=plano, data_cadastro=cadastro, estado_plano=estado,
               whatsapp="(31) 99999-0000")
    s.add(m)
    s.flush()
    return m


def _checkin(s, m, dia):
    s.add(Frequencia(member_id=m.id, checkin_datetime=datetime.combine(dia, time(18)), plano=m.plano))


def _pagamento(s, m, dia, vence):
    s.add(Pagamento(member_id=m.id, data_pagamento=datetime.combine(dia, time(10)),
                    tipo_transacao="Renovação Plano", valor=190.0, nova_data_vencimento=vence))


@pytest.fixture
def meses(db_session):
    s = db_session
    ana = _membro(s, "Ana", "Mensal", cadastro=date(2026, 9, 10))      # nova, voltou
    bia = _membro(s, "Bia", "Gympass", cadastro=date(2026, 9, 12))     # nova, nao voltou
    _membro(s, "Caio", "Mensal", cadastro=date(2026, 8, 30))           # cadastrada fora do mes
    for dia in (date(2026, 9, 10), date(2026, 9, 17)):
        _checkin(s, ana, dia)
    _checkin(s, bia, date(2026, 9, 12))

    dani = _membro(s, "Dani", "Mensal")                                # venceu 19/09 e renovou
    _pagamento(s, dani, date(2026, 8, 20), date(2026, 9, 19))
    _pagamento(s, dani, date(2026, 9, 19), date(2026, 10, 19))
    edu = _membro(s, "Edu", "Mensal")                                  # venceu 24/09 e nao renovou
    _pagamento(s, edu, date(2026, 8, 25), date(2026, 9, 24))
    fabio = _membro(s, "Fabio", "Trimestral")                          # vence so em dezembro
    _pagamento(s, fabio, date(2026, 9, 1), date(2026, 12, 1))
    gil = _membro(s, "Gil", "Gympass")                                 # nao e Assinante
    _pagamento(s, gil, date(2026, 8, 25), date(2026, 9, 24))

    hugo = _membro(s, "Hugo", "Mensal")                                # treinou em agosto, sumiu
    for dia in (date(2026, 8, 5), date(2026, 8, 12)):
        _checkin(s, hugo, dia)
    iara = _membro(s, "Iara", "Mensal")                                # treinou nos dois meses
    _checkin(s, iara, date(2026, 8, 10))
    _checkin(s, iara, date(2026, 9, 15))
    joao = _membro(s, "Joao", "Mensal")                                # so em julho: nao conta
    _checkin(s, joao, date(2026, 7, 20))
    lia = _membro(s, "Lia", "Mensal", estado="PENDENTE")               # PENDENTE fica fora de tudo
    _checkin(s, lia, date(2026, 8, 3))
    s.flush()
    return montar_meses(s, HOJE)


def test_doze_meses_do_mais_recente_para_o_mais_antigo(meses):
    assert len(meses) == 12
    assert meses[0]["rotulo"] == "Setembro/2026"
    assert meses[-1]["rotulo"] == "Outubro/2025"


def test_checkin_de_outro_mes_nao_entra_nos_totais(meses):
    assert meses[0]["checkins"] == 4          # Ana x2, Bia, Iara em setembro
    assert meses[1]["checkins"] == 3          # agosto: Hugo x2 e Iara (Lia e PENDENTE, fica fora)
    assert set(meses[0]["media"]) == {"checkins", "pct_gt", "receita"}


def test_evolucao_semana_a_semana(meses):
    evolucao = meses[0]["evolucao"]
    assert [b["rotulo"] for b in evolucao] == [
        "01/09 – 06/09", "07/09 – 13/09", "14/09 – 20/09", "21/09 – 27/09", "28/09 – 30/09"]
    assert [b["checkins"] for b in evolucao] == [0, 2, 2, 0, 0]
    assert evolucao[1]["pct_gt"] == 50.0      # Bia (Gympass) e Ana na semana de 07/09
    assert evolucao[2]["receita"] == 190.0    # pagamento da Dani em 19/09


def test_membros_novos(meses):
    novos = meses[0]["novos"]
    assert novos["total"] == 2 and novos["voltaram"] == 1
    assert novos["por_categoria"] == [
        {"categoria": "Assinante", "total": 1, "voltaram": 1},
        {"categoria": "Gym/Totalpass", "total": 1, "voltaram": 0},
    ]


def test_renovacoes(meses):
    renovacoes = meses[0]["renovacoes"]
    assert renovacoes["venciam"] == 2 and renovacoes["renovaram"] == 1
    assert [(r["nome"], r["vencimento"]) for r in renovacoes["nao_renovaram"]] == [("Edu", "24/09/2026")]
    assert renovacoes["nao_renovaram"][0]["whatsapp"].startswith("https://wa.me/")


def test_inativos(meses):
    inativos = meses[0]["inativos"]
    assert [(i["nome"], i["checkins"]) for i in inativos] == [("Hugo", 2)]
    assert inativos[0]["whatsapp"].startswith("https://wa.me/")


def test_gera_html_mensal(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("src.reports.weekly_summary.get_reports_dir", lambda: tmp_path)
    html = Path(generate_monthly_summary(db_session=db_session, hoje=HOJE)).read_text(encoding="utf-8")
    assert "<title>Resumo Mensal" in html
    assert '"rotulo": "Setembro/2026"' in html
    assert '"mensal": true' in html
    for bloco in ('id="evolucao"', 'id="novos"', 'id="nao-renovaram"', 'id="inativos"'):
        assert bloco in html
