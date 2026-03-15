
import pytest
from datetime import datetime, timedelta, date
from src.services.member_service import MemberService
from src.services.plan_service import PlanService
from src.data.models import Plano
from src.config import PLANOS_COM_VENCIMENTO
from src.core.plan_status import ATIVO, INATIVO


class TestSubscriptionPlans:
    
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)

    def test_plan_expiration_logic(self, member_service, db_session):
        # Create a member with a past expiration date
        past_date = (date.today() - timedelta(days=1)).strftime('%d/%m/%Y')
        
        # Ensure 'Mensal' is treated as a plan with expiration
        # We might need to mock config if strict validation checks config file
        if "Mensal" not in PLANOS_COM_VENCIMENTO:
             PLANOS_COM_VENCIMENTO.append("Mensal")
        
        member_result = member_service.create({
            "nome": "Expired User",
            "plano": "Mensal",
            "vencimento_plano": past_date,
            "estado_plano": ATIVO
        })
        
        # Trigger update expiration
        count = member_service.update_expired_plans()
        
        assert count == 1
        
        # Verify status changed to INATIVO
        member = member_service.get_by_id(member_result.member_id)
        assert member.estado_plano == INATIVO

    def test_active_plan_not_expired(self, member_service):
        future_date = (date.today() + timedelta(days=30)).strftime('%d/%m/%Y')
        
        member_result = member_service.create({
            "nome": "Active User",
            "plano": "Mensal",
            "vencimento_plano": future_date,
            "estado_plano": ATIVO
        })
        
        count = member_service.update_expired_plans()
        
        assert count == 0
        member = member_service.get_by_id(member_result.member_id)
        assert member.estado_plano == ATIVO


class TestPlanCRUD:
    """Tests for plan creation and modification."""
    
    @pytest.fixture
    def plan_service(self, db_session):
        return PlanService(db_session=db_session)
    
    def test_create_plan(self, db_session):
        """Create a new basic plan."""
        plan = Plano(
            nome="Teste Anual",
            preco=1000.0,
            requer_vencimento=True,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        
        saved = db_session.query(Plano).filter(Plano.nome == "Teste Anual").first()
        assert saved is not None
        assert saved.preco == 1000.0
        assert saved.requer_vencimento is True
    
    def test_update_plan_price(self, db_session):
        """Update plan price."""
        # Get existing plan
        plan = db_session.query(Plano).filter(Plano.nome == "Mensal").first()
        original_price = plan.preco
        
        # Update price
        plan.preco = 250.0
        db_session.commit()
        
        # Verify
        updated = db_session.query(Plano).filter(Plano.nome == "Mensal").first()
        assert updated.preco == 250.0
        assert updated.preco != original_price
    
    def test_create_quota_plan(self, db_session):
        """Create a quota-based plan with is_quota and quota_amount."""
        plan = Plano(
            nome="Pacote 5",
            preco=100.0,
            is_quota=True,
            quota_amount=5,
            requer_vencimento=False,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        
        saved = db_session.query(Plano).filter(Plano.nome == "Pacote 5").first()
        assert saved.is_quota is True
        assert saved.quota_amount == 5
        assert saved.requer_vencimento is False
    
    def test_deactivate_plan(self, db_session):
        """Deactivate a plan by setting ativo=False."""
        plan = Plano(
            nome="Plano Obsoleto",
            preco=50.0,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        
        # Deactivate
        plan.ativo = False
        db_session.commit()
        
        # Verify
        inactive = db_session.query(Plano).filter(Plano.nome == "Plano Obsoleto").first()
        assert inactive.ativo is False
    
    def test_create_per_checkin_plan(self, db_session):
        """Create a plan that charges per check-in."""
        plan = Plano(
            nome="Diária Teste",
            preco=0.0,
            valor_por_checkin=30.0,
            requer_vencimento=False,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        
        saved = db_session.query(Plano).filter(Plano.nome == "Diária Teste").first()
        assert saved.valor_por_checkin == 30.0
        assert saved.preco == 0.0


class TestPlanService:
    """Tests for PlanService centralized access."""
    
    @pytest.fixture
    def plan_service(self, db_session):
        return PlanService(db_session=db_session)
    
    @pytest.fixture
    def setup_plans(self, db_session):
        """Create various plan types for testing."""
        plans = [
            Plano(nome="Trimestral", preco=300.0, requer_vencimento=True, ativo=True),
            Plano(nome="Pacote 10", preco=200.0, is_quota=True, quota_amount=10, ativo=True),
            Plano(nome="Gympass", preco=0.0, valor_por_checkin=15.0, ativo=True),
            Plano(nome="Inactive", preco=50.0, ativo=False),
        ]
        for p in plans:
            db_session.add(p)
        db_session.commit()
        return plans
    
    def test_get_plan_names(self, plan_service, setup_plans):
        """get_plan_names() returns only active plans."""
        names = plan_service.get_plan_names()
        
        assert "Mensal" in names  # From conftest
        assert "Trimestral" in names
        assert "Pacote 10" in names
        assert "Inactive" not in names  # Should be excluded
    
    def test_get_quota_plans(self, plan_service, setup_plans):
        """get_quota_plans() returns only quota-based plans."""
        quota = plan_service.get_quota_plans()
        
        assert "Pacote 10" in quota
        assert "Mensal" not in quota
        assert "Trimestral" not in quota
    
    def test_is_quota_plan(self, plan_service, setup_plans):
        """is_quota_plan() checks if a plan is quota-based."""
        assert plan_service.is_quota_plan("Pacote 10") is True
        assert plan_service.is_quota_plan("Mensal") is False
        assert plan_service.is_quota_plan("NonExistent") is False
    
    def test_requires_vencimento(self, plan_service, setup_plans):
        """requires_vencimento() checks if plan needs expiration date."""
        assert plan_service.requires_vencimento("Trimestral") is True
        assert plan_service.requires_vencimento("Pacote 10") is False  # Quota plans don't
        assert plan_service.requires_vencimento("Gympass") is False
    
    def test_get_checkin_payment_plans(self, plan_service, setup_plans):
        """get_checkin_payment_plans() returns plans with per-checkin payments."""
        checkin_plans = plan_service.get_checkin_payment_plans()
        
        assert "Gympass" in checkin_plans
        assert checkin_plans["Gympass"] == 15.0
        assert "Mensal" not in checkin_plans
    
    def test_get_plans_as_dict(self, plan_service, setup_plans):
        """get_plans_as_dict() returns all plan info as dict."""
        plans = plan_service.get_plans_as_dict()
        
        assert "Mensal" in plans
        assert "Pacote 10" in plans
        assert plans["Pacote 10"]["is_quota"] is True
        assert plans["Pacote 10"]["quota_amount"] == 10
    
    def test_get_plan_price(self, plan_service, setup_plans):
        """get_plan_price() returns the preco of a plan."""
        assert plan_service.get_plan_price("Trimestral") == 300.0
        assert plan_service.get_plan_price("Pacote 10") == 200.0
        assert plan_service.get_plan_price("NonExistent") == 0.0
