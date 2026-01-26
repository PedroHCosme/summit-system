
import sys
import os
import sqlite3
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.database_manager import DatabaseManager

def test_update_member_fields():
    db_path = "test_gym_update.db"
    
    # Clean up previous test
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db = DatabaseManager(db_path)
    if not db.connect():
        print("Failed to connect to DB")
        return
        
    db.create_tables()
    
    # Create a member
    member_data = {
        "nome": "Test Member",
        "plano": "Mensal",
        "estado_plano": "ATIVO",
        "genero": "Masculino"
    }
    
    member_id = db.add_member(member_data)
    print(f"Member created with ID: {member_id}")
    
    # Test 1: Update using update_member_from_dict (which EditMemberDialog uses indirectly or directly)
    print("\nTesting update_member_from_dict...")
    update_data = {
        "id": member_id,
        "profissao": "Engenheiro",
        "contato_emergencia": "11999999999"
    }
    
    success = db.update_member_from_dict(update_data)
    if not success:
        print("update_member_from_dict returned False")
    
    # Verify
    member = db.get_member_by_id(member_id)
    print(f"Member after dict update: Profession={member.get('profissao')}, Emergency={member.get('contato_emergencia')}")
    
    if member.get('profissao') == "Engenheiro" and member.get('contato_emergencia') == "11999999999":
        print("PASS: update_member_from_dict updated fields correctly.")
    else:
        print("FAIL: update_member_from_dict failed to update fields.")
        
    # Test 2: Update using update_member (direct args)
    print("\nTesting update_member (direct args)...")
    success = db.update_member(
        member_id,
        profissao="Professor",
        contato_emergencia="11888888888"
    )
    if not success:
        print("update_member returned False")
        
    # Verify
    member = db.get_member_by_id(member_id)
    print(f"Member after direct update: Profession={member.get('profissao')}, Emergency={member.get('contato_emergencia')}")
    
    if member.get('profissao') == "Professor" and member.get('contato_emergencia') == "11888888888":
        print("PASS: update_member updated fields correctly.")
    else:
        print("FAIL: update_member failed to update fields.")

    db.connection.close()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_update_member_fields()
