"""Script para corrigir o tipo de data_pagamento de DATE para DATETIME.

O problema: data_pagamento estava como DATE, que remove a hora.
Solução: Alterar para DATETIME para preservar hora completa.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path


def fix_payment_datetime(db_path='gym_database.db'):
    """Corrige o tipo de data_pagamento para DATETIME."""
    
    # Criar backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'gym_database_backup_datetime_{timestamp}.db'
    
    print("=" * 60)
    print("🔧 CORREÇÃO: data_pagamento DATE → DATETIME")
    print("=" * 60)
    print()
    print(f"📁 Banco: {db_path}")
    print(f"💾 Backup: {backup_path}")
    print()
    
    # Backup
    shutil.copy2(db_path, backup_path)
    print("✅ Backup criado!")
    print()
    
    # Conectar
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Iniciando migração...")
        print()
        
        # 1. Criar tabela temporária com DATETIME
        cursor.execute("""
            CREATE TABLE pagamentos_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                data_pagamento DATETIME NOT NULL,     -- MUDOU: DATE → DATETIME
                tipo_transacao TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                metodo_pagamento TEXT,
                nova_data_vencimento DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                CHECK (valor >= 0),
                
                FOREIGN KEY (member_id) REFERENCES membros(id) ON DELETE CASCADE
            )
        """)
        print("✅ Tabela temporária criada (data_pagamento como DATETIME)")
        
        # 2. Copiar dados (SQLite manterá o formato original)
        cursor.execute("""
            INSERT INTO pagamentos_new 
            SELECT * FROM pagamentos
        """)
        
        rows_copied = cursor.rowcount
        print(f"✅ {rows_copied} pagamentos copiados")
        
        # 3. Dropar tabela antiga
        cursor.execute("DROP TABLE pagamentos")
        print("✅ Tabela antiga removida")
        
        # 4. Renomear tabela nova
        cursor.execute("ALTER TABLE pagamentos_new RENAME TO pagamentos")
        print("✅ Tabela renomeada")
        
        # 5. Recriar índices
        cursor.execute("CREATE INDEX idx_pagamentos_member_id ON pagamentos(member_id)")
        cursor.execute("CREATE INDEX idx_pagamentos_data ON pagamentos(data_pagamento)")
        cursor.execute("CREATE INDEX idx_pagamentos_tipo ON pagamentos(tipo_transacao)")
        print("✅ Índices recriados")
        
        # Commit
        conn.commit()
        
        print()
        print("=" * 60)
        print("✅ MIGRAÇÃO CONCLUÍDA!")
        print("=" * 60)
        print()
        print("📊 Resultado:")
        print(f"   • Pagamentos migrados: {rows_copied}")
        print(f"   • Tipo da coluna: DATE → DATETIME")
        print(f"   • Backup salvo em: {backup_path}")
        print()
        print("⚠️  IMPORTANTE:")
        print("   • Novos check-ins agora salvarão hora completa")
        print("   • Pagamentos antigos mantêm data (sem hora)")
        print("   • Consultas financeiras agora funcionarão corretamente")
        print()
        
    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        print(f"💾 Restaure o backup se necessário: {backup_path}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    # Verificar se o banco existe
    db_path = Path('gym_database.db')
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print("   Execute este script na raiz do projeto!")
        exit(1)
    
    # Executar correção
    fix_payment_datetime(str(db_path))
    print("✅ Script finalizado!")
