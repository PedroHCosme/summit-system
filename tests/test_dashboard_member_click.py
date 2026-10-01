"""Clique num membro do dashboard: perfil abre com Frequencia e Financeiro carregados."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from unittest.mock import MagicMock

from src.ui.coordinators.members_coordinator import MembersCoordinator


def test_clique_no_dashboard_carrega_historicos(monkeypatch):
    monkeypatch.setattr("src.data.data_provider.get_member_by_id", lambda mid: {"id": mid, "nome": "Ana"})
    window = MagicMock()
    window.is_connected = True
    coordenador = MembersCoordinator(window)
    coordenador.load_member_history = MagicMock()
    coordenador.load_member_financial_history = MagicMock()

    coordenador.on_dashboard_member_clicked(7)

    window.member_search_screen.display_member_data.assert_called_once()
    coordenador.load_member_history.assert_called_once_with(7, "Ana")
    coordenador.load_member_financial_history.assert_called_once_with(7, "Ana")
