"""Script para adicionar hora aos pagamentos que estão sem hora.

Problema: Pagamentos antigos salvos como '2025-11-11' sem hora.
Solução: Adicionar '12:00:00' para que sejam comparáveis com ranges de datetime.
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def fix_payment_times(db_path='gym_database.db'):
    """Adiciona hora aos pagamentos que estão sem hora."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("🔧 CORREÇÃO: Adicionar hora aos pagamentos sem timestamp")
        print("=" * 60)
        print()
        
        # Buscar pagamentos sem hora (apenas data)
        cursor.execute("""
            SELECT id, data_pagamento
            FROM pagamentos
            WHERE length(data_pagamento) = 10
        """)
        
        pagamentos_sem_hora = cursor.fetchall()
        
        print(f"📊 Encontrados {len(pagamentos_sem_hora)} pagamentos sem hora")
        print()
        
        if len(pagamentos_sem_hora) == 0:
            print("✅ Nenhum pagamento precisa de correção!")
            return
        
        # Atualizar cada um adicionando 12:00:00
        updated = 0
        for pag_id, data_str in pagamentos_sem_hora:
            # Adicionar hora 12:00:00
            nova_data = f"{data_str} 12:00:00"
            
            cursor.execute("""
                UPDATE pagamentos
                SET data_pagamento = ?
                WHERE id = ?
            """, (nova_data, pag_id))
            
            updated += 1
            
            if updated % 100 == 0:
                print(f"   ✅ {updated} pagamentos atualizados...")
        
        conn.commit()
        
        print()
        print("=" * 60)
        print("✅ CORREÇÃO CONCLUÍDA!")
        print("=" * 60)
        print()
        print(f"📊 Total atualizado: {updated} pagamentos")
        print(f"   Formato antigo: '2025-11-11'")
        print(f"   Formato novo: '2025-11-11 12:00:00'")
        print()
        print("✅ Agora os filtros de data funcionarão corretamente!")
        print()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        conn.rollback()
        raise
    
    finally:
        conn.close()


if __name__ == '__main__':
    db_path = Path('gym_database.db')
    if not db_path.exists():
        print(f"❌ Banco não encontrado: {db_path}")
        exit(1)
    
    fix_payment_times(str(db_path))
    print("✅ Script finalizado!")
