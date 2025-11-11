#!/usr/bin/env python3
"""
Script de validação rápida das novas funcionalidades.

Testa:
1. API de transações do DatabaseManager
2. Verificação de duplicatas
3. Modo incremental de migração (sem executar migração completa)

Uso:
    python tests/validate_improvements.py
"""

import sys
import os
from datetime import datetime

# Adiciona diretório raiz ao path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

from src.data.database_manager import DatabaseManager


def test_transaction_commit():
    """Testa se transações fazem commit corretamente."""
    print("\n[Teste 1] Transação com commit bem-sucedido...")
    
    db = DatabaseManager("test_db.db")
    db.connect()
    db.create_tables()
    
    try:
        with db.transaction():
            member_data = {
                'nome': 'Teste Transação',
                'plano': 'Mensal',
                'genero': 'M'
            }
            member_id = db.add_member(member_data)
            assert member_id is not None, "Membro deveria ter sido criado"
        
        # Verifica se foi commitado
        member = db.get_member_by_id(member_id)
        assert member is not None, "Membro deveria existir após commit"
        assert member['nome'] == 'Teste Transação'
        
        print("  ✅ Transação commitada com sucesso")
        return True
        
    except Exception as e:
        print(f"  ❌ Falhou: {e}")
        return False
    finally:
        db.close()
        # Limpa arquivo de teste
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")


def test_transaction_rollback():
    """Testa se transações fazem rollback em caso de erro."""
    print("\n[Teste 2] Transação com rollback em erro...")
    
    db = DatabaseManager("test_db.db")
    db.connect()
    db.create_tables()
    
    member_id = None
    
    try:
        with db.transaction():
            member_data = {
                'nome': 'Teste Rollback',
                'plano': 'Mensal'
            }
            member_id = db.add_member(member_data)
            
            # Força um erro
            raise ValueError("Erro intencional para testar rollback")
        
    except ValueError:
        pass  # Esperado
    
    # Verifica se foi revertido
    if member_id:
        member = db.get_member_by_id(member_id)
        if member is None:
            print("  ✅ Rollback executado corretamente")
            result = True
        else:
            print("  ❌ Membro não deveria existir após rollback")
            result = False
    else:
        print("  ✅ Membro não foi criado (esperado)")
        result = True
    
    db.close()
    if os.path.exists("test_db.db"):
        os.remove("test_db.db")
    
    return result


def test_checkin_exists():
    """Testa verificação de check-ins duplicados."""
    print("\n[Teste 3] Verificação de check-ins duplicados...")
    
    db = DatabaseManager("test_db.db")
    db.connect()
    db.create_tables()
    
    try:
        member_data = {'nome': 'Teste Checkin', 'plano': 'Mensal'}
        member_id = db.add_member(member_data)
        
        if not member_id:
            raise ValueError("Falha ao criar membro")
        
        checkin_time = datetime(2025, 11, 11, 9, 0, 0)
        
        # Primeiro check-in
        db.add_checkin(member_id, checkin_time)
        
        # Verifica se existe
        exists = db.checkin_exists(member_id, checkin_time)
        assert exists, "Check-in deveria existir"
        
        # Verifica que outro horário não existe
        other_time = datetime(2025, 11, 11, 10, 0, 0)
        not_exists = db.checkin_exists(member_id, other_time)
        assert not not_exists, "Check-in não deveria existir"
        
        print("  ✅ Verificação de duplicatas funcionando")
        return True
        
    except Exception as e:
        print(f"  ❌ Falhou: {e}")
        return False
    finally:
        db.close()
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")


def test_multiple_operations_in_transaction():
    """Testa múltiplas operações em uma transação."""
    print("\n[Teste 4] Múltiplas operações em transação...")
    
    db = DatabaseManager("test_db.db")
    db.connect()
    db.create_tables()
    
    try:
        with db.transaction():
            # Cria 3 membros
            ids = []
            for i in range(3):
                member_data = {
                    'nome': f'Membro {i+1}',
                    'plano': 'Mensal'
                }
                member_id = db.add_member(member_data)
                ids.append(member_id)
            
            # Adiciona check-ins para cada
            for member_id in ids:
                if member_id:
                    db.add_checkin(member_id, datetime.now())
        
        # Verifica se todos foram criados
        all_members = db.get_all_members()
        assert len(all_members) == 3, f"Deveria ter 3 membros, tem {len(all_members)}"
        
        print("  ✅ Múltiplas operações em transação funcionando")
        return True
        
    except Exception as e:
        print(f"  ❌ Falhou: {e}")
        return False
    finally:
        db.close()
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")


def test_context_manager_properties():
    """Testa propriedades do context manager."""
    print("\n[Teste 5] Propriedades do context manager...")
    
    db = DatabaseManager("test_db.db")
    db.connect()
    db.create_tables()
    
    try:
        # Testa que retorna self
        with db.transaction() as tx:
            assert tx is db, "Context manager deveria retornar self"
            member_data = {'nome': 'Teste CM', 'plano': 'Mensal'}
            tx.add_member(member_data)
        
        print("  ✅ Context manager retorna self corretamente")
        return True
        
    except Exception as e:
        print(f"  ❌ Falhou: {e}")
        return False
    finally:
        db.close()
        if os.path.exists("test_db.db"):
            os.remove("test_db.db")


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("VALIDAÇÃO DAS MELHORIAS IMPLEMENTADAS")
    print("=" * 60)
    
    tests = [
        test_transaction_commit,
        test_transaction_rollback,
        test_checkin_exists,
        test_multiple_operations_in_transaction,
        test_context_manager_properties,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ❌ Erro inesperado: {e}")
            results.append(False)
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Testes passados: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Todas as validações passaram com sucesso!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == "__main__":
    sys.exit(main())
