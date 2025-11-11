#!/usr/bin/env python3
"""
Script para testar a integração financeira completa.
Valida registro de pagamentos em check-ins e renovações.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Agora podemos importar
from src.data.database_manager import DatabaseManager
from src.config import PLANOS_PRECOS, PLANOS_PAGAMENTO_POR_CHECKIN


def test_financial_integration():
    """Testa a integração financeira completa."""
    
    print("="*70)
    print("TESTE DE INTEGRAÇÃO FINANCEIRA")
    print("="*70)
    
    db = DatabaseManager()
    db.connect()
    
    cursor = db.connection.cursor()
    
    # Criar membro de teste
    print("\n1. Criando membro de teste...")
    member_data = {
        'nome': 'Teste Financeiro',
        'plano': 'Mensal',
        'vencimento_plano': '15/11/2025',
        'estado_plano': 'ATIVO',
        'genero': 'Masculino'
    }
    
    member_id = db.add_member(member_data)
    print(f"   ✓ Membro criado: ID {member_id}")
    
    # Contar pagamentos antes
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_before = cursor.fetchone()[0]
    print(f"   Pagamentos iniciais: {payments_before}")
    
    print("\n2. Testando RENOVAÇÃO de plano...")
    print("   Renovando plano Mensal (R$ 190,00)...")
    
    success = db.update_member_from_dict(
        {
            'id': member_id,
            'plano': 'Mensal',
            'vencimento_plano': '15/12/2025'
        },
        register_payment=True,
        metodo_pagamento="PIX"
    )
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_after_renewal = cursor.fetchone()[0]
    
    if payments_after_renewal > payments_before:
        print(f"   ✓ Pagamento de renovação registrado!")
        cursor.execute("""
            SELECT tipo_transacao, valor, metodo_pagamento 
            FROM pagamentos 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        last_payment = cursor.fetchone()
        print(f"     Tipo: {last_payment[0]}")
        print(f"     Valor: R$ {last_payment[1]:.2f}")
        print(f"     Método: {last_payment[2]}")
    else:
        print("   ✗ ERRO: Pagamento de renovação NÃO foi registrado!")
    
    print("\n3. Testando MUDANÇA de plano...")
    print("   Mudando de Mensal para Trimestral (R$ 500,00)...")
    
    payments_before_change = payments_after_renewal
    
    success = db.update_member_from_dict(
        {
            'id': member_id,
            'plano': 'Trimestral',
            'vencimento_plano': '15/01/2026'
        },
        register_payment=True,
        metodo_pagamento="Cartão"
    )
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_after_change = cursor.fetchone()[0]
    
    if payments_after_change > payments_before_change:
        print(f"   ✓ Pagamento de mudança de plano registrado!")
        cursor.execute("""
            SELECT tipo_transacao, descricao, valor, metodo_pagamento 
            FROM pagamentos 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        last_payment = cursor.fetchone()
        print(f"     Tipo: {last_payment[0]}")
        print(f"     Descrição: {last_payment[1]}")
        print(f"     Valor: R$ {last_payment[2]:.2f}")
        print(f"     Método: {last_payment[3]}")
    else:
        print("   ✗ ERRO: Pagamento de mudança NÃO foi registrado!")
    
    print("\n4. Testando CHECK-IN com Diária...")
    
    # Mudar para Diária
    db.update_member_from_dict(
        {
            'id': member_id,
            'plano': 'Diária',
            'estado_plano': 'ATIVO'
        },
        register_payment=False
    )
    
    payments_before_checkin = payments_after_change
    
    # Fazer check-in
    checkin_time = datetime.now()
    checkin_id = db.add_checkin(member_id, checkin_time)
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_after_checkin = cursor.fetchone()[0]
    
    if payments_after_checkin > payments_before_checkin:
        print(f"   ✓ Pagamento de Diária registrado no check-in!")
        cursor.execute("""
            SELECT tipo_transacao, valor 
            FROM pagamentos 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        last_payment = cursor.fetchone()
        print(f"     Tipo: {last_payment[0]}")
        print(f"     Valor: R$ {last_payment[1]:.2f}")
        
        expected_value = PLANOS_PAGAMENTO_POR_CHECKIN.get('Diária', 0)
        if last_payment[1] == expected_value:
            print(f"     ✓ Valor correto (R$ {expected_value:.2f})")
        else:
            print(f"     ✗ ERRO: Valor incorreto! Esperado R$ {expected_value:.2f}")
    else:
        print("   ✗ ERRO: Pagamento de Diária NÃO foi registrado!")
    
    print("\n5. Testando CHECK-IN com Gympass...")
    
    # Mudar para Gympass
    db.update_member_from_dict(
        {
            'id': member_id,
            'plano': 'Gympass',
            'estado_plano': 'ATIVO'
        },
        register_payment=False
    )
    
    payments_before_gympass = payments_after_checkin
    
    # Fazer check-in
    checkin_id = db.add_checkin(member_id, datetime.now())
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_after_gympass = cursor.fetchone()[0]
    
    if payments_after_gympass > payments_before_gympass:
        print(f"   ✓ Pagamento de Gympass registrado no check-in!")
        cursor.execute("""
            SELECT tipo_transacao, valor 
            FROM pagamentos 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        last_payment = cursor.fetchone()
        print(f"     Tipo: {last_payment[0]}")
        print(f"     Valor: R$ {last_payment[1]:.2f}")
        
        expected_value = PLANOS_PAGAMENTO_POR_CHECKIN.get('Gympass', 0)
        if last_payment[1] == expected_value:
            print(f"     ✓ Valor correto (R$ {expected_value:.2f})")
        else:
            print(f"     ✗ ERRO: Valor incorreto! Esperado R$ {expected_value:.2f}")
    else:
        print("   ✗ ERRO: Pagamento de Gympass NÃO foi registrado!")
    
    print("\n6. Testando CHECK-IN com Totalpass...")
    
    # Mudar para Totalpass
    db.update_member_from_dict(
        {
            'id': member_id,
            'plano': 'Totalpass',
            'estado_plano': 'ATIVO'
        },
        register_payment=False
    )
    
    payments_before_totalpass = payments_after_gympass
    
    # Fazer check-in
    checkin_id = db.add_checkin(member_id, datetime.now())
    
    cursor.execute("SELECT COUNT(*) FROM pagamentos WHERE member_id = ?", (member_id,))
    payments_after_totalpass = cursor.fetchone()[0]
    
    if payments_after_totalpass > payments_before_totalpass:
        print(f"   ✓ Pagamento de Totalpass registrado no check-in!")
        cursor.execute("""
            SELECT tipo_transacao, valor 
            FROM pagamentos 
            WHERE member_id = ? 
            ORDER BY id DESC LIMIT 1
        """, (member_id,))
        last_payment = cursor.fetchone()
        print(f"     Tipo: {last_payment[0]}")
        print(f"     Valor: R$ {last_payment[1]:.2f}")
        
        expected_value = PLANOS_PAGAMENTO_POR_CHECKIN.get('Totalpass', 0)
        if last_payment[1] == expected_value:
            print(f"     ✓ Valor correto (R$ {expected_value:.2f})")
        else:
            print(f"     ✗ ERRO: Valor incorreto! Esperado R$ {expected_value:.2f}")
    else:
        print("   ✗ ERRO: Pagamento de Totalpass NÃO foi registrado!")
    
    print("\n7. Resumo final dos pagamentos...")
    cursor.execute("""
        SELECT tipo_transacao, descricao, valor, metodo_pagamento, data_pagamento
        FROM pagamentos 
        WHERE member_id = ? 
        ORDER BY data_pagamento
    """, (member_id,))
    
    all_payments = cursor.fetchall()
    total_receita = 0
    
    print(f"\n   Total de {len(all_payments)} pagamentos registrados:")
    print("   " + "-"*66)
    for i, payment in enumerate(all_payments, 1):
        tipo, desc, valor, metodo, data = payment
        total_receita += valor
        print(f"   {i}. {tipo:20s} | R$ {valor:7.2f} | {metodo or 'N/A':10s}")
        if desc:
            print(f"      → {desc}")
    
    print("   " + "-"*66)
    print(f"   RECEITA TOTAL: R$ {total_receita:.2f}")
    
    # Limpar teste
    print("\n8. Limpando dados de teste...")
    cursor.execute("DELETE FROM pagamentos WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM frequencia WHERE member_id = ?", (member_id,))
    cursor.execute("DELETE FROM membros WHERE id = ?", (member_id,))
    db.connection.commit()
    print("   ✓ Dados de teste removidos")
    
    db.close()
    
    print("\n" + "="*70)
    print("TESTE CONCLUÍDO!")
    print("="*70)


if __name__ == "__main__":
    try:
        test_financial_integration()
    except Exception as e:
        print(f"\n✗ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
