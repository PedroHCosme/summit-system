
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data.db import get_session_factory, init_db
from src.services.member_service import MemberService
from src.services.checkin_service import CheckinService
from src.data.database_manager import DatabaseManager
from src.data.models import Membro, Frequencia

def reproduce():
    print("🚀 Iniciando reprodução do caso de voucher...")
    
    # 1. Setup DB
    init_db()
    
    # Create services (using same DB session if possible, or allowing them to create their own)
    session_factory = get_session_factory()
    session = session_factory()
    
    member_service = MemberService(db_session=session)
    checkin_service = CheckinService(db_session=session)
    # db_manager = DatabaseManager() # Using legacy for historical check-in insertion if needed
    
    # 2. Create Member (No plan initially)
    print("Creating member...")
    result = member_service.create({
        "nome": "Usuario Teste Voucher",
        "plano": "" 
    })
    member_id = result.member_id
    print(f"Member created: {member_id}")
    
    # 3. Add historical check-ins (e.g., 4 check-ins in the last few days)
    print("Adding 4 historical check-ins...")
    today = datetime.now()
    for i in range(4, 0, -1):
        dt = today - timedelta(days=i)
        # We manually insert check-ins to simulate 'existing' check-ins
        # Using SQLAlchemy directly to avoid CheckinService logic for now
        # OR using checkin_service.perform_checkin but passing a non-quota plan context?
        # Actually, let's just insert into Frequencia table directly.
        c = Frequencia(member_id=member_id, checkin_datetime=dt)
        session.add(c)
    session.commit()
    
    # Verify check-ins
    hist = checkin_service.get_member_history(member_id)
    print(f"Historical check-ins found: {len(hist)}")
    
    # 4. Update Member to 'Pacote 10' (Quota plan)
    print("Updating member to 'Pacote 10' with 10 credits...")
    # Simulate EditMemberDialog which sends 'voucher_credits': 10
    update_data = {
        "id": member_id,
        "plano": "Pacote 10",
        "voucher_credits": 10,  # User input from spinbox
        "estado_plano": "ATIVO"
    }
    
    # Note: 'Pacote 10' must exist in Planos table with is_quota=True
    # If not, let's create it or ensure it exists
    from src.data.models import Plano
    plan = session.query(Plano).filter(Plano.nome == "Pacote 10").first()
    if not plan:
        print("Creating 'Pacote 10' plan...")
        plan = Plano(nome="Pacote 10", preco=200.0, is_quota=True, quota_amount=10)
        session.add(plan)
        session.commit()
    
    # Perform Update
    member_service.update_from_dict(update_data)
    
    # 5. Check Credits
    member = member_service.get_by_id(member_id)
    print(f"Credits after update: {member.voucher_credits}")
    
    if member.voucher_credits == 10:
        print("✅ Correct: Credits are 10. Historical check-ins did NOT consume credits directly.")
    elif member.voucher_credits == 6:
        print("❌ Issue Reproduced: Credits are 6. 4 historical check-ins consumed credits!")
    else:
        print(f"❓ Unexpected credits: {member.voucher_credits}")

    # 6. Perform NEW check-in
    print("Performing NEW check-in...")
    checkin_service.perform_checkin(member_id)
    
    session.refresh(member)
    print(f"Credits after new check-in: {member.voucher_credits}")
    
    if member.voucher_credits == 9: # Or 5 if it was 6
        print("✅ New check-in correctly deducted 1 credit.")
    else:
        print("❌ New check-in deduction failed.")

if __name__ == "__main__":
    reproduce()
