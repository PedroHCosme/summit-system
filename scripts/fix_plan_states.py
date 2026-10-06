"""Script para corrigir estados de planos no banco de dados.

Este script atualiza o estado_plano de todos os membros baseado na data de vencimento:
- ATIVO: vencimento >= hoje
- INATIVO: vencimento < hoje
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def corrigir_estados_planos(db_path='gym_database.db'):
    """Corrige os estados dos planos baseado nas datas de vencimento."""
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar todos os membros com vencimento
        cursor.execute("""
            SELECT id, nome, vencimento_plano, estado_plano
            FROM membros
            WHERE vencimento_plano IS NOT NULL AND vencimento_plano != ''
        """)
        
        membros = cursor.fetchall()
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        atualizados = 0
        erros = 0
        
        print(f"🔍 Analisando {len(membros)} membros com data de vencimento...")
        print()
        
        for member_id, nome, vencimento_str, estado_atual in membros:
            try:
                # Tentar parsear a data (múltiplos formatos)
                vencimento_dt = None
                
                if '/' in vencimento_str:
                    # Formato DD/MM/YYYY
                    vencimento_dt = datetime.strptime(vencimento_str, '%d/%m/%Y')
                elif '-' in vencimento_str:
                    # Formato DD-MM-YY (ano com 2 dígitos)
                    if len(vencimento_str.split('-')[2]) == 2:
                        vencimento_dt = datetime.strptime(vencimento_str, '%d-%m-%y')
                    else:
                        # Formato YYYY-MM-DD
                        vencimento_dt = datetime.strptime(vencimento_str, '%Y-%m-%d')
                else:
                    # Tentar YYYY-MM-DD sem separador
                    vencimento_dt = datetime.strptime(vencimento_str, '%Y%m%d')
                
                vencimento_dt = vencimento_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                
                # Calcular estado correto
                if vencimento_dt < hoje:
                    estado_correto = 'INATIVO'
                else:
                    estado_correto = 'ATIVO'
                
                # Verificar se precisa atualizar
                if estado_atual != estado_correto:
                    cursor.execute("""
                        UPDATE membros
                        SET estado_plano = ?
                        WHERE id = ?
                    """, (estado_correto, member_id))
                    
                    atualizados += 1
                    dias = (vencimento_dt - hoje).days
                    
                    if estado_correto == 'ATIVO':
                        print(f"✅ {nome}: {estado_atual} → ATIVO (vence em {dias} dias)")
                    else:
                        print(f"❌ {nome}: {estado_atual} → INATIVO (venceu há {abs(dias)} dias)")
            
            except ValueError as e:
                erros += 1
                print(f"⚠️  {nome}: Erro ao parsear data '{vencimento_str}': {e}")
        
        # Commit das alterações
        conn.commit()
        
        print()
        print("=" * 60)
        print(f"✅ Correção concluída!")
        print(f"📊 Estatísticas:")
        print(f"   • Total de membros analisados: {len(membros)}")
        print(f"   • Membros atualizados: {atualizados}")
        print(f"   • Membros já corretos: {len(membros) - atualizados - erros}")
        print(f"   • Erros: {erros}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao corrigir estados: {e}")
        conn.rollback()
    
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("🔧 CORREÇÃO DE ESTADOS DE PLANOS")
    print("=" * 60)
    print()
    
    # Verificar se o banco existe
    db_path = Path('gym_database.db')
    if not db_path.exists():
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print("   Execute este script na raiz do projeto!")
        exit(1)
    
    print(f"📁 Banco de dados: {db_path.absolute()}")
    print()
    
    # Executar correção
    corrigir_estados_planos(str(db_path))
    print()
    print("✅ Script finalizado!")
