"""Smoke test: MainWindow constrói e mantém coordenadores + handlers.

Rede de segurança para a decomposição do God Object. Não testa comportamento
de negócio (isso vive nos testes de service) — só garante que a janela monta e
que os métodos-alvo dos sinais existem, que é o risco real do refactor.
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, monkeypatch):
    # ponytail: o smoke test não precisa conectar ao banco — só verifica
    # montagem + coordenadores. Neutralizamos _auto_connect para não iniciar
    # a QThread de migração (que vazaria e derrubaria a suíte inteira).
    monkeypatch.setattr(MainWindow, "_auto_connect", lambda self: None)
    w = MainWindow()
    yield w
    w.deleteLater()


def test_coordinators_instantiated(window):
    assert window.members_coordinator is not None
    assert window.checkin_coordinator is not None
    assert window.reports_coordinator is not None
    assert window.settings_coordinator is not None


@pytest.mark.parametrize("coordinator, method", [
    ("members_coordinator", "on_member_search_by_name"),
    ("members_coordinator", "on_edit_member_clicked"),
    ("members_coordinator", "on_delete_member_clicked"),
    ("members_coordinator", "on_list_delete_member_clicked"),
    ("checkin_coordinator", "on_confirm_checkin_clicked"),
    ("checkin_coordinator", "on_checkin_search_by_name"),
])
def test_coordinator_handlers_exist(window, coordinator, method):
    assert callable(getattr(getattr(window, coordinator), method))
