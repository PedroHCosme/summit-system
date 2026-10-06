from datetime import date, timedelta

import pytest

from src.core.plan_status import ATIVO, PENDENTE
from src.data.models import Membro, Plano


@pytest.fixture
def web_client(db_session, monkeypatch):
    from src.web import app as web_app

    web_app.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    monkeypatch.setattr(web_app, "SessionLocal", lambda: db_session)
    return web_app.app.test_client()


def _seed_web_plans(db_session):
    mensal = db_session.query(Plano).filter(Plano.nome == "Mensal").first()
    mensal.preco = 190.0
    mensal.requer_vencimento = True
    mensal.ativo = True
    diaria = Plano(
        nome="Diária",
        preco=0.0,
        valor_por_checkin=35.0,
        requer_vencimento=False,
        ativo=True,
    )
    db_session.add(diaria)
    db_session.commit()


def _add_member(db_session, **kwargs):
    member = Membro(
        nome=kwargs.get("nome", "Membro Web"),
        apelido=kwargs.get("apelido"),
        whatsapp=kwargs.get("whatsapp", "11999990000"),
        plano=kwargs.get("plano", "Mensal"),
        vencimento_plano=kwargs.get("vencimento_plano"),
        estado_plano=kwargs.get("estado_plano", ATIVO),
        data_cadastro=date.today(),
    )
    db_session.add(member)
    db_session.commit()
    return member


def test_web_checkin_single_result_uses_confirmation_card(web_client, db_session):
    _seed_web_plans(db_session)
    _add_member(
        db_session,
        nome="Ana Boulder",
        apelido="Aninha",
        whatsapp="11987654321",
        vencimento_plano=date.today() + timedelta(days=10),
    )

    response = web_client.post("/checkin", data={"identifier": "Ana Boulder"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Encontramos você?" in html
    assert "Sou eu, fazer check-in" in html
    assert "Aninha" in html
    assert "Final 4321" in html
    assert "Plano em dia" in html
    assert "Encontramos mais de um membro" not in html


def test_web_checkin_multiple_results_asks_member_to_choose(web_client, db_session):
    _seed_web_plans(db_session)
    _add_member(db_session, nome="João Rocha", whatsapp="11999991111")
    _add_member(db_session, nome="João Silva", whatsapp="11999992222", plano="Diária")

    response = web_client.post("/checkin", data={"identifier": "João"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Encontramos mais de um membro." in html
    assert "Escolha seu nome para continuar." in html
    assert "João Rocha" in html
    assert "Final 1111" in html
    assert "João Silva" in html
    assert "Final 2222" in html


def test_web_checkin_not_found_shows_register_link(web_client, db_session):
    _seed_web_plans(db_session)

    response = web_client.post("/checkin", data={"identifier": "Nome Inexistente"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Membro não encontrado" in html
    assert "Fazer cadastro" in html


def test_web_checkin_pending_member_is_not_allowed(web_client, db_session):
    _seed_web_plans(db_session)
    member = _add_member(
        db_session,
        nome="Pendente Web",
        estado_plano=PENDENTE,
        vencimento_plano=date.today() + timedelta(days=10),
    )

    search_response = web_client.post("/checkin", data={"identifier": "Pendente Web"})
    search_html = search_response.get_data(as_text=True)
    assert "Cadastro pendente" in search_html
    assert "aguardando aprovação" in search_html
    assert "Sou eu, fazer check-in" not in search_html

    confirm_response = web_client.post(
        "/checkin",
        data={"member_id": str(member.id)},
        follow_redirects=True,
    )
    confirm_html = confirm_response.get_data(as_text=True)
    assert "Seu cadastro ainda está aguardando aprovação da academia." in confirm_html


def test_web_checkin_expired_member_shows_warning_but_allows_confirmation(web_client, db_session):
    _seed_web_plans(db_session)
    _add_member(
        db_session,
        nome="Vencido Web",
        vencimento_plano=date.today() - timedelta(days=1),
    )

    response = web_client.post("/checkin", data={"identifier": "Vencido Web"})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Plano vencido" in html
    assert "Seu plano parece vencido" in html
    assert "Sou eu, fazer check-in" in html
