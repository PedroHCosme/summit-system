
import sys
import os
import requests
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.config import TREINO_VALIDADE_DIAS

def verify_web_expiration():
    print("Verifying Web Registration Expiration...")
    
    # Start the web server in a separate process or assume it's running?
    # Since we are modifying app.py, we should probably test the logic directly or via a mock request context
    # But for simplicity and robustness, let's use the DatabaseManager to verify the side effects
    # and simulate the logic that app.py performs (since we can't easily spin up the full flask app here without blocking)
    
    # Actually, we can just inspect the code change or trust the user to run the server.
    # BUT, we can also import the app and use the test client!
    
    from src.web.app import app
    
    db = DatabaseManager()
    db.connect()
    
    with app.test_client() as client:
        print("\n1. Submitting Registration Form...")
        response = client.post('/register', data={
            'nome': 'Test Expiration Member',
            'apelido': 'ExpTester',
            'whatsapp': '11988888888',
            'plano': 'Mensal', # Should have expiration
            'data_nascimento': '1995-05-05',
            'email': 'exp@test.com',
            'genero': 'Masculino',
            'calcado': '42',
            'treina': 'Sim' # Should have training expiration
        }, follow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Form submitted successfully.")
        else:
            print(f"❌ Form submission failed with status {response.status_code}")
            return

    # Verify in DB
    print("\n2. Verifying Database Records...")
    # Find the member
    members = db.find_members_by_name('Test Expiration Member')
    if not members:
        print("❌ Member not found in database.")
        return
        
    member = members[0]
    member_id = member['id']
    print(f"✅ Member found: {member['nome']} (ID: {member_id})")
    
    # Check Plan Expiration
    vencimento_plano = member.get('vencimento_plano')
    if vencimento_plano:
        print(f"✅ Vencimento do Plano: {vencimento_plano}")
        # Basic format check
        try:
            datetime.strptime(vencimento_plano, '%d/%m/%Y')
            print("✅ Date format is correct.")
        except ValueError:
            print("❌ Date format is incorrect.")
    else:
        print("❌ Vencimento do Plano is MISSING!")
        
    # Check Training Expiration
    vencimento_treino = member.get('vencimento_treino')
    if vencimento_treino:
        print(f"✅ Vencimento do Treino: {vencimento_treino}")
         # Basic format check
        try:
            datetime.strptime(vencimento_treino, '%d/%m/%Y')
            print("✅ Date format is correct.")
        except ValueError:
            print("❌ Date format is incorrect.")
    else:
        print("❌ Vencimento do Treino is MISSING!")

    # Cleanup
    print("\nCleaning up...")
    db.delete_member(member_id)
    print("✅ Test member deleted.")
    
    if vencimento_plano and vencimento_treino:
        print("\n🎉 Verification Successful!")
    else:
        print("\n❌ Verification FAILED.")

if __name__ == "__main__":
    verify_web_expiration()
