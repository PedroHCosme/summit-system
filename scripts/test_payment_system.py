"""Script de teste para verificar o registro automático de pagamentos."""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager


def test_payment_registration():
    """Testa o registro automático de pagamentos."""
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Erro ao conectar ao banco de dados!")
        return
    
    print("=== Teste de Registro Automático de Pagamentos ===\n")
    
    # Buscar um membro de teste
    all_members = db.get_all_members()
    if not all_members:
        print("❌ Nenhum membro encontrado no banco!")
        return
    
    # Pegar o primeiro membro
    test_member = all_members[0]
    member_id = test_member['id']
    nome = test_member['nome']
    plano_atual = test_member.get('plano', 'N/A')
    
    print(f"Membro de teste: {nome}")
    print(f"Plano atual: {plano_atual}")
    print(f"ID: {member_id}\n")
    
    # Verificar pagamentos atuais
    payment_history = db.get_member_payment_history(member_id)
    print(f"Pagamentos existentes: {len(payment_history)}\n")
    
    if payment_history:
        print("Últimos 3 pagamentos:")
        for payment in payment_history[:3]:
            data = payment['data_pagamento']
            tipo = payment['tipo_transacao']
            valor = payment['valor']
            print(f"  • {data} - {tipo} - R$ {valor:.2f}")
        print()
    
    # Simular uma mudança de plano
    print("=" * 50)
    print("SIMULAÇÃO: Mudança de plano de 'Mensal' para 'Trimestral'")
    print("=" * 50)
    
    updated_data = {
        'id': member_id,
        'plano': 'Trimestral',
        'vencimento_plano': '15/01/2026'
    }
    
    print("\nDados para atualização:")
    print(f"  • Novo plano: Trimestral")
    print(f"  • Nova data de vencimento: 15/01/2026")
    print(f"  • Método de pagamento: PIX")
    print()
    
    # Executar atualização COM registro de pagamento
    success = db.update_member_from_dict(
        updated_data,
        register_payment=True,
        metodo_pagamento="PIX"
    )
    
    if success:
        print("✅ Membro atualizado com sucesso!")
        
        # Verificar se o pagamento foi criado
        new_payment_history = db.get_member_payment_history(member_id)
        new_payments_count = len(new_payment_history)
        
        print(f"\nPagamentos após atualização: {new_payments_count}")
        
        if new_payments_count > len(payment_history):
            print("\n🎉 NOVO PAGAMENTO REGISTRADO AUTOMATICAMENTE!")
            latest_payment = new_payment_history[0]
            print(f"\nDetalhes do pagamento:")
            print(f"  • Data: {latest_payment['data_pagamento']}")
            print(f"  • Tipo: {latest_payment['tipo_transacao']}")
            print(f"  • Descrição: {latest_payment.get('descricao', 'N/A')}")
            print(f"  • Valor: R$ {latest_payment['valor']:.2f}")
            print(f"  • Método: {latest_payment.get('metodo_pagamento', 'N/A')}")
        else:
            print("\n⚠️  Nenhum pagamento novo foi criado (plano pode não ter mudado)")
    else:
        print("❌ Erro ao atualizar membro!")
    
    # Reverter mudança para não afetar dados reais
    print("\n" + "=" * 50)
    print("Revertendo mudanças para não afetar dados reais...")
    print("=" * 50)
    
    revert_data = {
        'id': member_id,
        'plano': plano_atual,
        'vencimento_plano': test_member.get('vencimento_plano', '')
    }
    
    db.update_member_from_dict(revert_data, register_payment=False)
    print("✅ Dados revertidos!\n")
    
    # Mostrar resumo financeiro
    print("=" * 50)
    print("RESUMO FINANCEIRO ATUAL")
    print("=" * 50)
    
    summary = db.get_financial_summary()
    print(f"\nReceita Total: R$ {summary['total_receita']:,.2f}")
    print(f"Total de Transações: {summary['total_transacoes']}")
    print(f"Ticket Médio: R$ {summary['ticket_medio']:,.2f}")
    
    print("\n✅ Teste concluído!")
    
    db.close()


if __name__ == "__main__":
    test_payment_registration()
