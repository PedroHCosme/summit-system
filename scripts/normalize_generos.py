#!/usr/bin/env python3
"""
Script para normalizar os valores de gênero no banco de dados.
Converte "M" para "Masculino" e "F" para "Feminino".
"""

import sqlite3
import sys
import os
from pathlib import Path

# Define o caminho do banco de dados
project_root = Path(__file__).parent.parent
DB_PATH = os.path.join(project_root, "gym_database.db")


def normalize_generos():
    """Normaliza os valores de gênero no banco de dados."""
    
    print("Conectando ao banco de dados...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Primeiro, vamos verificar quais valores existem atualmente
        print("\nVerificando valores de gênero existentes...")
        cursor.execute("SELECT DISTINCT genero FROM membros WHERE genero IS NOT NULL ORDER BY genero")
        generos_atuais = cursor.fetchall()
        
        print("Gêneros encontrados:")
        for genero in generos_atuais:
            cursor.execute("SELECT COUNT(*) FROM membros WHERE genero = ?", (genero[0],))
            count = cursor.fetchone()[0]
            print(f"  - '{genero[0]}': {count} membros")
        
        # Normalizar para "Masculino"
        print("\nNormalizando para 'Masculino'...")
        cursor.execute("UPDATE membros SET genero = 'Masculino' WHERE genero IN ('M', 'Male', 'masculino', 'm')")
        m_updated = cursor.rowcount
        print(f"  ✓ {m_updated} registros atualizados para 'Masculino'")
        
        # Normalizar para "Feminino"
        print("\nNormalizando para 'Feminino'...")
        cursor.execute("UPDATE membros SET genero = 'Feminino' WHERE genero IN ('F', 'Female', 'feminino', 'f')")
        f_updated = cursor.rowcount
        print(f"  ✓ {f_updated} registros atualizados para 'Feminino'")

        # Normalizar para "Outro"
        print("\nNormalizando para 'Outro'...")
        cursor.execute("UPDATE membros SET genero = 'Outro' WHERE genero IN ('Other', 'other', 'outro', 'o', 'T', 't')")
        o_updated = cursor.rowcount
        print(f"  ✓ {o_updated} registros atualizados para 'Outro'")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar o resultado final
        print("\n" + "="*50)
        print("Valores após normalização:")
        cursor.execute("SELECT DISTINCT genero FROM membros WHERE genero IS NOT NULL ORDER BY genero")
        generos_finais = cursor.fetchall()
        
        for genero in generos_finais:
            cursor.execute("SELECT COUNT(*) FROM membros WHERE genero = ?", (genero[0],))
            count = cursor.fetchone()[0]
            print(f"  - '{genero[0]}': {count} membros")
        
        print("\n✓ Normalização concluída com sucesso!")
        print(f"Total de registros atualizados: {m_updated + f_updated + o_updated}")
        
    except Exception as e:
        print(f"\n✗ Erro ao normalizar gêneros: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()
    
    return True


if __name__ == "__main__":
    print("="*50)
    print("Script de Normalização de Gêneros")
    print("="*50)
    
    success = normalize_generos()
    
    if success:
        print("\n✓ Script executado com sucesso!")
        sys.exit(0)
    else:
        print("\n✗ Script falhou!")
        sys.exit(1)
