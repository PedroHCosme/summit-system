"""Script para adicionar a tabela de pagamentos ao banco de dados existente."""

import sqlite3
import os

# Caminho para o banco de dados
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_dir, "gym_database.db")

print(f"Conectando ao banco de dados: {db_path}")

try:
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a tabela já existe
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pagamentos'
    """)
    
    if cursor.fetchone():
        print("✓ Tabela 'pagamentos' já existe!")
    else:
        print("Criando tabela 'pagamentos'...")
        
        # Criar a tabela de pagamentos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pagamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                data_pagamento TEXT NOT NULL,
                tipo_transacao TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                metodo_pagamento TEXT,
                nova_data_vencimento TEXT,
                FOREIGN KEY (member_id) REFERENCES membros(id)
            )
        """)
        
        conn.commit()
        print("✓ Tabela 'pagamentos' criada com sucesso!")
    
    # Verificar a estrutura da tabela
    cursor.execute("PRAGMA table_info(pagamentos)")
    columns = cursor.fetchall()
    
    print("\nEstrutura da tabela 'pagamentos':")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✓ Migração concluída com sucesso!")
    
except Exception as e:
    print(f"\n✗ Erro durante a migração: {e}")
    import traceback
    traceback.print_exc()
