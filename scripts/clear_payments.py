"""Script para limpar a tabela de pagamentos."""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager


def clear_payments():
    """Remove todos os pagamentos da tabela."""
    
    db = DatabaseManager()
    
    # Conectar ao banco de dados
    if not db.connect():
        print("❌ Erro ao conectar ao banco de dados!")
        return
    
    print("=== Limpeza de Pagamentos ===\n")
    
    try:
        cursor = db.connection.cursor()
        
        # Contar pagamentos antes
        cursor.execute("SELECT COUNT(*) FROM pagamentos")
        count_before = cursor.fetchone()[0]
        print(f"Pagamentos existentes: {count_before}")
        
        # Deletar todos os pagamentos
        cursor.execute("DELETE FROM pagamentos")
        db.connection.commit()
        
        # Contar pagamentos depois
        cursor.execute("SELECT COUNT(*) FROM pagamentos")
        count_after = cursor.fetchone()[0]
        print(f"Pagamentos após limpeza: {count_after}")
        
        print("\n✅ Limpeza concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao limpar pagamentos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    clear_payments()
