"""Script para testar o registro automático de pagamento por check-in."""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.config import PLANOS_PAGAMENTO_POR_CHECKIN


def test_checkin_payment():
    """Testa o registro automático de pagamento ao fazer check-in."""
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Erro ao conectar ao banco de dados!")
        return
    
    print("=" * 60)
    print("TESTE: Pagamento Automático por Check-in")
    print("=" * 60)
    print()
    
    # Buscar membros com planos que geram pagamento por check-in
    all_members = db.get_all_members()
    
    # Filtrar membros por plano
    test_members = {}
    for plano in PLANOS_PAGAMENTO_POR_CHECKIN.keys():
        for member in all_members:
            if member.get('plano') == plano:
                test_members[plano] = member
                break
    
    if not test_members:
        print("❌ Nenhum membro encontrado com planos Diária, Gympass ou Totalpass!")
        print("\nPlanos encontrados no banco:")
        planos_unicos = set(m.get('plano', 'N/A') for m in all_members)
        for plano in sorted(planos_unicos):
            count = sum(1 for m in all_members if m.get('plano') == plano)
            print(f"  • {plano}: {count} membros")
        return
    
    print("Membros encontrados para teste:")
    for plano, member in test_members.items():
        print(f"  • {plano}: {member['nome']} (ID: {member['id']})")
    print()
    
    # Testar cada plano
    for plano, member in test_members.items():
        member_id = member['id']
        nome = member['nome']
        valor_esperado = PLANOS_PAGAMENTO_POR_CHECKIN[plano]
        
        print("=" * 60)
        print(f"TESTANDO: {plano}")
        print("=" * 60)
        print(f"Membro: {nome}")
        print(f"Valor esperado por check-in: R$ {valor_esperado:.2f}")
        print()
        
        # Verificar pagamentos antes
        payments_before = db.get_member_payment_history(member_id)
        print(f"Pagamentos antes: {len(payments_before)}")
        
        # Fazer check-in
        print(f"\n🔄 Fazendo check-in...")
        checkin_datetime = datetime.now()
        checkin_id = db.add_checkin(member_id, checkin_datetime)
        
        if checkin_id:
            print(f"✅ Check-in registrado (ID: {checkin_id})")
            
            # Verificar pagamentos depois
            payments_after = db.get_member_payment_history(member_id)
            print(f"Pagamentos depois: {len(payments_after)}")
            
            if len(payments_after) > len(payments_before):
                print("\n🎉 PAGAMENTO REGISTRADO AUTOMATICAMENTE!")
                
                # Mostrar último pagamento
                last_payment = payments_after[0]
                print(f"\nDetalhes do pagamento:")
                print(f"  • Data: {last_payment['data_pagamento']}")
                print(f"  • Tipo: {last_payment['tipo_transacao']}")
                print(f"  • Descrição: {last_payment.get('descricao', 'N/A')}")
                print(f"  • Valor: R$ {last_payment['valor']:.2f}")
                print(f"  • Método: {last_payment.get('metodo_pagamento', 'N/A')}")
                
                # Validar valor
                if last_payment['valor'] == valor_esperado:
                    print(f"\n✅ Valor correto: R$ {valor_esperado:.2f}")
                else:
                    print(f"\n⚠️  Valor incorreto! Esperado: R$ {valor_esperado:.2f}, Recebido: R$ {last_payment['valor']:.2f}")
                
                # Remover o check-in de teste
                print(f"\n🧹 Removendo check-in de teste...")
                db.delete_checkin(checkin_id)
                print("✅ Check-in removido")
                
            else:
                print("\n⚠️  Nenhum pagamento foi registrado!")
        else:
            print("❌ Erro ao registrar check-in!")
        
        print()
    
    # Resumo final
    print("=" * 60)
    print("RESUMO DO TESTE")
    print("=" * 60)
    print()
    print("Configuração de pagamentos por check-in:")
    for plano, valor in PLANOS_PAGAMENTO_POR_CHECKIN.items():
        print(f"  • {plano}: R$ {valor:.2f}")
    
    print("\n✅ Teste concluído!")
    
    db.close()


if __name__ == "__main__":
    test_checkin_payment()
