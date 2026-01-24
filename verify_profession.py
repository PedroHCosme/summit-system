
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.data.migrations import DatabaseMigrator
from src.core.models import Pessoa

def verify_profession_field():
    print("Verificando implementação do campo 'Profissão'...")
    
    # 1. Initialize DB and Migrations
    db = DatabaseManager(":memory:") # Use memory DB for test, or local file if needed to check schema persistence
    # Using a temporary file to better simulate the real environment schema update
    db_file = "test_verify_profession.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    db = DatabaseManager(db_file)
    db.connect()
    db.create_tables()
    
    migrator = DatabaseMigrator(db)
    
    print("Executando migrações...")
    migrator.run_all()
    
    # 2. Check Schema
    cursor = db.connection.cursor()
    cursor.execute("PRAGMA table_info(membros)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "profissao" in columns:
        print("SUCCESS: Coluna 'profissao' encontrada na tabela 'membros'.")
    else:
        print("FAILURE: Coluna 'profissao' NÃO encontrada.")
        return

    # 3. Test Persistence
    print("Testando persistência de dados...")
    test_member = {
        "nome": "Teste Profissao",
        "profissao": "Desenvolvedor de Software",
        "plano": "Mensal",
        "data_nascimento": "01/01/1990",
        "whatsapp": "11999999999",
        "genero": "Masculino",
        "email": "teste@example.com"
    }
    
    member_id = db.add_member(test_member)
    
    if not member_id:
        print("FAILURE: Falha ao adicionar membro.")
        return
        
    retrieved_member = db.get_member_by_id(member_id)
    
    if retrieved_member and retrieved_member.get('profissao') == "Desenvolvedor de Software":
        print(f"SUCCESS: Profissão recuperada corretamente: {retrieved_member.get('profissao')}")
    else:
        print(f"FAILURE: Profissão incorreta ou não salva. Valor: {retrieved_member.get('profissao') if retrieved_member else 'None'}")

    db.close()
    if os.path.exists(db_file):
        os.remove(db_file)

if __name__ == "__main__":
    verify_profession_field()
