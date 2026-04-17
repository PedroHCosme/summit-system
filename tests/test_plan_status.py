"""Tests for the plan_status constants module — the single source of truth for estado_plano."""

import pytest
from src.core.plan_status import (
    ATIVO, INATIVO, VALID_STATES,
    is_active, display_label,
    DISPLAY_LABEL_ATIVO, DISPLAY_LABEL_PLANO_VENCIDO,
)


class TestPlanStatusConstants:
    """Tests for the canonical status constants."""

    def test_ativo_value(self):
        assert ATIVO == "ATIVO"

    def test_inativo_value(self):
        assert INATIVO == "INATIVO"

    def test_valid_states_contains_required_states(self):
        assert {"ATIVO", "INATIVO", "PENDENTE"}.issubset(VALID_STATES)

    def test_valid_states_is_immutable(self):
        with pytest.raises(AttributeError):
            VALID_STATES.add("VENCIDO")  # type: ignore


class TestIsActive:
    """Tests for the is_active() helper."""

    def test_ativo_returns_true(self):
        assert is_active("ATIVO") is True

    def test_inativo_returns_false(self):
        assert is_active("INATIVO") is False

    def test_case_insensitive_ativo(self):
        assert is_active("ativo") is True
        assert is_active("Ativo") is True
        assert is_active("aTiVo") is True

    def test_case_insensitive_inativo(self):
        assert is_active("inativo") is False
        assert is_active("Inativo") is False

    def test_whitespace_handling(self):
        assert is_active("  ATIVO  ") is True
        assert is_active("  INATIVO  ") is False

    def test_empty_string_returns_false(self):
        assert is_active("") is False

    def test_none_returns_false(self):
        assert is_active(None) is False

    def test_vencido_returns_false(self):
        """'VENCIDO' is not a valid DB state and should return False."""
        assert is_active("VENCIDO") is False

    def test_arbitrary_string_returns_false(self):
        assert is_active("INVALIDADO") is False
        assert is_active("PAUSADO") is False
        assert is_active("foo") is False


class TestDisplayLabel:
    """Tests for the display_label() helper."""

    def test_ativo_display(self):
        assert display_label("ATIVO") == DISPLAY_LABEL_ATIVO

    def test_inativo_display(self):
        assert display_label("INATIVO") == DISPLAY_LABEL_PLANO_VENCIDO

    def test_empty_display(self):
        assert display_label("") == DISPLAY_LABEL_PLANO_VENCIDO

    def test_none_display(self):
        assert display_label(None) == DISPLAY_LABEL_PLANO_VENCIDO


class TestDatabaseIntegrity:
    """Integration test: no member should have estado_plano outside VALID_STATES."""

    def test_all_members_have_valid_status(self, db_session):
        """Every member in the DB must have estado_plano in VALID_STATES or NULL."""
        from src.data.models import Membro

        members = db_session.query(Membro).all()
        for member in members:
            if member.estado_plano is not None:
                assert member.estado_plano in VALID_STATES, (
                    f"Member '{member.nome}' has invalid estado_plano: "
                    f"'{member.estado_plano}'. Valid states: {VALID_STATES}"
                )
