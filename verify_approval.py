
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager

def verify_approval_workflow():
    print("Verifying Member Approval Workflow...")
    
    db = DatabaseManager()
    db.connect()
    
    # 1. Simulate Web Registration (Status PENDENTE)
    print("\n1. Simulating Web Registration...")
    member_data = {
        'nome': 'Test Pending Member',
        'apelido': 'Tester',
        'whatsapp': '11999999999',
        'plano': 'Mensal',
        'data_nascimento': '1990-01-01',
        'email': 'test@example.com',
        'genero': 'Outro',
        'calcado': '40',
        'treina': 'Não',
        'estado_plano': 'PENDENTE' # This is what app.py does now
    }
    
    member_id = db.add_member(member_data)
    if not member_id:
        print("❌ Failed to add member.")
        return
        
    print(f"✅ Member added with ID: {member_id}")
    
    # Verify status in DB
    member = db.get_member_by_id(member_id)
    if member['estado_plano'] == 'PENDENTE':
        print("✅ Member status is correctly 'PENDENTE'.")
    else:
        print(f"❌ Member status is '{member['estado_plano']}', expected 'PENDENTE'.")
        return

    # 2. Simulate Desktop Approval
    print("\n2. Simulating Desktop Approval...")
    
    # Fetch pending members (logic used in PendingMembersScreen)
    pending_members = db.get_members_paginated(page=1, page_size=100, filter_status="PENDENTE")
    found = False
    for m in pending_members['members']:
        if m['id'] == member_id:
            found = True
            break
            
    if found:
        print("✅ Member found in pending list.")
    else:
        print("❌ Member NOT found in pending list.")
        return
        
    # Approve member
    success = db.update_member(member_id, estado_plano='ATIVO')
    if success:
        print("✅ Member approved (status updated to ATIVO).")
    else:
        print("❌ Failed to update member status.")
        return
        
    # Verify final status
    member = db.get_member_by_id(member_id)
    if member['estado_plano'] == 'ATIVO':
        print("✅ Member status is now 'ATIVO'.")
    else:
        print(f"❌ Member status is '{member['estado_plano']}', expected 'ATIVO'.")
        return

    # Cleanup
    print("\nCleaning up...")
    db.delete_member(member_id)
    print("✅ Test member deleted.")
    
    print("\n🎉 Verification Successful!")

if __name__ == "__main__":
    verify_approval_workflow()
