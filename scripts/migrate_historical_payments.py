"""Script para migrar dados históricos de pagamentos."""

import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.config import PLANOS_COM_VENCIMENTO, PLANOS_PRECOS


def migrate_historical_payments():
    """Migra pagamentos históricos com base nos membros existentes."""
    
    db = DatabaseManager()
    
    # Conectar ao banco de dados
    if not db.connect():
        print("❌ Erro ao conectar ao banco de dados!")
        return
    
    print("=== Migração de Pagamentos Históricos ===\n")
    
    # Obter todos os membros
    all_members = db.get_all_members()
    print(f"Total de membros encontrados: {len(all_members)}\n")
    
    pagamentos_criados = 0
    membros_processados = 0
    
    for member in all_members:
        member_id = member['id']
        nome = member['nome']
        plano = member.get('plano', '')
        created_at_str = member.get('created_at')
        
        # Pular membros sem plano definido ou com planos que não geram receita
        if not plano or plano not in PLANOS_COM_VENCIMENTO:
            continue
        
        # Pegar data de criação (created_at)
        if created_at_str:
            try:
                # Tentar diferentes formatos de data
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        data_cadastro = datetime.strptime(created_at_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    # Se nenhum formato funcionou, usar data atual
                    data_cadastro = datetime.now()
            except Exception as e:
                print(f"  ⚠️  Erro ao processar data de {nome}: {e}")
                data_cadastro = datetime.now()
        else:
            data_cadastro = datetime.now()
        
        # Verificar se já existe um pagamento para este membro
        existing_payments = db.get_member_payment_history(member_id)
        
        if existing_payments:
            print(f"  ⏭️  Pulando {nome} - já possui {len(existing_payments)} pagamento(s)")
            continue
        
        # Obter valor do plano
        valor = PLANOS_PRECOS.get(plano, 0.0)
        
        if valor <= 0:
            print(f"  ⚠️  Plano '{plano}' de {nome} não tem valor definido")
            continue
        
        # Determinar tipo de transação baseado no plano
        tipo_transacao = plano
        
        # Calcular data de vencimento (se aplicável)
        data_vencimento_str = member.get('data_vencimento')
        nova_data_vencimento = None
        
        if data_vencimento_str:
            try:
                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y']:
                    try:
                        nova_data_vencimento = datetime.strptime(data_vencimento_str, fmt)
                        break
                    except ValueError:
                        continue
            except:
                pass
        
        # Criar registro de pagamento
        try:
            db.add_payment(
                member_id=member_id,
                data_pagamento=data_cadastro,
                tipo_transacao=tipo_transacao,
                descricao=f"Pagamento inicial - {plano}",
                valor=valor,
                metodo_pagamento="N/A",  # Método desconhecido para dados migrados
                nova_data_vencimento=nova_data_vencimento.isoformat() if nova_data_vencimento else None
            )
            
            pagamentos_criados += 1
            membros_processados += 1
            print(f"  ✓ {nome} - {plano} - R$ {valor:.2f} (cadastro: {data_cadastro.strftime('%d/%m/%Y')})")
            
        except Exception as e:
            print(f"  ✗ Erro ao criar pagamento para {nome}: {e}")
    
    print(f"\n=== Resumo da Migração ===")
    print(f"Membros processados: {membros_processados}")
    print(f"Pagamentos criados: {pagamentos_criados}")
    
    # Mostrar resumo financeiro
    print("\n=== Resumo Financeiro Total ===")
    summary = db.get_financial_summary()
    print(f"Receita Total: R$ {summary['total_receita']:,.2f}")
    print(f"Total de Transações: {summary['total_transacoes']}")
    print(f"Ticket Médio: R$ {summary['ticket_medio']:,.2f}")
    
    # Breakdown por tipo
    print("\n=== Receita por Tipo de Plano ===")
    breakdown = db.get_revenue_breakdown()
    for item in breakdown:
        tipo = item['tipo_transacao']
        quantidade = item['quantidade']
        total = item['total_valor']
        print(f"{tipo}: {quantidade} pagamento(s) - R$ {total:,.2f}")
    
    print("\n✅ Migração concluída com sucesso!")


if __name__ == "__main__":
    migrate_historical_payments()
