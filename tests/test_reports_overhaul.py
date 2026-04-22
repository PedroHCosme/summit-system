from datetime import date, datetime, time, timedelta
from pathlib import Path

from src.data.models import Frequencia, Membro, Pagamento, Plano
from src.reports.analytics import (
    SEGMENTO_ESTAVEL,
    SEGMENTO_MUITO_ATIVO,
    SEGMENTO_REATIVACAO_URGENTE,
    SEGMENTO_RISCO_ALTO,
    SEGMENTO_RISCO_MODERADO,
    ReportAnalyticsService,
    previous_period_bounds,
)
from src.reports.finance_report import generate_finance_report
from src.reports.members_report import generate_members_report
from src.services.member_service import MemberService
from src.services.payment_service import PaymentService


def _seed_plans(session):
    session.add_all(
        [
            Plano(nome="Diaria", valor_por_checkin=35.0, preco=0.0, ativo=True),
            Plano(nome="Pacote 10", is_quota=True, quota_amount=10, preco=300.0, ativo=True),
        ]
    )
    session.commit()


def _add_member(session, nome, plano="Mensal", estado="ATIVO", venc_offset=30, credits=0):
    vencimento = date.today() + timedelta(days=venc_offset) if venc_offset is not None else None
    member = Membro(
        nome=nome,
        plano=plano,
        estado_plano=estado,
        data_cadastro=date.today() - timedelta(days=90),
        vencimento_plano=vencimento,
        voucher_credits=credits,
    )
    session.add(member)
    session.commit()
    return member


def _add_checkin(session, member_id, days_ago):
    when = datetime.combine(date.today() - timedelta(days=days_ago), time(hour=10))
    session.add(Frequencia(member_id=member_id, checkin_datetime=when))
    session.commit()


def _add_payment(session, member_id, amount, days_ago=2, tipo="Renovacao Plano", metodo="PIX"):
    when = datetime.combine(date.today() - timedelta(days=days_ago), time(hour=11))
    session.add(
        Pagamento(
            member_id=member_id,
            data_pagamento=when,
            tipo_transacao=tipo,
            valor=amount,
            metodo_pagamento=metodo,
        )
    )
    session.commit()


def test_previous_period_bounds_same_length():
    start = datetime(2026, 4, 1, 8, 0, 0)
    end = datetime(2026, 4, 15, 22, 0, 0)

    prev_start, prev_end = previous_period_bounds(start, end)
    current_days = (end.date() - start.date()).days + 1
    previous_days = (prev_end.date() - prev_start.date()).days + 1

    assert previous_days == current_days
    assert prev_end.date() == start.date() - timedelta(days=1)


def test_analytics_segments_exclude_pending_and_format_scripts(db_session):
    _seed_plans(db_session)
    period_start = date.today() - timedelta(days=29)
    period_end = date.today()

    urgente = _add_member(db_session, "Urgente", venc_offset=-40)
    risco_alto = _add_member(db_session, "Risco Alto", venc_offset=-10)
    risco_moderado = _add_member(db_session, "Risco Moderado", venc_offset=20)
    muito_ativo = _add_member(db_session, "Muito Ativo", venc_offset=20)
    estavel = _add_member(db_session, "Estavel", venc_offset=20)
    pendente = _add_member(db_session, "Pendente", estado="PENDENTE", venc_offset=20)

    _add_checkin(db_session, urgente.id, days_ago=80)
    _add_checkin(db_session, risco_alto.id, days_ago=34)
    _add_checkin(db_session, risco_moderado.id, days_ago=20)
    _add_checkin(db_session, estavel.id, days_ago=4)
    for days_ago in [1, 3, 5, 7, 9, 11, 13, 15]:
        _add_checkin(db_session, muito_ativo.id, days_ago=days_ago)
    _add_checkin(db_session, pendente.id, days_ago=1)

    _add_payment(db_session, urgente.id, 190.0)
    _add_payment(db_session, risco_alto.id, 190.0)
    _add_payment(db_session, risco_moderado.id, 190.0)
    _add_payment(db_session, muito_ativo.id, 190.0)
    _add_payment(db_session, estavel.id, 190.0)

    analytics = ReportAnalyticsService(db_session)
    payload = analytics.compute_member_features(period_start, period_end)

    rows = payload["list_data"]
    names = {row["nome"] for row in rows}
    assert "Pendente" not in names

    by_name = {row["nome"]: row for row in rows}
    assert by_name["Urgente"]["segmento"] == SEGMENTO_REATIVACAO_URGENTE
    assert by_name["Risco Alto"]["segmento"] == SEGMENTO_RISCO_ALTO
    assert by_name["Risco Moderado"]["segmento"] == SEGMENTO_RISCO_MODERADO
    assert by_name["Muito Ativo"]["segmento"] == SEGMENTO_MUITO_ATIVO
    assert by_name["Estavel"]["segmento"] == SEGMENTO_ESTAVEL

    for queue_key, queue_rows in payload["action_queues"].items():
        script = payload["outreach_scripts"][queue_key]
        for row in queue_rows:
            rendered = script.format(
                nome=row["nome"],
                plano=row["plano"],
                dias_desde_ultimo_checkin=row["dias_desde_ultimo_checkin"],
            )
            assert "{nome" not in rendered


def test_members_and_finance_reports_render_new_contract(db_session):
    _seed_plans(db_session)
    period_start = datetime.combine(date.today() - timedelta(days=30), time.min)
    period_end = datetime.combine(date.today(), time.max)

    m1 = _add_member(db_session, "Cliente Risco", venc_offset=-25)
    m2 = _add_member(db_session, "Cliente Ativo", venc_offset=20)
    _add_checkin(db_session, m1.id, days_ago=42)
    for days_ago in [1, 3, 6, 8, 10]:
        _add_checkin(db_session, m2.id, days_ago=days_ago)

    _add_payment(db_session, m1.id, 190.0, tipo="Renovacao Plano", metodo="PIX")
    _add_payment(db_session, m2.id, 190.0, tipo="Renovacao Plano", metodo="Cartao")
    _add_payment(db_session, m2.id, 90.0, tipo="Treino", metodo="PIX")

    members_report_path = generate_members_report(
        db_session=db_session,
        start_date=period_start,
        end_date=period_end,
        period_label="Teste",
    )
    members_html = Path(members_report_path).read_text(encoding="utf-8")
    assert "Resumo Executivo" in members_html
    assert "Playbook de Retencao" in members_html
    assert "Clientes que pode estar perdendo" in members_html
    assert "Clientes muito ativos" in members_html

    finance_report_path = generate_finance_report(
        period="Teste",
        start_date=period_start,
        end_date=period_end,
        payment_service=PaymentService(db_session=db_session),
        member_service=MemberService(db_session=db_session),
    )
    finance_html = Path(finance_report_path).read_text(encoding="utf-8")
    assert "Resumo Executivo" in finance_html
    assert "Receita em risco" in finance_html
    assert "Top fontes de receita" in finance_html
    assert "Menores fontes de receita" in finance_html

