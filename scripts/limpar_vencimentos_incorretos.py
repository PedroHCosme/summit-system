#!/usr/bin/env python3
"""
Script para limpar datas de vencimento de membros com planos que não requerem vencimento.

Planos como Gympass, Totalpass, Diária, Cortesia e Voucher não devem ter data de vencimento.
Este script identifica e limpa essas datas incorretas.
"""
import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.database_manager import DatabaseManager
from src.config import PLANOS_COM_VENCIMENTO

def main():
    # Usar o banco de dados principal
    db_path = project_root / "gym_database.db"
    
    if not db_path.exists():
        print(f"Erro: Banco de dados não encontrado em {db_path}")
        return
    
    print("=" * 60)
    print("LIMPEZA DE VENCIMENTOS INCORRETOS")
    print("=" * 60)
    print(f"\nPlanos COM vencimento: {PLANOS_COM_VENCIMENTO}")
    print("")
    
    db = DatabaseManager(str(db_path))
    if not db.connect():
        print("Erro: Falha ao conectar ao banco de dados.")
        return
    
    try:
        cursor = db.connection.cursor()
        
        # Buscar membros com vencimento_plano que têm planos sem vencimento
        cursor.execute("""
            SELECT id, nome, plano, vencimento_plano 
            FROM membros 
            WHERE vencimento_plano IS NOT NULL 
              AND vencimento_plano != ''
        """)
        
        members_with_vencimento = cursor.fetchall()
        
        to_clean = []
        for row in members_with_vencimento:
            member = dict(row)
            plano = member.get('plano', '')
            if plano and plano not in PLANOS_COM_VENCIMENTO:
                to_clean.append(member)
        
        if not to_clean:
            print("✓ Nenhum membro com vencimento incorreto encontrado.")
            return
        
        print(f"Encontrados {len(to_clean)} membros com vencimento incorreto:\n")
        for m in to_clean:
            print(f"  - ID {m['id']}: {m['nome']} | Plano: {m['plano']} | Vencimento: {m['vencimento_plano']}")
        
        print(f"\nLimpando vencimento de {len(to_clean)} membros...")
        
        # Limpar vencimento_plano
        member_ids = [m['id'] for m in to_clean]
        placeholders = ','.join('?' * len(member_ids))
        cursor.execute(f"""
            UPDATE membros 
            SET vencimento_plano = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """, member_ids)
        
        db.connection.commit()
        
        print(f"\n✓ {cursor.rowcount} registros atualizados com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a limpeza: {e}")
        db.connection.rollback()
    finally:
        db.connection.close()

if __name__ == "__main__":
    main()
