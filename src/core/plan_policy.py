"""
PlanPolicy — pure decision gateway for a single plan.

No database access. Instantiate with a Plano ORM object or via
PlanService.get_plan_policy(plan_name).
"""

from typing import Optional, TYPE_CHECKING

from src.core.plan_status import (
    LIMIAR_INATIVO_PADRAO,
    LIMIAR_INATIVO_AVULSO,
    LIMIAR_INATIVO_QUOTA,
    calcular_status_plano,
    calcular_status_membro,
)

if TYPE_CHECKING:
    from src.data.models import Plano


class PlanPolicy:
    """Decision gateway for a single plan — pure logic, no DB access."""

    def __init__(self, plan: "Plano") -> None:
        self._plan = plan

    # -------------------------------------------------------------------------
    # Plan structure
    # -------------------------------------------------------------------------

    @property
    def requires_due_date(self) -> bool:
        """True for time-based plans (Mensal, Trimestral, etc.)."""
        return bool(self._plan.requer_vencimento) and not self._plan.is_quota

    @property
    def is_quota(self) -> bool:
        """True for credit/voucher-based plans (Pacote 10, etc.)."""
        return bool(self._plan.is_quota)

    @property
    def is_per_checkin(self) -> bool:
        """True for plans that generate a payment on every check-in (Diária, Gympass, Totalpass)."""
        return bool(self._plan.valor_por_checkin and self._plan.valor_por_checkin > 0)

    # -------------------------------------------------------------------------
    # Pricing
    # -------------------------------------------------------------------------

    @property
    def checkin_price(self) -> float:
        return self._plan.valor_por_checkin or 0.0

    @property
    def renewal_price(self) -> float:
        return self._plan.preco or 0.0

    # -------------------------------------------------------------------------
    # Activity / status rules
    # -------------------------------------------------------------------------

    @property
    def inactivity_threshold_days(self) -> int:
        """Days without a check-in before a member is considered inactive."""
        if self._plan.is_quota:
            return LIMIAR_INATIVO_QUOTA
        # Per-checkin plans and zero-cost avulso plans (Cortesia) use the lenient threshold.
        if self.is_per_checkin or (
            not self._plan.requer_vencimento
            and not self._plan.is_quota
            and (self._plan.preco or 0.0) == 0.0
        ):
            return LIMIAR_INATIVO_AVULSO
        return LIMIAR_INATIVO_PADRAO

    def plan_status(self, vencimento, estado_db: Optional[str] = None) -> str:
        """Computed plan status (EM DIA / VENCIDO / SEM VENCIMENTO / PENDENTE)."""
        return calcular_status_plano(
            vencimento_plano=vencimento,
            estado_plano_db=estado_db,
            is_quota=self._plan.is_quota,
            valor_por_checkin=self._plan.valor_por_checkin or 0.0,
        )

    def member_activity_status(
        self, ultimo_checkin, voucher_credits: int = 0
    ) -> str:
        """Computed activity status (ATIVO / INATIVO) based on last check-in."""
        return calcular_status_membro(
            plano_nome=self._plan.nome,
            ultimo_checkin=ultimo_checkin,
            voucher_credits=voucher_credits,
            is_quota=self._plan.is_quota,
            valor_por_checkin=self._plan.valor_por_checkin or 0.0,
        )

    # -------------------------------------------------------------------------
    # Payment classification
    # -------------------------------------------------------------------------

    @property
    def renewal_transaction_type(self) -> str:
        """Transaction type string to use when recording a plan purchase/renewal."""
        from src.core.payment_constants import TIPO_COMPRA_VOUCHER, TIPO_RENOVACAO_PLANO
        return TIPO_COMPRA_VOUCHER if self._plan.is_quota else TIPO_RENOVACAO_PLANO
