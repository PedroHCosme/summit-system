
import pytest
from datetime import datetime, timedelta
from src.services.checkin_service import CheckinService
from src.services.member_service import MemberService
from src.data.models import Plano, Membro, Pagamento, Frequencia

class TestCheckinFunctionality:
    
    @pytest.fixture
    def checkin_service(self, db_session):
        return CheckinService(db_session=db_session)
        
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)

    def test_valid_checkin(self, checkin_service, member_service, db_session):
        # Create member
        member_result = member_service.create({
            "nome": "Test User",
            "plano": "Mensal"
        })
        assert member_result.success
        member_id = member_result.member_id
        
        # Perform Check-in
        result = checkin_service.perform_checkin(member_id)
        
        assert result.success is True
        assert result.checkin_id is not None
        assert "sucesso" in result.message.lower()

    def test_duplicate_checkin_same_day(self, checkin_service, member_service):
        member_result = member_service.create({
            "nome": "Duplicate User",
            "plano": "Mensal"
        })
        member_id = member_result.member_id
        
        # First check-in
        checkin_service.perform_checkin(member_id)
        
        # Second check-in same day
        result = checkin_service.perform_checkin(member_id)
        
        assert result.success is False
        assert "duplicado" in result.message.lower()

    def test_checkin_nonexistent_member(self, checkin_service):
        result = checkin_service.perform_checkin(99999)
        assert result.success is False
        assert "não encontrado" in result.message.lower()

    def test_checkin_with_payment_generation(self, checkin_service, member_service, db_session):
        # Create Diária plan that requires payment
        diaria_plan = Plano(nome="Diária", preco=0.0, valor_por_checkin=20.0, ativo=True)
        db_session.add(diaria_plan)
        db_session.commit()
        
        # Create member with Diária plan
        member_result = member_service.create({
            "nome": "Daily User",
            "plano": "Diária"
        })
        member_id = member_result.member_id
        
        # Perform check-in
        result = checkin_service.perform_checkin(member_id)
        
        assert result.success is True
        assert result.payment_generated is True
        assert result.payment_amount == 20.0


class TestVoucherPlanFunctionality:
    """Tests for quota-based voucher plans."""
    
    @pytest.fixture
    def checkin_service(self, db_session):
        return CheckinService(db_session=db_session)
        
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)
    
    @pytest.fixture
    def quota_plan(self, db_session):
        """Create a quota-based plan."""
        plan = Plano(
            nome="Pacote 10",
            preco=200.0,
            valor_por_checkin=0.0,
            requer_vencimento=False,
            ativo=True,
            is_quota=True,
            quota_amount=10
        )
        db_session.add(plan)
        db_session.commit()
        return plan

    def test_voucher_checkin_deducts_balance(self, checkin_service, member_service, db_session, quota_plan):
        """Check-in with voucher plan decrements balance from 10 to 9."""
        # Create member with quota plan and credits
        member_result = member_service.create({
            "nome": "Voucher User",
            "plano": "Pacote 10",
            "voucher_credits": 10
        })
        assert member_result.success
        member_id = member_result.member_id
        
        # Perform check-in
        result = checkin_service.perform_checkin(member_id)
        
        assert result.success is True
        assert "Restam 9 vouchers" in result.message
        
        # Verify balance was decremented
        member = db_session.query(Membro).filter(Membro.id == member_id).first()
        assert member.voucher_credits == 9
    
    def test_voucher_zero_balance_blocks_checkin(self, checkin_service, member_service, db_session, quota_plan):
        """Check-in with 0 vouchers is blocked (no Frequencia recorded) and warns."""
        # Create member with quota plan but zero credits
        member_result = member_service.create({
            "nome": "Zero Balance User",
            "plano": "Pacote 10",
            "voucher_credits": 0
        })
        assert member_result.success
        member_id = member_result.member_id

        # Perform check-in - should be blocked
        result = checkin_service.perform_checkin(member_id)

        assert result.success is False
        assert "voucher" in result.message.lower()

        # No check-in should have been recorded
        checkins = db_session.query(Frequencia).filter(Frequencia.member_id == member_id).count()
        assert checkins == 0
        # Balance stays at 0 (nothing decremented below zero)
        member = db_session.query(Membro).filter(Membro.id == member_id).first()
        assert member.voucher_credits == 0
    
    def test_voucher_no_payment_generated(self, checkin_service, member_service, db_session, quota_plan):
        """Quota plan check-in does not create payment record."""
        # Create member with quota plan
        member_result = member_service.create({
            "nome": "No Pay User",
            "plano": "Pacote 10",
            "voucher_credits": 5
        })
        member_id = member_result.member_id
        
        # Count payments before
        payments_before = db_session.query(Pagamento).filter(
            Pagamento.member_id == member_id
        ).count()
        
        # Perform check-in
        result = checkin_service.perform_checkin(member_id)
        
        assert result.success is True
        assert result.payment_generated is False
        
        # Verify no new payment was created
        payments_after = db_session.query(Pagamento).filter(
            Pagamento.member_id == member_id
        ).count()
        assert payments_after == payments_before
    
    def test_quota_plan_accumulates_credits(self, member_service, db_session, quota_plan):
        """Renewing quota plan adds credits (e.g., 5 + 10 = 15)."""
        # Create member with existing credits (from a previous voucher purchase)
        member_result = member_service.create({
            "nome": "Accumulate User",
            "plano": "Mensal",  # Start with time-based plan
            "voucher_credits": 5  # But has some leftover credits from before
        })
        member_id = member_result.member_id
        
        # Purchase a quota plan (should add credits to existing balance)
        update_result = member_service.update_from_dict({
            'id': member_id,
            'plano': 'Pacote 10',
            'voucher_credits': 10  # Adding 10 credits
        }, register_payment=True, metodo_pagamento='PIX')
        
        assert update_result.success
        
        # Verify credits accumulated (5 existing + 10 new = 15)
        member = db_session.query(Membro).filter(Membro.id == member_id).first()
        assert member.voucher_credits == 15
    
    def test_switch_to_time_plan_resets_credits(self, member_service, db_session, quota_plan):
        """Switching from Voucher to Mensal sets voucher_credits = 0."""
        # Create member with quota plan and credits
        member_result = member_service.create({
            "nome": "Switch User",
            "plano": "Pacote 10",
            "voucher_credits": 8
        })
        member_id = member_result.member_id
        
        # Switch to time-based plan
        update_result = member_service.update_from_dict({
            'id': member_id,
            'plano': 'Mensal',
            'vencimento_plano': '31/12/2026'
        }, register_payment=True, metodo_pagamento='PIX')
        
        assert update_result.success
        
        # Verify credits were reset
        member = db_session.query(Membro).filter(Membro.id == member_id).first()
        assert member.voucher_credits == 0
