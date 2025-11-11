"""Script para limpar datas de nascimento inválidas (----------).

Problema: Datas importadas como '----------' do Google Sheets.
Solução: Substituir por string vazia para que não apareçam na interface.
"""

import sqlite3
from pathlib import Path


def fix_birth_dates(db_path='gym_database.db'):
    """Limpa datas de nascimento inválidas."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("🔧 CORREÇÃO: Datas de Nascimento Inválidas")
        print("=" * 60)
        print()
        
        # Verificar quantas datas estão com o problema
        cursor.execute("""
            SELECT COUNT(*) 
            FROM membros 
            WHERE data_nascimento IN ('----------', '---', '--', 'N/A', 'n/a', '#N/A')
        """)
        
        count = cursor.fetchone()[0]
        
        print(f"📊 Encontrados {count} membros com datas inválidas")
        print()
        
        if count == 0:
            print("✅ Nenhuma data precisa de correção!")
            return
        
        # Limpar as datas inválidas
        cursor.execute("""
            UPDATE membros
            SET data_nascimento = ''
            WHERE data_nascimento IN ('----------', '---', '--', 'N/A', 'n/a', '#N/A')
        """)
        
        conn.commit()
        
        updated = cursor.rowcount
        
        print()
        print("=" * 60)
        print("✅ CORREÇÃO CONCLUÍDA!")
        print("=" * 60)
        print()
        print(f"📊 Total atualizado: {updated} datas limpas")
        print(f"   Valores inválidos ('----------', etc.) → '' (vazio)")
        print()
        print("✅ Agora as datas de nascimento não mostrarão '----------'!")
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
    
    fix_birth_dates(str(db_path))
    print("✅ Script finalizado!")
