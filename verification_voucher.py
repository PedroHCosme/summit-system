
import sys
import os
from datetime import datetime, timedelta

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from src.data.database_manager import DatabaseManager
from src.data.migrations import DatabaseMigrator
from src.services.member_service import MemberService
from src.services.checkin_service import CheckinService

def run_verification():
    print("=== Iniciando Verificação do Plano Voucher ===")
    
    # 1. Setup Banco e Migrações
    db_manager = DatabaseManager()
    db_manager.connect() # Ensure connection
    migrator = DatabaseMigrator(db_manager)
    print("Executando migrações...")
    migrator.ensure_voucher_credits_column()
    migrator.seed_voucher_plan()
    
    # 2. Services
    member_service = MemberService(db_manager=db_manager) # Inicializa com legacy, mas internamente usa legacy ou não. 
    # O ideal é usar session do provider se possível, mas vamos testar via service facade.
    # O MemberService foi atualizado para usar session se passar, ou db_manager.
    # Vamos usar db_manager para simplificar o setup do script sem framework de injeção.
    # MAS espere, implementamos _create_sqlalchemy e _update_sqlalchemy.
    # O default do projeto parece misturar. Vamos tentar instanciar session.
    
    from src.data.data_provider import get_provider
    provider = get_provider()
    session = provider.session
    
    member_service = MemberService(db_session=session)
    checkin_service = CheckinService(db_session=session)
    
    # 3. Criar Membro
    print("\nCriando membro de teste...")
    member_data = {
        "nome": "Test Voucher User",
        "email": "voucher@test.com",
        "plano": "Mensal" # Começa com outro plano
    }
    result = member_service.create(member_data)
    if not result.success:
        print(f"Erro ao criar membro: {result.message}")
        return
    
    member_id = result.member_id
    print(f"Membro criado: ID {member_id}")
    
    # 4. Comprar Voucher (Update)
    print("\nComprando Voucher (2 créditos)...")
    update_data = {
        "id": member_id,
        "plano": "Voucher",
        "voucher_credits": 2,
        "price": 100.0
    }
    result = member_service.update_from_dict(update_data, register_payment=True, metodo_pagamento="PIX")
    if not result.success:
         print(f"Erro ao atualizar para Voucher: {result.message}")
         return
    print("Plano atualizado para Voucher.")
    
    # Verificar créditos no banco
    member = member_service.get_by_id(member_id)
    print(f"Créditos atuais: {member.voucher_credits}")
    assert member.voucher_credits == 2, "Deveria ter 2 créditos"
    
    # 5. Check-in 1 (Sucesso)
    print("\nRealizando Check-in 1...")
    checkin_res = checkin_service.perform_checkin(member_id)
    if checkin_res.success:
        print("Check-in 1: Sucesso")
    else:
        print(f"Check-in 1: Falha ({checkin_res.message})")
        
    session.expire_all() # Refresh
    member = member_service.get_by_id(member_id)
    print(f"Créditos restantes: {member.voucher_credits}")
    assert member.voucher_credits == 1, "Deveria ter 1 crédito"
    
    # 6. Check-in 2 (Sucesso - Dia seguinte simulado)
    print("\nRealizando Check-in 2 (Dia seguinte)...")
    # Hack para simular dia seguinte no mesmo teste: criar checkin com data explicita
    tomorrow = datetime.now() + timedelta(days=1)
    checkin_res = checkin_service.perform_checkin(member_id, checkin_datetime=tomorrow)
    
    if checkin_res.success:
        print("Check-in 2: Sucesso")
    else:
        print(f"Check-in 2: Falha ({checkin_res.message})")
        
    session.expire_all()
    member = member_service.get_by_id(member_id)
    print(f"Créditos restantes: {member.voucher_credits}")
    assert member.voucher_credits == 0, "Deveria ter 0 créditos"
    
    # 7. Check-in 3 (Falha - Sem créditos)
    print("\nRealizando Check-in 3 (Dia posterior - deve falhar)...")
    after_tomorrow = datetime.now() + timedelta(days=2)
    checkin_res = checkin_service.perform_checkin(member_id, checkin_datetime=after_tomorrow)
    
    if not checkin_res.success:
        print(f"Check-in 3: Falhou como esperado. Motivo: {checkin_res.message}")
    else:
        print("Check-in 3: Sucesso (INESPERADO!)")
        
    print("\n=== Verificação Concluída ===")

if __name__ == "__main__":
    run_verification()
