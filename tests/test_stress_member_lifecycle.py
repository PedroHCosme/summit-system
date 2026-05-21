from collections import Counter
from datetime import date, datetime, timedelta

import pytest

from src.config import TREINO_PRECO
from src.core.payment_constants import (
    METODO_CHECKIN,
    METODO_PIX,
    TIPO_PAGAMENTO_MANUAL,
    TIPO_COMPRA_VOUCHER,
    TIPO_PAGAMENTO_TREINO,
    TIPO_RENOVACAO_PLANO,
    TIPO_VENDA_PRODUTO,
)
from src.core.plan_status import ATIVO, INATIVO, PENDENTE
from src.data.models import Membro, Pagamento, Plano
from src.services.checkin_service import CheckinService
from src.services.member_service import MemberService
from src.services.payment_service import PaymentService


PLANOS_TEMPO = {
    "Mensal": 190.0,
    "Trimestral": 500.0,
    "Semestral": 950.0,
    "Anual": 1900.0,
    "Escolinha 1x": 260.0,
    "Escolinha 2x": 360.0,
}

PLANOS_AVULSOS = {
    "Diária": 35.0,
    "Gympass": 15.0,
    "Totalpass": 15.0,
}


@pytest.fixture
def seeded_stress_plans(db_session):
    """Prepara planos realistas para cenários de stress."""
    mensal = db_session.query(Plano).filter(Plano.nome == "Mensal").first()
    mensal.preco = PLANOS_TEMPO["Mensal"]
    mensal.requer_vencimento = True
    mensal.ativo = True

    for nome, preco in PLANOS_TEMPO.items():
        if nome == "Mensal":
            continue
        db_session.add(Plano(
            nome=nome,
            preco=preco,
            requer_vencimento=True,
            ativo=True,
        ))

    for nome, valor in PLANOS_AVULSOS.items():
        db_session.add(Plano(
            nome=nome,
            preco=0.0,
            valor_por_checkin=valor,
            requer_vencimento=False,
            ativo=True,
        ))

    db_session.add_all([
        Plano(
            nome="Pacote 10",
            preco=200.0,
            is_quota=True,
            quota_amount=10,
            requer_vencimento=False,
            ativo=True,
        ),
        Plano(
            nome="Cortesia",
            preco=0.0,
            requer_vencimento=False,
            ativo=True,
        ),
    ])
    db_session.commit()


def _payments_for(db_session, member_id):
    return (
        db_session.query(Pagamento)
        .filter(Pagamento.member_id == member_id)
        .order_by(Pagamento.id)
        .all()
    )


def _payment_totals(payments):
    totals = {}
    for payment in payments:
        totals[payment.tipo_transacao] = totals.get(payment.tipo_transacao, 0.0) + payment.valor
    return totals


def test_daily_to_monthly_to_quarterly_to_daily_financial_lifecycle(db_session, seeded_stress_plans):
    """Diária cobra por uso; mensal/trimestral cobram renovação; volta à diária não cobra até check-in."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)

    result = members.create({"nome": "Fantasia Ciclo Diaria", "plano": "Diária"})
    member_id = result.member_id

    for day in (1, 2, 3):
        checkin = checkins.perform_checkin(member_id, datetime(2026, 1, day, 10, 0))
        assert checkin.success is True
        assert checkin.payment_generated is True
        assert checkin.payment_amount == 35.0

    mensal_due = date(2026, 2, 1)
    mensal = members.update_from_dict({
        "id": member_id,
        "plano": "Mensal",
        "vencimento_plano": mensal_due,
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert mensal.success is True
    assert mensal.member.vencimento_plano == mensal_due

    trimestral_due = date(2026, 5, 1)
    trimestral = members.update_from_dict({
        "id": member_id,
        "plano": "Trimestral",
        "vencimento_plano": trimestral_due,
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert trimestral.success is True
    assert trimestral.member.vencimento_plano == trimestral_due

    payments_before_daily_return = db_session.query(Pagamento).filter(
        Pagamento.member_id == member_id
    ).count()
    daily_return = members.update_from_dict({
        "id": member_id,
        "plano": "Diária",
        "vencimento_plano": date(2026, 12, 31),
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert daily_return.success is True
    assert daily_return.member.vencimento_plano is None
    assert db_session.query(Pagamento).filter(Pagamento.member_id == member_id).count() == payments_before_daily_return

    final_checkin = checkins.perform_checkin(member_id, datetime(2026, 1, 4, 10, 0))
    assert final_checkin.success is True
    assert final_checkin.payment_generated is True

    payments = _payments_for(db_session, member_id)
    counts = Counter(payment.tipo_transacao for payment in payments)
    totals = _payment_totals(payments)

    assert counts["Diária"] == 4
    assert counts[TIPO_RENOVACAO_PLANO] == 2
    assert totals["Diária"] == 140.0
    assert totals[TIPO_RENOVACAO_PLANO] == 690.0
    assert sum(payment.valor for payment in payments) == 830.0
    assert all(payment.metodo_pagamento in (METODO_CHECKIN, METODO_PIX) for payment in payments)


def test_daily_member_training_activation_expiration_and_renewal_financials(db_session, seeded_stress_plans):
    """Treino é receita separada mesmo quando o plano base é diária."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Diaria Treino",
        "plano": "Diária",
        "treina": "Não",
    })
    member_id = result.member_id

    checkin = checkins.perform_checkin(member_id, datetime(2026, 2, 1, 8, 0))
    assert checkin.success is True

    first_due = date.today() + timedelta(days=30)
    activate_training = members.update_from_dict({
        "id": member_id,
        "treina": "Sim",
        "vencimento_treino": first_due,
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert activate_training.success is True

    member = members.get_by_id(member_id)
    member.vencimento_treino = date.today() - timedelta(days=1)
    db_session.commit()

    renewed_due = date.today() + timedelta(days=60)
    renew_training = members.update_from_dict({
        "id": member_id,
        "treina": "Sim",
        "vencimento_treino": renewed_due,
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert renew_training.success is True
    assert renew_training.member.vencimento_treino == renewed_due

    payments = _payments_for(db_session, member_id)
    counts = Counter(payment.tipo_transacao for payment in payments)
    totals = _payment_totals(payments)

    assert counts["Diária"] == 1
    assert counts[TIPO_PAGAMENTO_TREINO] == 2
    assert totals["Diária"] == 35.0
    assert totals[TIPO_PAGAMENTO_TREINO] == TREINO_PRECO * 2


def test_switching_from_voucher_to_monthly_resets_voucher_balance_and_records_monthly_payment(
    db_session, seeded_stress_plans
):
    """Hoje vouchers não ficam guardados ao migrar para plano de tempo; saldo zera por mutual exclusivity."""
    members = MemberService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Voucher Para Mensal",
        "plano": "Pacote 10",
        "voucher_credits": 7,
    })
    member_id = result.member_id

    update = members.update_from_dict({
        "id": member_id,
        "plano": "Mensal",
        "vencimento_plano": date.today() + timedelta(days=30),
    }, register_payment=True, metodo_pagamento=METODO_PIX)

    assert update.success is True
    assert update.member.voucher_credits == 0
    assert update.member.vencimento_plano == date.today() + timedelta(days=30)

    payments = _payments_for(db_session, member_id)
    assert len(payments) == 1
    assert payments[0].tipo_transacao == TIPO_RENOVACAO_PLANO
    assert payments[0].valor == PLANOS_TEMPO["Mensal"]


def test_expiration_and_renewal_for_all_plan_families(db_session, seeded_stress_plans):
    """Vencimento não gera pagamento; renovação paga apenas quando existe compra/renovação."""
    members = MemberService(db_session=db_session)
    past_due = date.today() - timedelta(days=1)
    future_due = date.today() + timedelta(days=30)

    time_member_ids = []
    for plan_name in PLANOS_TEMPO:
        result = members.create({
            "nome": f"Fantasia Vencido {plan_name}",
            "plano": plan_name,
            "vencimento_plano": past_due,
            "estado_plano": ATIVO,
        })
        time_member_ids.append((plan_name, result.member_id))

    no_due_member_ids = []
    for plan_name in [*PLANOS_AVULSOS, "Pacote 10", "Cortesia"]:
        result = members.create({
            "nome": f"Fantasia Sem Vencimento {plan_name}",
            "plano": plan_name,
            "vencimento_plano": past_due,
            "voucher_credits": 5 if plan_name == "Pacote 10" else 0,
            "estado_plano": ATIVO,
        })
        no_due_member_ids.append((plan_name, result.member_id))

    assert db_session.query(Pagamento).count() == 0

    expired_count = members.update_expired_plans()

    assert expired_count == len(PLANOS_TEMPO)
    assert db_session.query(Pagamento).count() == 0

    for _, member_id in time_member_ids:
        assert members.get_by_id(member_id).estado_plano == INATIVO

    for _, member_id in no_due_member_ids:
        member = members.get_by_id(member_id)
        assert member.estado_plano == ATIVO
        assert member.vencimento_plano is None

    for plan_name, member_id in time_member_ids:
        renewal = members.update_from_dict({
            "id": member_id,
            "plano": plan_name,
            "estado_plano": ATIVO,
            "vencimento_plano": future_due,
        }, register_payment=True, metodo_pagamento=METODO_PIX)
        assert renewal.success is True
        assert renewal.member.vencimento_plano == future_due

    payments = db_session.query(Pagamento).all()
    assert len(payments) == len(PLANOS_TEMPO)
    assert all(payment.tipo_transacao == TIPO_RENOVACAO_PLANO for payment in payments)
    assert sum(payment.valor for payment in payments) == sum(PLANOS_TEMPO.values())


def test_quota_repurchase_and_per_checkin_plans_do_not_use_time_plan_renewal(db_session, seeded_stress_plans):
    """Pacote gera compra de voucher; planos por check-in só geram receita no check-in."""
    members = MemberService(db_session=db_session)

    quota = members.create({
        "nome": "Fantasia Recompra Voucher",
        "plano": "Pacote 10",
        "voucher_credits": 3,
    })
    quota_update = members.update_from_dict({
        "id": quota.member_id,
        "plano": "Pacote 10",
        "voucher_credits": 10,
    }, register_payment=True, metodo_pagamento=METODO_PIX)

    assert quota_update.success is True
    assert quota_update.member.voucher_credits == 13

    quota_payments = _payments_for(db_session, quota.member_id)
    assert len(quota_payments) == 1
    assert quota_payments[0].tipo_transacao == TIPO_COMPRA_VOUCHER
    assert quota_payments[0].valor == 200.0

    for plan_name in PLANOS_AVULSOS:
        result = members.create({
            "nome": f"Fantasia Renovacao Avulso {plan_name}",
            "plano": plan_name,
        })
        before = db_session.query(Pagamento).filter(Pagamento.member_id == result.member_id).count()
        update = members.update_from_dict({
            "id": result.member_id,
            "plano": plan_name,
            "vencimento_plano": date.today() + timedelta(days=30),
        }, register_payment=True, metodo_pagamento=METODO_PIX)
        after = db_session.query(Pagamento).filter(Pagamento.member_id == result.member_id).count()

        assert update.success is True
        assert update.member.vencimento_plano is None
        assert after == before


def test_deleting_daily_checkin_removes_only_automatic_checkin_payment(db_session, seeded_stress_plans):
    """Excluir check-in de diária remove a cobrança automática, mas mantém pagamentos manuais."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)
    payments = PaymentService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Delete Checkin",
        "plano": "Diária",
    })
    member_id = result.member_id

    checkin = checkins.perform_checkin(member_id, datetime(2026, 3, 1, 9, 0))
    manual = payments.create_payment(
        member_id=member_id,
        valor=25.0,
        tipo_transacao=TIPO_PAGAMENTO_MANUAL,
        descricao="Ajuste manual",
        metodo_pagamento=METODO_PIX,
        data_pagamento=datetime(2026, 3, 1, 9, 5),
    )
    assert checkin.success is True
    assert manual.success is True
    assert db_session.query(Pagamento).filter(Pagamento.member_id == member_id).count() == 2

    deleted = checkins.delete_checkin(checkin.checkin_id)

    assert deleted.success is True
    remaining = _payments_for(db_session, member_id)
    assert len(remaining) == 1
    assert remaining[0].tipo_transacao == TIPO_PAGAMENTO_MANUAL
    assert remaining[0].valor == 25.0


def test_editing_daily_checkin_moves_automatic_payment_and_blocks_duplicate_target_date(
    db_session, seeded_stress_plans
):
    """Editar check-in move a receita automática para a nova data e respeita 1 check-in/dia."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Edit Checkin",
        "plano": "Diária",
    })
    member_id = result.member_id

    first = checkins.perform_checkin(member_id, datetime(2026, 4, 1, 9, 0))
    second = checkins.perform_checkin(member_id, datetime(2026, 4, 3, 9, 0))
    assert first.success is True
    assert second.success is True

    moved = checkins.update_datetime(first.checkin_id, datetime(2026, 4, 2, 18, 30))
    assert moved.success is True

    moved_payment = db_session.query(Pagamento).filter(
        Pagamento.member_id == member_id,
        Pagamento.metodo_pagamento == METODO_CHECKIN,
        Pagamento.data_pagamento == datetime(2026, 4, 2, 18, 30),
    ).first()
    assert moved_payment is not None
    assert moved_payment.tipo_transacao == "Diária"

    duplicate_target = checkins.update_datetime(first.checkin_id, datetime(2026, 4, 3, 20, 0))
    assert duplicate_target.success is False
    assert "nova data" in duplicate_target.message.lower()


def test_deleting_member_removes_member_checkins_and_member_payments_from_financial_summary(
    db_session, seeded_stress_plans
):
    """Excluir membro remove seu histórico operacional e financeiro do banco atual."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)
    payments = PaymentService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Delete Member",
        "plano": "Diária",
    })
    member_id = result.member_id

    checkins.perform_checkin(member_id, datetime(2026, 5, 1, 10, 0))
    payments.create_payment(
        member_id=member_id,
        valor=99.0,
        tipo_transacao=TIPO_VENDA_PRODUTO,
        descricao="Produto teste",
        metodo_pagamento=METODO_PIX,
        data_pagamento=datetime(2026, 5, 1, 11, 0),
    )
    assert payments.get_summary().total_receita == 134.0

    deleted = members.delete(member_id)

    assert deleted.success is True
    assert members.get_by_id(member_id) is None
    assert checkins.get_member_history(member_id) == []
    assert payments.get_member_history(member_id) == []
    assert payments.get_summary().total_receita == 0.0


def test_pending_web_member_approval_does_not_create_payment_until_paid_renewal(
    db_session, seeded_stress_plans
):
    """Cadastro pendente pode ser aprovado sem cobrança; pagamento só entra na renovação paga."""
    members = MemberService(db_session=db_session)
    payments = PaymentService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Pendente Web",
        "plano": "Mensal",
        "estado_plano": PENDENTE,
        "vencimento_plano": date.today() + timedelta(days=30),
    })
    member_id = result.member_id
    assert payments.get_summary().total_transacoes == 0

    approved = members.update_from_dict({
        "id": member_id,
        "estado_plano": ATIVO,
    }, register_payment=False)
    assert approved.success is True
    assert payments.get_summary().total_transacoes == 0

    renewed = members.update_from_dict({
        "id": member_id,
        "plano": "Mensal",
        "vencimento_plano": date.today() + timedelta(days=60),
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    assert renewed.success is True

    history = _payments_for(db_session, member_id)
    assert len(history) == 1
    assert history[0].tipo_transacao == TIPO_RENOVACAO_PLANO
    assert history[0].valor == PLANOS_TEMPO["Mensal"]


def test_duplicate_manual_payments_are_allowed_and_reported_as_separate_transactions(
    db_session, seeded_stress_plans
):
    """Pagamento manual repetido é mantido como duas transações, sem deduplicação silenciosa."""
    members = MemberService(db_session=db_session)
    payments = PaymentService(db_session=db_session)

    result = members.create({
        "nome": "Fantasia Manual Duplicado",
        "plano": "Mensal",
    })
    member_id = result.member_id

    for _ in range(2):
        payment = payments.create_payment(
            member_id=member_id,
            valor=42.0,
            tipo_transacao=TIPO_PAGAMENTO_MANUAL,
            descricao="Mesmo pagamento informado duas vezes",
            metodo_pagamento=METODO_PIX,
            data_pagamento=datetime(2026, 6, 1, 12, 0),
        )
        assert payment.success is True

    summary = payments.get_summary()
    breakdown = {item.tipo_transacao: item for item in payments.get_breakdown()}

    assert summary.total_receita == 84.0
    assert summary.total_transacoes == 2
    assert breakdown[TIPO_PAGAMENTO_MANUAL].quantidade == 2
    assert breakdown[TIPO_PAGAMENTO_MANUAL].total_valor == 84.0


def test_mixed_month_financial_summary_and_breakdown_with_pending_member_excluded_from_reports(
    db_session, seeded_stress_plans
):
    """Mês misto fecha totais por categoria e relatórios ignoram membro pendente na análise de membros."""
    members = MemberService(db_session=db_session)
    checkins = CheckinService(db_session=db_session)
    payments = PaymentService(db_session=db_session)

    today = date.today()
    yesterday = today - timedelta(days=1)

    daily = members.create({"nome": "Fantasia Mes Diaria", "plano": "Diária"})
    monthly = members.create({
        "nome": "Fantasia Mes Mensal",
        "plano": "Mensal",
        "vencimento_plano": today + timedelta(days=30),
    })
    training = members.create({"nome": "Fantasia Mes Treino", "plano": "Mensal", "treina": "Não"})
    quota = members.create({"nome": "Fantasia Mes Voucher", "plano": "Pacote 10", "voucher_credits": 0})
    pending = members.create({
        "nome": "Fantasia Mes Pendente",
        "plano": "Mensal",
        "estado_plano": PENDENTE,
        "vencimento_plano": today + timedelta(days=30),
    })

    checkins.perform_checkin(daily.member_id, datetime.combine(yesterday, datetime.min.time()).replace(hour=9))
    checkins.perform_checkin(daily.member_id, datetime.combine(today, datetime.min.time()).replace(hour=9))
    members.update_from_dict({
        "id": monthly.member_id,
        "plano": "Mensal",
        "vencimento_plano": today + timedelta(days=60),
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    members.update_from_dict({
        "id": training.member_id,
        "treina": "Sim",
        "vencimento_treino": today + timedelta(days=30),
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    members.update_from_dict({
        "id": quota.member_id,
        "plano": "Pacote 10",
        "voucher_credits": 10,
    }, register_payment=True, metodo_pagamento=METODO_PIX)
    members.update_from_dict({
        "id": pending.member_id,
        "plano": "Mensal",
        "vencimento_plano": today + timedelta(days=60),
    }, register_payment=True, metodo_pagamento=METODO_PIX)

    start = datetime.combine(yesterday, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    summary = payments.get_summary(start, end)
    breakdown = {item.tipo_transacao: item for item in payments.get_breakdown(start, end)}
    report_members = members.get_all_excluding_pending()

    assert summary.total_receita == 740.0
    assert summary.total_transacoes == 6
    assert breakdown["Diária"].total_valor == 70.0
    assert breakdown[TIPO_RENOVACAO_PLANO].total_valor == 380.0
    assert breakdown[TIPO_PAGAMENTO_TREINO].total_valor == 90.0
    assert breakdown[TIPO_COMPRA_VOUCHER].total_valor == 200.0
    assert "Fantasia Mes Pendente" not in {member.nome for member in report_members}
