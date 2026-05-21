
import pytest
from datetime import date, timedelta
from src.services.member_service import MemberService
from src.data.models import Plano, Membro, Pagamento

class TestMemberManagement:
    
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)

    def test_add_member_required_fields(self, member_service):
        # Test missing name
        result = member_service.create({"plano": "Mensal"})
        assert result.success is False
        assert "nome" in result.message.lower()

    def test_add_member_success(self, member_service):
        result = member_service.create({
            "nome": "New User",
            "plano": "Mensal",
            "email": "new@example.com",
            "whatsapp": "123456789"
        })
        assert result.success is True
        assert result.member_id is not None
        
        member = member_service.get_by_id(result.member_id)
        assert member.nome == "New User"
        assert member.email == "new@example.com"

    def test_add_member_blocks_duplicate_name(self, member_service):
        member_service.create({
            "nome": "João da Silva",
            "plano": "Mensal",
            "email": "joao@example.com",
            "whatsapp": "(11) 99999-0000",
        })

        result = member_service.create({
            "nome": "joao   da silva",
            "plano": "Mensal",
            "email": "outro@example.com",
            "whatsapp": "(11) 98888-0000",
        })

        assert result.success is False
        assert "nome" in result.message.lower()

    def test_add_member_blocks_duplicate_email(self, member_service):
        member_service.create({
            "nome": "Maria Um",
            "plano": "Mensal",
            "email": "Maria@Example.com",
            "whatsapp": "(11) 99999-1111",
        })

        result = member_service.create({
            "nome": "Maria Dois",
            "plano": "Mensal",
            "email": "maria@example.com",
            "whatsapp": "(11) 99999-2222",
        })

        assert result.success is False
        assert "email" in result.message.lower()

    def test_add_member_blocks_duplicate_whatsapp_for_adult(self, member_service):
        member_service.create({
            "nome": "Responsavel Adulto",
            "plano": "Mensal",
            "email": "adulto1@example.com",
            "whatsapp": "(11) 99999-3333",
        })

        result = member_service.create({
            "nome": "Outro Adulto",
            "plano": "Mensal",
            "email": "adulto2@example.com",
            "whatsapp": "11999993333",
            "data_nascimento": date.today() - timedelta(days=365 * 20),
        })

        assert result.success is False
        assert "whatsapp" in result.message.lower()

    def test_add_member_allows_duplicate_whatsapp_for_minor(self, member_service):
        member_service.create({
            "nome": "Responsavel Menor",
            "plano": "Mensal",
            "email": "responsavel@example.com",
            "whatsapp": "(11) 99999-4444",
        })

        result = member_service.create({
            "nome": "Aluno Menor",
            "plano": "Mensal",
            "email": "menor@example.com",
            "whatsapp": "11999994444",
            "data_nascimento": date.today() - timedelta(days=365 * 12),
        })

        assert result.success is True

    def test_update_member_info(self, member_service):
        # Create
        create_result = member_service.create({"nome": "Update Me", "plano": "Mensal"})
        member_id = create_result.member_id
        
        # Update
        update_result = member_service.update(member_id, nome="Updated Name", profissao="Engineer")
        assert update_result.success is True
        
        # Verify
        member = member_service.get_by_id(member_id)
        assert member.nome == "Updated Name"
        assert member.profissao == "Engineer"

    def test_delete_member(self, member_service):
        create_result = member_service.create({"nome": "Delete Me", "plano": "Mensal"})
        member_id = create_result.member_id
        
        delete_result = member_service.delete(member_id)
        assert delete_result.success is True
        
        member = member_service.get_by_id(member_id)
        assert member is None

    def test_get_recent_members_returns_latest_registrations(self, member_service, db_session):
        older = Membro(nome="Older Member", plano="Mensal", data_cadastro=date(2024, 1, 1))
        middle = Membro(nome="Middle Member", plano="Mensal", data_cadastro=date(2024, 2, 1))
        newer = Membro(nome="Newer Member", plano="Mensal", data_cadastro=date(2024, 3, 1))
        db_session.add_all([older, middle, newer])
        db_session.commit()

        recent = member_service.get_recent_members(limit=2)

        assert [member["nome"] for member in recent] == ["Newer Member", "Middle Member"]

    def test_paginated_members_can_sort_by_latest_registration(self, member_service, db_session):
        first = Membro(nome="First Same Day", plano="Mensal", data_cadastro=date(2024, 4, 1))
        second = Membro(nome="Second Same Day", plano="Mensal", data_cadastro=date(2024, 4, 1))
        db_session.add_all([first, second])
        db_session.commit()

        result = member_service.get_paginated(
            sort_by="data_cadastro",
            sort_dir="desc",
            page_size=2,
        )

        assert [member["nome"] for member in result.members] == [
            "Second Same Day",
            "First Same Day",
        ]


class TestMemberRegistrationAdvanced:
    """Advanced member registration tests."""
    
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)
    
    @pytest.fixture
    def quota_plan(self, db_session):
        """Create a quota-based plan."""
        plan = Plano(
            nome="Pacote 10",
            preco=200.0,
            is_quota=True,
            quota_amount=10,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        return plan

    def test_add_member_with_quota_plan(self, member_service, db_session, quota_plan):
        """New member with quota plan gets voucher_credits set."""
        result = member_service.create({
            "nome": "Quota User",
            "plano": "Pacote 10",
            "voucher_credits": 10
        })
        assert result.success is True
        
        member = member_service.get_by_id(result.member_id)
        assert member.plano == "Pacote 10"
        assert member.voucher_credits == 10
        # Quota plans should not have vencimento
        assert member.vencimento_plano is None or member.vencimento_plano == ""
        
    def test_add_member_with_vencimento(self, member_service):
        """Member with time-based plan gets vencimento and estado_plano set."""
        future_date = date.today() + timedelta(days=30)
        
        result = member_service.create({
            "nome": "Time Plan User",
            "plano": "Mensal",
            "vencimento_plano": future_date
        })
        assert result.success is True
        
        member = member_service.get_by_id(result.member_id)
        assert member.vencimento_plano == future_date
        assert member.estado_plano == "ATIVO"

    def test_add_member_respects_custom_plan_without_vencimento(self, member_service, db_session):
        """Plano sem vencimento no banco sempre limpa vencimento informado."""
        db_session.add(Plano(
            nome="Plano Sem Vencimento Custom",
            preco=80.0,
            requer_vencimento=False,
            ativo=True
        ))
        db_session.commit()

        result = member_service.create({
            "nome": "No Expiration User",
            "plano": "Plano Sem Vencimento Custom",
            "vencimento_plano": date.today() + timedelta(days=30)
        })

        assert result.success is True
        member = member_service.get_by_id(result.member_id)
        assert member.vencimento_plano is None

    def test_add_member_respects_custom_plan_with_vencimento(self, member_service, db_session):
        """Plano com vencimento no banco preserva a data mesmo fora do config.py."""
        future_date = date.today() + timedelta(days=30)
        db_session.add(Plano(
            nome="Plano Com Vencimento Custom",
            preco=120.0,
            requer_vencimento=True,
            ativo=True
        ))
        db_session.commit()

        result = member_service.create({
            "nome": "Custom Expiration User",
            "plano": "Plano Com Vencimento Custom",
            "vencimento_plano": future_date
        })

        assert result.success is True
        member = member_service.get_by_id(result.member_id)
        assert member.vencimento_plano == future_date

    def test_add_member_with_training(self, member_service):
        """Member with training service gets treina and vencimento_treino set."""
        future_date = date.today() + timedelta(days=30)
        
        result = member_service.create({
            "nome": "Training User",
            "plano": "Mensal",
            "treina": "Sim",
            "vencimento_treino": future_date
        })
        assert result.success is True
        
        member = member_service.get_by_id(result.member_id)
        assert member.treina == "Sim"
        assert member.vencimento_treino == future_date


class TestEditMemberAdvanced:
    """Comprehensive edit member tests."""
    
    @pytest.fixture
    def member_service(self, db_session):
        return MemberService(db_session=db_session)
    
    @pytest.fixture
    def quota_plan(self, db_session):
        """Create a quota-based plan."""
        plan = Plano(
            nome="Pacote 10",
            preco=200.0,
            is_quota=True,
            quota_amount=10,
            ativo=True
        )
        db_session.add(plan)
        db_session.commit()
        return plan

    def test_update_plan_with_payment(self, member_service, db_session):
        """Changing plan registers payment when register_payment=True."""
        # Create member
        result = member_service.create({"nome": "Plan Changer", "plano": "Mensal"})
        member_id = result.member_id
        
        # Count payments before
        payments_before = db_session.query(Pagamento).filter(
            Pagamento.member_id == member_id
        ).count()
        
        # Update plan with payment registration
        future_date = (date.today() + timedelta(days=90)).strftime('%d/%m/%Y')
        update_result = member_service.update_from_dict({
            'id': member_id,
            'plano': 'Trimestral',
            'vencimento_plano': future_date
        }, register_payment=True, metodo_pagamento='PIX')
        
        assert update_result.success is True
        
        # Verify payment was created
        payments_after = db_session.query(Pagamento).filter(
            Pagamento.member_id == member_id
        ).count()
        assert payments_after > payments_before
        
        # Verify member updated
        member = member_service.get_by_id(member_id)
        assert member.plano == "Trimestral"

    def test_update_to_quota_plan(self, member_service, db_session, quota_plan):
        """Switching to quota plan sets voucher_credits."""
        # Create member with time-based plan
        result = member_service.create({"nome": "To Quota", "plano": "Mensal"})
        member_id = result.member_id
        
        # Switch to quota plan
        update_result = member_service.update_from_dict({
            'id': member_id,
            'plano': 'Pacote 10',
            'voucher_credits': 10
        }, register_payment=True, metodo_pagamento='PIX')
        
        assert update_result.success is True
        
        member = member_service.get_by_id(member_id)
        assert member.plano == "Pacote 10"
        assert member.voucher_credits == 10

    def test_rebuy_same_quota_plan_accumulates_credits_and_registers_payment(
        self, member_service, db_session, quota_plan
    ):
        """Comprar o mesmo pacote novamente acumula créditos e registra pagamento."""
        result = member_service.create({
            "nome": "Quota Rebuyer",
            "plano": "Pacote 10",
            "voucher_credits": 2
        })

        update_result = member_service.update_from_dict({
            'id': result.member_id,
            'plano': 'Pacote 10',
            'voucher_credits': 10
        }, register_payment=True, metodo_pagamento='PIX')

        assert update_result.success is True
        member = member_service.get_by_id(result.member_id)
        assert member.voucher_credits == 12

        payment = db_session.query(Pagamento).filter(
            Pagamento.member_id == result.member_id
        ).one()
        assert payment.tipo_transacao == "Compra Voucher"
        assert payment.valor == 200.0

    def test_update_training_activation(self, member_service, db_session):
        """Activating training sets treina='Sim' and vencimento_treino."""
        # Create member without training
        result = member_service.create({
            "nome": "Train Me",
            "plano": "Mensal",
            "treina": "Não"
        })
        member_id = result.member_id
        
        # Activate training
        future_date = date.today() + timedelta(days=30)
        update_result = member_service.update_from_dict({
            'id': member_id,
            'treina': 'Sim',
            'vencimento_treino': future_date
        })
        
        assert update_result.success is True
        
        member = member_service.get_by_id(member_id)
        assert member.treina == "Sim"
        assert member.vencimento_treino == future_date

    def test_update_all_fields(self, member_service, db_session):
        """Update multiple fields at once."""
        # Create member
        result = member_service.create({"nome": "Full Update", "plano": "Mensal"})
        member_id = result.member_id
        
        # Update all fields
        update_result = member_service.update_from_dict({
            'id': member_id,
            'nome': 'Full Update Changed',
            'apelido': 'Fulano',
            'email': 'full@example.com',
            'whatsapp': '999888777',
            'genero': 'Masculino',
            'calcado': '42',
            'profissao': 'Developer',
            'contato_emergencia': 'Mom: 111222333',
            'observacoes': 'VIP member'
        })
        
        assert update_result.success is True
        
        member = member_service.get_by_id(member_id)
        assert member.nome == "Full Update Changed"
        assert member.apelido == "Fulano"
        assert member.email == "full@example.com"
        assert member.whatsapp == "999888777"
        assert member.genero == "Masculino"
        assert member.calcado == "42"
        assert member.profissao == "Developer"
        assert member.contato_emergencia == "Mom: 111222333"
        assert member.observacoes == "VIP member"

    def test_update_vencimento_extends_plan(self, member_service, db_session):
        """Updating vencimento extends the plan."""
        # Create member with short expiration
        short_date = date.today() + timedelta(days=5)
        result = member_service.create({
            "nome": "Extend Me",
            "plano": "Mensal",
            "vencimento_plano": short_date
        })
        member_id = result.member_id
        
        # Extend vencimento
        long_date = date.today() + timedelta(days=60)
        update_result = member_service.update_from_dict({
            'id': member_id,
            'vencimento_plano': long_date
        })
        
        assert update_result.success is True
        
        member = member_service.get_by_id(member_id)
        assert member.vencimento_plano == long_date
