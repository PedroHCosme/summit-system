from src.data.database_manager import DatabaseManager
from datetime import datetime

db = DatabaseManager()
db.connect()

# Find Guilherme Carvalho
cursor = db.connection.cursor()
cursor.execute("SELECT id, nome, plano FROM membros WHERE nome LIKE '%Guilherme Carvalho%'")
member = cursor.fetchone()

if member:
    member_id = member[0]
    now = datetime.now()
    
    # 1. Simulate existing correct payment (Gympass, 15.0)
    db.add_payment(
        member_id=member_id,
        valor=15.0,
        tipo_transacao="Gympass",
        descricao="Check-in - Gympass",
        metodo_pagamento="Check-in",
        data_pagamento=now
    )
    print("Created initial Gympass payment.")
    
    # 2. Simulate sync trying to create "Diária" payment for same check-in
    # This calls _create_checkin_payment_if_missing
    db._create_checkin_payment_if_missing(
        member_id=member_id,
        checkin_datetime=now,
        plan_for_payment="Diária",
        member_name="Guilherme Carvalho"
    )
    print("Called _create_checkin_payment_if_missing with 'Diária'.")
    
    # 3. Check if duplicate payment was created
    cursor.execute("""
        SELECT count(*) FROM pagamentos 
        WHERE member_id = ? 
        AND DATE(data_pagamento) = DATE(?)
        AND tipo_transacao = 'Diária'
    """, (member_id, now))
    
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("SUCCESS: Duplicate 'Diária' payment was PREVENTED.")
    else:
        print(f"FAILURE: Duplicate 'Diária' payment was CREATED (count={count}).")
        
    # Cleanup
    cursor.execute("DELETE FROM pagamentos WHERE member_id = ? AND DATE(data_pagamento) = DATE(?)", (member_id, now))
    db.connection.commit()
