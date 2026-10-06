"""Script para corrigir estados de planos baseado na data de vencimento.

Problema: Alguns estados estão como INATIVO quando deveriam ser ATIVO.
Solução: Recalcular o estado baseado na data atual vs vencimento.
Suporta múltiplos formatos: DD/MM/YYYY, DD-MM-YY, YY-MM-DD, YYYY-MM-DD
"""

import sqlite3
from datetime import datetime
from pathlib import Path


def parse_date(date_str: str) -> datetime:
    """
    Parse data com suporte a múltiplos formatos.
    
    Formatos suportados:
    - DD/MM/YYYY (ex: 25/11/2025)
    - DD-MM-YYYY (ex: 25-11-2025)
    - DD-MM-YY (ex: 25-11-25)
    - YY-MM-DD (ex: 25-11-18) -> 2025-11-18
    - YYYY-MM-DD (ex: 2025-11-18)
    - YYYYMMDD (ex: 20251118)
    """
    if not date_str or not date_str.strip():
        return None
    
    try:
        # Formato DD/MM/YYYY
        if '/' in date_str:
            return datetime.strptime(date_str, '%d/%m/%Y')
        elif '-' in date_str:
            parts = date_str.split('-')
            
            # Detectar formato baseado no primeiro número
            first_num = int(parts[0])
            
            if first_num > 31:
                # Formato YYYY-MM-DD (ano com 4 dígitos)
                return datetime.strptime(date_str, '%Y-%m-%d')
            elif len(parts[2]) == 4:
                # Formato DD-MM-YYYY (ano com 4 dígitos no final)
                return datetime.strptime(date_str, '%d-%m-%Y')
            else:
                # Ambos com 2 dígitos: decidir entre DD-MM-YY e YY-MM-DD
                second_num = int(parts[1])
                third_num = int(parts[2])
                
                if second_num > 12:
                    # Não pode ser mês, então é DD-MM-YY
                    return datetime.strptime(date_str, '%d-%m-%y')
                elif third_num > 31:
                    # Terceiro não pode ser dia, então é YY-MM-DD
                    return datetime.strptime(date_str, '%y-%m-%d')
                else:
                    # Ambíguo: assumir YY-MM-DD, mas verificar se faz sentido
                    try:
                        temp_dt = datetime.strptime(date_str, '%y-%m-%d')
                        if temp_dt.year < 2020:
                            return datetime.strptime(date_str, '%d-%m-%y')
                        else:
                            return temp_dt
                    except ValueError:
                        return datetime.strptime(date_str, '%d-%m-%y')
        else:
            # Sem separador, tentar YYYYMMDD
            return datetime.strptime(date_str, '%Y%m%d')
    except ValueError as e:
        print(f"   ⚠️  Erro ao parsear data '{date_str}': {e}")
        return None


def fix_plan_states(db_path='gym_database.db'):
    """Corrige os estados dos planos baseado na data de vencimento."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("🔧 CORREÇÃO: Estados de Planos (v2 - Suporte YY-MM-DD)")
        print("=" * 60)
        print()
        
        # Buscar todos os membros com vencimento_plano
        cursor.execute("""
            SELECT id, nome, vencimento_plano, estado_plano
            FROM membros
            WHERE vencimento_plano IS NOT NULL AND vencimento_plano != ''
        """)
        
        members = cursor.fetchall()
        
        print(f"📊 Total de membros com planos: {len(members)}")
        print()
        
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        corretos = 0
        incorretos = 0
        erros = 0
        updates = []
        
        for member in members:
            member_id = member['id']
            nome = member['nome']
            vencimento_str = member['vencimento_plano']
            estado_atual = member['estado_plano']
            
            # Parse da data
            vencimento_dt = parse_date(vencimento_str)
            
            if vencimento_dt is None:
                print(f"   ⚠️  {nome}: Data inválida '{vencimento_str}'")
                erros += 1
                continue
            
            # Normalizar para comparação sem hora
            vencimento_dt = vencimento_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Calcular estado correto
            estado_correto = 'INATIVO' if vencimento_dt < hoje else 'ATIVO'
            
            if estado_atual == estado_correto:
                corretos += 1
            else:
                incorretos += 1
                days_diff = (vencimento_dt - hoje).days
                
                print(f"   ❌ {nome}:")
                print(f"      Vencimento: {vencimento_str} ({vencimento_dt.strftime('%d/%m/%Y')})")
                print(f"      Dias até vencer: {days_diff}")
                print(f"      Estado atual: {estado_atual}")
                print(f"      Estado correto: {estado_correto}")
                print()
                
                updates.append((estado_correto, member_id))
        
        print()
        print("=" * 60)
        print("📊 RESULTADO DA ANÁLISE:")
        print("=" * 60)
        print(f"   ✅ Corretos: {corretos}")
        print(f"   ❌ Incorretos: {incorretos}")
        print(f"   ⚠️  Erros de parsing: {erros}")
        print()
        
        if incorretos > 0:
            resposta = input(f"Deseja atualizar os {incorretos} registros incorretos? (s/N): ")
            
            if resposta.lower() == 's':
                for estado, member_id in updates:
                    cursor.execute("""
                        UPDATE membros
                        SET estado_plano = ?
                        WHERE id = ?
                    """, (estado, member_id))
                
                conn.commit()
                print()
                print(f"✅ {incorretos} estados corrigidos com sucesso!")
            else:
                print()
                print("❌ Nenhuma alteração foi feita.")
        else:
            print("✅ Todos os estados estão corretos!")
        
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
    
    fix_plan_states(str(db_path))
    print("✅ Script finalizado!")
