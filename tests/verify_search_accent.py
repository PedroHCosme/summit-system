import sys
import os

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.db import init_db, get_session_factory
from src.data.models import Membro
from src.services.member_service import MemberService
from sqlalchemy import text

def verify_accent_search():
    print("=== Verifying Accent-Insensitive Search ===")
    
    # Initialize DB (in-memory or uses existing configuration)
    # We will use a test session
    SessionLocal = get_session_factory()
    session = SessionLocal()
    
    # Clean up any existing test data (optional, but good for repeatability)
    # Be careful not to delete real data if running on prod DB.
    # For safety, let's just insert a very specific unique name
    
    test_name = "Inácio Teste"
    test_search_term = "Inacio"
    
    # Check if exists and delete
    existing = session.query(Membro).filter(Membro.nome == test_name).first()
    if existing:
        session.delete(existing)
        session.commit()
        print(f"cleaned up existing '{test_name}'")

    # Insert test member
    new_member = Membro(
        nome=test_name,
        plano="Mensal",
        estado_plano="ATIVO"
    )
    session.add(new_member)
    session.commit()
    print(f"Inserted member: {test_name}")
    
    # Test search with MemberService
    service = MemberService(db_session=session)
    
    print(f"\nSearching for '{test_search_term}' (no accent)...")
    results = service.search_by_name(test_search_term)
    
    found = False
    for member in results:
        if member.nome == test_name:
            found = True
            break
            
    if found:
        print("✅ SUCCESS: Found 'Inácio' when searching for 'Inacio'")
    else:
        print("❌ FAILURE: Did not find 'Inácio' when searching for 'Inacio'")
        print("Results found:", [m.nome for m in results])

    # Test search with accent
    print(f"\nSearching for '{test_name}' (with accent)...")
    results_accent = service.search_by_name(test_name)
    found_accent = False
    for member in results_accent:
        if member.nome == test_name:
            found_accent = True
            break
    
    if found_accent:
         print("✅ SUCCESS: Found 'Inácio' when searching for 'Inácio'")
    else:
         print("❌ FAILURE: Did not find 'Inácio' when searching for 'Inácio'")


    # Test REVERSE: stored without accent, search with accent
    test_name_no_accent = "Joao Sem Acento"
    test_search_term_accent = "João"
    
     # Check if exists and delete
    existing_no = session.query(Membro).filter(Membro.nome == test_name_no_accent).first()
    if existing_no:
        session.delete(existing_no)
        session.commit()
    
    new_member_no = Membro(
        nome=test_name_no_accent,
        plano="Mensal",
        estado_plano="ATIVO"
    )
    session.add(new_member_no)
    session.commit()
    print(f"\nInserted member: {test_name_no_accent}")
    
    print(f"Searching for '{test_search_term_accent}' (with accent)...")
    results_reverse = service.search_by_name(test_search_term_accent)
    
    found_reverse = False
    for member in results_reverse:
        if member.nome == test_name_no_accent:
            found_reverse = True
            break
            
    if found_reverse:
        print("✅ SUCCESS: Found 'Joao' when searching for 'João'")
    else:
        print("❌ FAILURE: Did not find 'Joao' when searching for 'João'")
        print("Results found:", [m.nome for m in results_reverse])
        
    # Cleanup
    session.delete(new_member)
    session.delete(new_member_no)
    session.commit()
    session.close()

if __name__ == "__main__":
    verify_accent_search()
