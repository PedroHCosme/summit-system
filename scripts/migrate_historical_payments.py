"""Script para migrar dados históricos de pagamentos.

Este script realiza duas migrações:

1. PAGAMENTOS DE PLANOS COM VENCIMENTO (Mensal, Trimestral, Semestral, Anual):
   - Cria 1 pagamento histórico baseado na data de vencimento
   - Calcula: data_pagamento = vencimento - duração_plano
   
2. PAGAMENTOS DE CHECK-INS HISTÓRICOS (Diária, Gympass, Totalpass):
   - Para cada check-in na tabela frequencia SEM pagamento associado
   - Cria pagamento com data = data do check-in
   - Valor baseado no tipo de plano do membro
"""

import sys
import os
from datetime import datetime, timedelta

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.database_manager import DatabaseManager
from src.config import (
    PLANOS_COM_VENCIMENTO,
    PLANOS_PRECOS,
    PLANOS_PAGAMENTO_POR_CHECKIN,
)

# Mapa de dias por tipo de plano
PLANO_DURACAO_DIAS = {
    'Mensal': 30,
    'Mens. c/ Treino': 30,
    'Trimestral': 90,
    'Semestral': 180,
    'Anual': 365,
}

# Planos que geram pagamento por check-in
PLANOS_POR_CHECKIN = list(PLANOS_PAGAMENTO_POR_CHECKIN.keys())
# Suporte extra para planos derivados
if 'Diária Boulder' not in PLANOS_POR_CHECKIN:
    PLANOS_POR_CHECKIN.append('Diária Boulder')


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
        vencimento_str = member.get('vencimento_plano', '')
        estado_plano = member.get('estado_plano', '')
        
        # Pular membros sem plano definido ou com planos que não geram receita
        if not plano or plano not in PLANOS_COM_VENCIMENTO:
            continue
        
        # Pular membros INATIVOS (não faz sentido criar pagamento histórico)
        if estado_plano != 'ATIVO':
            continue
        
        # Pular se não tem data de vencimento
        if not vencimento_str:
            print(f"  ⚠️  Pulando {nome} - sem data de vencimento")
            continue
        
        # Parse da data de vencimento
        vencimento_dt = None
        try:
            # Tentar diferentes formatos de data
            for fmt in ['%d/%m/%Y', '%d/%m/%y', '%Y-%m-%d', '%d-%m-%Y', '%d-%m-%y']:
                try:
                    vencimento_dt = datetime.strptime(vencimento_str, fmt)
                    break
                except ValueError:
                    continue
            
            if vencimento_dt is None:
                print(f"  ⚠️  Pulando {nome} - data de vencimento inválida: {vencimento_str}")
                continue
                
        except Exception as e:
            print(f"  ⚠️  Erro ao processar data de vencimento de {nome}: {e}")
            continue
        
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
        
        # Calcular data do último pagamento baseado no vencimento
        duracao_dias = PLANO_DURACAO_DIAS.get(plano)
        
        if duracao_dias is None:
            print(f"  ⚠️  Pulando {nome} - duração do plano '{plano}' não mapeada")
            continue
        
        # Data do pagamento = vencimento - duração do plano
        data_pagamento = vencimento_dt - timedelta(days=duracao_dias)
        
        # Garantir que não seja no futuro
        hoje = datetime.now()
        if data_pagamento > hoje:
            # Se o pagamento calculado for no futuro, usar uma data passada razoável
            data_pagamento = hoje - timedelta(days=duracao_dias // 2)
        
        # Determinar tipo de transação baseado no plano
        tipo_transacao = plano
        
        # Criar registro de pagamento
        try:
            db.add_payment(
                member_id=member_id,
                data_pagamento=data_pagamento,
                tipo_transacao=tipo_transacao,
                descricao=f"Pagamento histórico - {plano}",
                valor=valor,
                metodo_pagamento="Migração",  # Indica que é dados migrados
                nova_data_vencimento=vencimento_dt.strftime('%Y-%m-%d')
            )
            
            pagamentos_criados += 1
            membros_processados += 1
            
            dias_atras = (hoje - data_pagamento).days
            print(f"  ✓ {nome} - {plano} - R$ {valor:.2f} (pago há {dias_atras} dias, em {data_pagamento.strftime('%d/%m/%Y')})")
            
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
    
    print("\n✅ Migração de planos com vencimento concluída!")
    db.close()


def migrate_checkin_payments():
    """Migra pagamentos históricos de check-ins (Diária, Gympass, Totalpass)."""
    
    db = DatabaseManager()
    
    if not db.connect():
        print("❌ Erro ao conectar ao banco de dados!")
        return
    
    print("\n" + "=" * 70)
    print("=== Migração de Pagamentos de Check-ins Históricos ===")
    print("=" * 70)
    print()
    
    if not db.connection:
        print("❌ Erro: banco não conectado!")
        return
    
    cursor = db.connection.cursor()
    
    # Buscar todos os check-ins que NÃO têm pagamento associado
    # Estratégia: LEFT JOIN pagamentos onde data_pagamento = checkin_datetime
    placeholders = ', '.join(['?'] * len(PLANOS_POR_CHECKIN))
    query = f"""
        SELECT 
            f.id as checkin_id,
            f.member_id,
            f.checkin_datetime,
            m.nome,
            m.plano
        FROM frequencia f
        JOIN membros m ON f.member_id = m.id
        LEFT JOIN pagamentos p ON (
            p.member_id = f.member_id 
            AND DATE(p.data_pagamento) = DATE(f.checkin_datetime)
            AND p.tipo_transacao = m.plano
        )
        WHERE p.id IS NULL
        AND m.plano IN ({placeholders})
        ORDER BY f.checkin_datetime
    """
    
    cursor.execute(query, PLANOS_POR_CHECKIN)
    checkins_sem_pagamento = cursor.fetchall()
    
    print(f"📊 Total de check-ins sem pagamento: {len(checkins_sem_pagamento)}")
    print()
    
    if len(checkins_sem_pagamento) == 0:
        print("✅ Todos os check-ins já têm pagamentos associados!")
        return
    
    pagamentos_criados = 0
    erros = 0
    
    # Agrupar por plano para mostrar progresso
    by_plano = {}
    for row in checkins_sem_pagamento:
        plano = row[4]
        by_plano[plano] = by_plano.get(plano, 0) + 1
    
    print("📋 Check-ins a processar por plano:")
    for plano, count in sorted(by_plano.items()):
        print(f"   • {plano}: {count} check-ins")
    print()
    
    print("🔄 Criando pagamentos...")
    print()
    
    for row in checkins_sem_pagamento:
        checkin_id, member_id, checkin_datetime_str, nome, plano = row
        
        # Parse da data do check-in
        try:
            # Tentar formatos
            checkin_dt = None
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y']:
                try:
                    checkin_dt = datetime.strptime(checkin_datetime_str, fmt)
                    break
                except ValueError:
                    continue
            
            if checkin_dt is None:
                erros += 1
                print(f"  ⚠️  Erro: data inválida '{checkin_datetime_str}' para {nome}")
                continue
            
            # Obter valor do check-in
            valor = PLANOS_PAGAMENTO_POR_CHECKIN.get(plano)
            
            # Planos derivados (ex: Diária Boulder) usam valor da diária
            if valor is None and 'Diária' in plano:
                valor = PLANOS_PAGAMENTO_POR_CHECKIN.get('Diária')
            
            if valor is None or valor <= 0:
                erros += 1
                print(f"  ⚠️  Erro: plano '{plano}' sem valor definido para check-in")
                continue
            
            # Criar pagamento
            db.add_payment(
                member_id=member_id,
                data_pagamento=checkin_dt,
                tipo_transacao=plano,
                descricao=f"Check-in histórico - {plano}",
                valor=valor,
                metodo_pagamento="Migração Check-in",
                nova_data_vencimento=None
            )
            
            pagamentos_criados += 1
            
            # Mostrar progresso a cada 100 pagamentos
            if pagamentos_criados % 100 == 0:
                print(f"   ✓ {pagamentos_criados} pagamentos criados...")
        
        except Exception as e:
            erros += 1
            print(f"  ✗ Erro ao criar pagamento para check-in {checkin_id}: {e}")
    
    print()
    print("=" * 70)
    print("📊 RESUMO DA MIGRAÇÃO DE CHECK-INS")
    print("=" * 70)
    print(f"✅ Pagamentos criados: {pagamentos_criados}")
    if erros > 0:
        print(f"⚠️  Erros: {erros}")
    print()
    
    # Resumo financeiro atualizado
    print("=== Resumo Financeiro Total (Após Migração) ===")
    summary = db.get_financial_summary()
    print(f"Receita Total: R$ {summary['total_receita']:,.2f}")
    print(f"Total de Transações: {summary['total_transacoes']}")
    print(f"Ticket Médio: R$ {summary['ticket_medio']:,.2f}")
    
    print()
    print("=== Receita por Tipo de Plano ===")
    breakdown = db.get_revenue_breakdown()
    for item in breakdown:
        tipo = item['tipo_transacao']
        quantidade = item['quantidade']
        total = item['total_valor']
        print(f"{tipo}: {quantidade} pagamento(s) - R$ {total:,.2f}")
    
    print()
    print("✅ Migração de check-ins concluída!")
    
    db.close()


if __name__ == "__main__":
    # Executar ambas as migrações
    print("=" * 70)
    print("MIGRAÇÃO COMPLETA DE PAGAMENTOS HISTÓRICOS")
    print("=" * 70)
    print()
    print("Este script executará duas migrações:")
    print("  1. Pagamentos de planos com vencimento")
    print("  2. Pagamentos de check-ins históricos")
    print()
    
    resposta = input("Deseja continuar? (s/N): ").strip().lower()
    if resposta not in ['s', 'sim', 'y', 'yes']:
        print("❌ Migração cancelada.")
        exit(0)
    
    print()
    
    # Parte 1: Planos com vencimento
    migrate_historical_payments()
    
    # Parte 2: Check-ins históricos
    migrate_checkin_payments()
