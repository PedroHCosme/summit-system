"""Script para adicionar a coluna email à tabela membros."""

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
    
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(membros)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'email' in column_names:
        print("✓ Coluna 'email' já existe na tabela 'membros'!")
    else:
        print("Adicionando coluna 'email' à tabela 'membros'...")
        
        # Adicionar a coluna email
        cursor.execute("""
            ALTER TABLE membros
            ADD COLUMN email TEXT
        """)
        
        conn.commit()
        print("✓ Coluna 'email' adicionada com sucesso!")
    
    # Verificar a estrutura da tabela
    cursor.execute("PRAGMA table_info(membros)")
    columns = cursor.fetchall()
    
    print("\nEstrutura atual da tabela 'membros':")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    conn.close()
    print("\n✓ Migração concluída com sucesso!")
    
except Exception as e:
    print(f"\n✗ Erro durante a migração: {e}")
    import traceback
    traceback.print_exc()
