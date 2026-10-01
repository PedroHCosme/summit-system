"""Membro arquivado: mais de 90 dias sem check-in, sem plano vigente e sem pagamento recente."""
from datetime import date, datetime, time, timedelta

import pytest

from src.core.plan_status import esta_arquivado
from src.data.models import Frequencia, Membro, Pagamento
from src.reports._common import ids_arquivados

HOJE = date(2026, 10, 1)


def _dia(dias_atras, hora=10):
    return datetime.combine(HOJE - timedelta(days=dias_atras), time(hora))


def _arquivado(**campos):
    base = dict(ultimo_checkin=None, ultimo_pagamento=None, vencimento_plano=None,
                vencimento_treino=None, data_cadastro=None)
    return esta_arquivado(**{**base, **campos}, hoje=HOJE)


@pytest.mark.parametrize("dias, esperado", [(90, False), (91, True)])
def test_limite_de_90_dias_do_ultimo_checkin(dias, esperado):
    assert _arquivado(ultimo_checkin=_dia(dias)) is esperado


@pytest.mark.parametrize("campo", ["vencimento_plano", "vencimento_treino"])
def test_plano_ou_treino_vigente_protege(campo):
    velho = _dia(200)
    assert _arquivado(ultimo_checkin=velho, **{campo: HOJE}) is False
    assert _arquivado(ultimo_checkin=velho, **{campo: HOJE - timedelta(days=1)}) is True


@pytest.mark.parametrize("dias, esperado", [(90, False), (91, True)])
def test_pagamento_recente_protege(dias, esperado):
    assert _arquivado(ultimo_checkin=_dia(200), ultimo_pagamento=_dia(dias, 11)) is esperado


@pytest.mark.parametrize("cadastro_ha, esperado", [(30, False), (91, True)])
def test_quem_nunca_fez_checkin_conta_desde_o_cadastro(cadastro_ha, esperado):
    assert _arquivado(data_cadastro=HOJE - timedelta(days=cadastro_ha)) is esperado


def test_checkin_vale_mais_que_o_cadastro():
    assert _arquivado(ultimo_checkin=_dia(200), data_cadastro=HOJE - timedelta(days=5)) is True


def test_sem_nenhuma_data_esta_arquivado():
    assert _arquivado() is True


def test_ids_arquivados_le_o_banco(db_session):
    def membro(nome, **campos):
        m = Membro(nome=nome, plano="Mensal", estado_plano="ATIVO", **campos)
        db_session.add(m)
        db_session.flush()
        return m

    sumido = membro("Sumido")
    ativo = membro("Ativo")
    pagou = membro("Pagou")
    vigente = membro("Vigente", vencimento_plano=HOJE + timedelta(days=5))
    for m, dias in ((sumido, 120), (ativo, 3), (pagou, 120), (vigente, 120)):
        db_session.add(Frequencia(member_id=m.id, checkin_datetime=_dia(dias), plano="Mensal"))
    db_session.add(Pagamento(member_id=pagou.id, data_pagamento=_dia(10), tipo_transacao="Renovacao Plano", valor=190.0))
    db_session.flush()

    assert ids_arquivados(db_session, HOJE) == {sumido.id}
