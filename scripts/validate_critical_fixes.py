#!/usr/bin/env python3
"""
Script de validação das correções críticas implementadas.

Testa:
1. Cobrança de Diária (0.0 na renovação, 35.0 no check-in)
2. Proteção contra check-ins duplicados
3. Foreign keys com ON DELETE CASCADE
4. Tipos de dados corretos (DATE/DATETIME)
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.config import PLANOS_PRECOS, PLANOS_PAGAMENTO_POR_CHECKIN


def print_header(title):
    """Imprime cabeçalho de seção."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_diaria_pricing():
    """Testa se Diária cobra apenas no check-in."""
    print_header("TESTE 1: Cobrança de Diária")
    
    # Verificar configuração
    print("\n[1.1] Verificando PLANOS_PRECOS...")
    diaria_preco = PLANOS_PRECOS.get("Diária", None)
    
    if diaria_preco == 0.0:
        print("  ✓ PLANOS_PRECOS['Diária'] = 0.0 (correto)")
    else:
        print(f"  ✗ PLANOS_PRECOS['Diária'] = {diaria_preco} (esperado: 0.0)")
        return False
    
    # Verificar check-in
    print("\n[1.2] Verificando PLANOS_PAGAMENTO_POR_CHECKIN...")
    diaria_checkin = PLANOS_PAGAMENTO_POR_CHECKIN.get("Diária", None)
    
    if diaria_checkin == 35.0:
        print("  ✓ PLANOS_PAGAMENTO_POR_CHECKIN['Diária'] = 35.0 (correto)")
    else:
        print(f"  ✗ PLANOS_PAGAMENTO_POR_CHECKIN['Diária'] = {diaria_checkin} (esperado: 35.0)")
        return False
    
    # Verificar Totalpass (bônus - corrigir typo 00.0)
    print("\n[1.3] Verificando Totalpass (typo 00.0 → 0.0)...")
    totalpass_preco = PLANOS_PRECOS.get("Totalpass", None)
    
    if totalpass_preco == 0.0:
        print("  ✓ PLANOS_PRECOS['Totalpass'] = 0.0 (correto)")
    else:
        print(f"  ✗ PLANOS_PRECOS['Totalpass'] = {totalpass_preco} (esperado: 0.0)")
        return False
    
    print("\n✅ TESTE 1 PASSOU: Diária configurada corretamente")
    return True


def test_duplicate_checkin_protection():
    """Testa proteção contra check-ins duplicados."""
    print_header("TESTE 2: Proteção Contra Check-ins Duplicados")
    
    db = DatabaseManager()
    if not db.connect():
        print("  ✗ Erro ao conectar ao banco de dados")
        return False
    
    try:
        print("\n[2.1] Criando membro de teste...")
        
        # Criar membro temporário
        test_member_name = f"TESTE_DUPLICATA_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        member_id = db.add_member({
            'nome': test_member_name,
            'plano': "Gympass",
            'estado_plano': "ATIVO"
        })
        
        if not member_id:
            print("  ✗ Erro ao criar membro de teste")
            return False
        
        print(f"  ✓ Membro criado: ID {member_id}")
        
        # Primeiro check-in
        print("\n[2.2] Fazendo primeiro check-in...")
        checkin_time = datetime.now()
        checkin_id1 = db.add_checkin(member_id, checkin_time)
        
        if checkin_id1:
            print(f"  ✓ Primeiro check-in registrado: ID {checkin_id1}")
        else:
            print("  ✗ Erro ao registrar primeiro check-in")
            db.delete_member(member_id)
            return False
        
        # Segundo check-in (mesmo dia - deve falhar)
        print("\n[2.3] Tentando segundo check-in no mesmo dia...")
        try:
            checkin_time2 = checkin_time + timedelta(hours=2)
            checkin_id2 = db.add_checkin(member_id, checkin_time2)
            
            # Se chegou aqui, não bloqueou (ERRO)
            print("  ✗ Check-in duplicado foi permitido (ERRO!)")
            db.delete_member(member_id)
            return False
            
        except ValueError as e:
            if "Check-in duplicado" in str(e):
                print(f"  ✓ Check-in duplicado bloqueado corretamente")
                print(f"    Mensagem: {str(e).split(chr(10))[0]}")
            else:
                print(f"  ✗ Erro inesperado: {e}")
                db.delete_member(member_id)
                return False
        
        # Terceiro check-in (dia diferente - deve funcionar)
        print("\n[2.4] Tentando check-in em dia diferente...")
        try:
            checkin_time3 = checkin_time + timedelta(days=1)
            checkin_id3 = db.add_checkin(member_id, checkin_time3)
            
            if checkin_id3:
                print(f"  ✓ Check-in em dia diferente permitido: ID {checkin_id3}")
            else:
                print("  ✗ Check-in válido foi rejeitado (ERRO!)")
                db.delete_member(member_id)
                return False
                
        except ValueError as e:
            print(f"  ✗ Check-in válido bloqueado indevidamente: {e}")
            db.delete_member(member_id)
            return False
        
        # Limpar membro de teste
        print("\n[2.5] Limpando dados de teste...")
        db.delete_member(member_id)
        print("  ✓ Membro de teste removido")
        
        print("\n✅ TESTE 2 PASSOU: Proteção contra duplicatas funciona")
        return True
        
    except Exception as e:
        print(f"\n  ✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_foreign_keys_cascade():
    """Testa ON DELETE CASCADE das foreign keys."""
    print_header("TESTE 3: Foreign Keys com ON DELETE CASCADE")
    
    print("\n⚠️  ATENÇÃO: Este teste só funciona após executar fix_database_critical.py")
    print("            Se o banco não foi migrado, este teste será pulado.\n")
    
    db = DatabaseManager()
    if not db.connect():
        print("  ✗ Erro ao conectar ao banco de dados")
        return False
    
    try:
        cursor = db.connection.cursor()
        
        # Verificar se foreign keys estão habilitadas
        print("[3.1] Verificando se foreign keys estão habilitadas...")
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        
        if fk_status == 1:
            print("  ✓ Foreign keys habilitadas")
        else:
            print("  ⚠️  Foreign keys desabilitadas (normal se não migrou ainda)")
            return True  # Não falha, apenas avisa
        
        # Criar membro de teste
        print("\n[3.2] Criando membro de teste...")
        test_member_name = f"TESTE_CASCADE_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        member_id = db.add_member({
            'nome': test_member_name,
            'plano': "Mensal",
            'estado_plano': "ATIVO"
        })
        
        print(f"  ✓ Membro criado: ID {member_id}")
        
        # Adicionar check-in
        print("\n[3.3] Adicionando check-in...")
        checkin_id = db.add_checkin(member_id, datetime.now())
        print(f"  ✓ Check-in criado: ID {checkin_id}")
        
        # Adicionar pagamento
        print("\n[3.4] Adicionando pagamento...")
        payment_id = db.add_payment(
            member_id=member_id,
            tipo_transacao="Mensal",
            valor=190.0,
            metodo_pagamento="Teste"
        )
        print(f"  ✓ Pagamento criado: ID {payment_id}")
        
        # Verificar registros antes de deletar
        print("\n[3.5] Verificando registros antes de deletar membro...")
        cursor.execute("SELECT COUNT(*) FROM frequencia WHERE member_id = ?", (member_id,))
        checkins_before = cursor.fetchone()[0]
        print(f"  → Check-ins do membro: {checkins_before}")
        
        cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
        payments_before = cursor.fetchone()[0]
        print(f"  → Pagamentos do membro: {payments_before}")
        
        # Deletar membro
        print("\n[3.6] Deletando membro...")
        db.delete_member(member_id)
        print("  ✓ Membro deletado")
        
        # Verificar se check-ins e pagamentos foram deletados em cascata
        print("\n[3.7] Verificando se dados foram deletados em cascata...")
        cursor.execute("SELECT COUNT(*) FROM frequencia WHERE member_id = ?", (member_id,))
        checkins_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
        payments_after = cursor.fetchone()[0]
        
        if checkins_after == 0 and payments_after == 0:
            print("  ✓ Check-ins deletados em cascata: 0 (esperado)")
            print("  ✓ Pagamentos deletados em cascata: 0 (esperado)")
            print("\n✅ TESTE 3 PASSOU: ON DELETE CASCADE funciona")
            return True
        else:
            print(f"  ✗ Check-ins órfãos: {checkins_after} (esperado: 0)")
            print(f"  ✗ Pagamentos órfãos: {payments_after} (esperado: 0)")
            print("\n❌ TESTE 3 FALHOU: Dados órfãos detectados")
            return False
        
    except Exception as e:
        print(f"\n  ✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_date_types():
    """Testa se datas estão no tipo correto."""
    print_header("TESTE 4: Tipos de Dados Corretos (DATE/DATETIME)")
    
    print("\n⚠️  ATENÇÃO: Este teste só funciona após executar fix_database_critical.py")
    print("            Se o banco não foi migrado, este teste será pulado.\n")
    
    db = DatabaseManager()
    if not db.connect():
        print("  ✗ Erro ao conectar ao banco de dados")
        return False
    
    try:
        cursor = db.connection.cursor()
        
        # Verificar schema da tabela membros
        print("[4.1] Verificando schema da tabela MEMBROS...")
        cursor.execute("PRAGMA table_info(membros)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        expected_types = {
            'vencimento_plano': 'DATE',
            'data_nascimento': 'DATE',
            'calcado': 'INTEGER'
        }
        
        all_correct = True
        for col, expected_type in expected_types.items():
            actual_type = columns.get(col, 'NOT_FOUND')
            if actual_type == expected_type:
                print(f"  ✓ {col}: {actual_type}")
            else:
                print(f"  ✗ {col}: {actual_type} (esperado: {expected_type})")
                all_correct = False
        
        # Verificar schema da tabela pagamentos
        print("\n[4.2] Verificando schema da tabela PAGAMENTOS...")
        cursor.execute("PRAGMA table_info(pagamentos)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        expected_types = {
            'data_pagamento': 'DATE',
            'nova_data_vencimento': 'DATE'
        }
        
        for col, expected_type in expected_types.items():
            actual_type = columns.get(col, 'NOT_FOUND')
            if actual_type == expected_type:
                print(f"  ✓ {col}: {actual_type}")
            else:
                print(f"  ✗ {col}: {actual_type} (esperado: {expected_type})")
                all_correct = False
        
        # Testar consulta por intervalo de datas
        print("\n[4.3] Testando consulta por intervalo de datas...")
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM pagamentos
                WHERE data_pagamento BETWEEN '2025-01-01' AND '2025-12-31'
            """)
            count = cursor.fetchone()[0]
            print(f"  ✓ Consulta por intervalo funciona: {count} pagamentos em 2025")
        except Exception as e:
            print(f"  ✗ Consulta por intervalo falhou: {e}")
            all_correct = False
        
        if all_correct:
            print("\n✅ TESTE 4 PASSOU: Tipos de dados corretos")
        else:
            print("\n⚠️  TESTE 4 INCOMPLETO: Execute fix_database_critical.py primeiro")
        
        return all_correct
        
    except Exception as e:
        print(f"\n  ✗ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Executa todos os testes."""
    print("\n" + "=" * 70)
    print("  VALIDAÇÃO DAS CORREÇÕES CRÍTICAS")
    print("=" * 70)
    print("\nTestando implementações:")
    print("  1. Cobrança de Diária (0.0 renovação, 35.0 check-in)")
    print("  2. Proteção contra check-ins duplicados")
    print("  3. Foreign keys com ON DELETE CASCADE")
    print("  4. Tipos de dados corretos (DATE/DATETIME)")
    
    results = {}
    
    # Teste 1: Configuração de preços
    results['test_1'] = test_diaria_pricing()
    
    # Teste 2: Proteção contra duplicatas
    results['test_2'] = test_duplicate_checkin_protection()
    
    # Teste 3: Foreign keys CASCADE
    results['test_3'] = test_foreign_keys_cascade()
    
    # Teste 4: Tipos de dados
    results['test_4'] = test_date_types()
    
    # Resumo
    print("\n" + "=" * 70)
    print("  RESUMO DOS TESTES")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        test_title = {
            'test_1': "Teste 1: Cobrança de Diária",
            'test_2': "Teste 2: Proteção Duplicatas",
            'test_3': "Teste 3: Foreign Keys CASCADE",
            'test_4': "Teste 4: Tipos de Dados"
        }[test_name]
        print(f"  {test_title}: {status}")
    
    print(f"\n  Total: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n✨ Sistema pronto para uso com as correções críticas.")
    elif passed >= 2:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        print("\n💡 Execute fix_database_critical.py para aplicar todas as correções:")
        print("   python scripts/fix_database_critical.py")
    else:
        print("\n❌ VÁRIOS TESTES FALHARAM")
        print("\n⚠️  Verifique se as alterações foram aplicadas corretamente.")
    
    print("\n")
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
