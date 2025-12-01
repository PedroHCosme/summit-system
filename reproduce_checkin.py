from src.data.database_manager import DatabaseManager
from datetime import datetime

db = DatabaseManager()
db.connect()

# Find Guilherme Carvalho
cursor = db.connection.cursor()
cursor.execute("SELECT id, nome, plano FROM membros WHERE nome LIKE '%Guilherme Carvalho%'")
member = cursor.fetchone()
print(f"Member found: {member}")

if member:
    member_id = member[0]
    
    # Simulate add_checkin logic manually to debug
    cursor.execute("SELECT plano, nome FROM membros WHERE id = ?", (member_id,))
    result = cursor.fetchone()
    member_data = dict(result)
    plano_atual = member_data.get('plano', '')
    print(f"Plano atual from DB: '{plano_atual}'")
    
    normalized = db._normalize_plan_for_checkin(plano_atual)
    print(f"Normalized plan: '{normalized}'")
    
    from src.config import PLANOS_PAGAMENTO_POR_CHECKIN
    print(f"Config PLANOS_PAGAMENTO_POR_CHECKIN: {PLANOS_PAGAMENTO_POR_CHECKIN}")
    
    valor = PLANOS_PAGAMENTO_POR_CHECKIN.get(normalized)
    print(f"Calculated value: {valor}")
    
    if valor == 35.0:
        print("BUG REPRODUCED: Value is 35.0!")
    elif valor == 15.0:
        print("Value is correct (15.0). Cannot reproduce with current state.")
    else:
        print(f"Value is {valor}")
