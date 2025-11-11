"""
Exemplos de uso da API de transações do DatabaseManager.

Este módulo demonstra como usar transações contextuais para garantir
atomicidade nas operações do banco de dados.
"""

from datetime import datetime
from src.data.database_manager import DatabaseManager


def exemplo_basico():
    """Exemplo básico de uso de transação."""
    db = DatabaseManager()
    db.connect()
    
    try:
        with db.transaction():
            # Todas as operações dentro deste bloco são atômicas
            member_data = {
                'nome': 'João Silva',
                'plano': 'Mensal',
                'whatsapp': '11999999999',
                'genero': 'M'
            }
            member_id = db.add_member(member_data)
            
            if member_id:
                # Adiciona check-in para o mesmo membro
                db.add_checkin(member_id, datetime.now())
                print(f"✓ Membro {member_id} e check-in criados com sucesso")
            else:
                raise Exception("Falha ao criar membro")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("Todas as operações foram revertidas")
    finally:
        db.close()


def exemplo_multiplos_membros():
    """Insere múltiplos membros em uma única transação."""
    db = DatabaseManager()
    db.connect()
    
    novos_membros = [
        {'nome': 'Maria Santos', 'plano': 'Trimestral', 'genero': 'F'},
        {'nome': 'Pedro Costa', 'plano': 'Mensal', 'genero': 'M'},
        {'nome': 'Ana Paula', 'plano': 'Semestral', 'genero': 'F'},
    ]
    
    try:
        with db.transaction():
            ids_criados = []
            for membro in novos_membros:
                member_id = db.add_member(membro)
                ids_criados.append(member_id)
                print(f"  → Criado: {membro['nome']} (ID: {member_id})")
            
            print(f"✓ {len(ids_criados)} membros criados com sucesso")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("Nenhum membro foi criado (rollback)")
    finally:
        db.close()


def exemplo_com_validacao():
    """Exemplo com validação personalizada."""
    db = DatabaseManager()
    db.connect()
    
    member_data = {
        'nome': 'Carlos Oliveira',
        'plano': 'Anual',
        'whatsapp': '11888888888'
    }
    
    try:
        with db.transaction():
            # Validação customizada
            if not member_data.get('nome'):
                raise ValueError("Nome é obrigatório")
            
            if len(member_data.get('whatsapp', '')) < 10:
                raise ValueError("WhatsApp inválido")
            
            # Se passou nas validações, insere
            member_id = db.add_member(member_data)
            print(f"✓ Membro {member_id} criado com sucesso")
            
    except ValueError as e:
        print(f"❌ Validação falhou: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
    finally:
        db.close()


def exemplo_aninhado_evitar():
    """
    ATENÇÃO: Este é um anti-padrão!
    
    Transações aninhadas NÃO são suportadas nativamente pelo SQLite.
    Use transações únicas e amplas quando possível.
    """
    db = DatabaseManager()
    db.connect()
    
    try:
        with db.transaction():
            member_id = db.add_member({'nome': 'Teste 1', 'plano': 'Mensal'})
            
            if member_id:
                # ❌ EVITE: transação dentro de transação
                # with db.transaction():  # Isso causaria problemas!
                #     db.add_checkin(member_id, datetime.now())
                
                # ✅ CORRETO: tudo na mesma transação
                db.add_checkin(member_id, datetime.now())
            
    finally:
        db.close()


def exemplo_migracao_batch():
    """Simula uma mini-migração com transação."""
    db = DatabaseManager()
    db.connect()
    
    # Dados simulados do Sheets
    dados_sheets = [
        {'nome': 'Membro 1', 'plano': 'Mensal', 'checkins': 5},
        {'nome': 'Membro 2', 'plano': 'Trimestral', 'checkins': 12},
        {'nome': 'Membro 3', 'plano': 'Semestral', 'checkins': 28},
    ]
    
    total_membros = 0
    total_checkins = 0
    
    try:
        with db.transaction():
            for dados in dados_sheets:
                # Insere membro
                member_data = {
                    'nome': dados['nome'],
                    'plano': dados['plano']
                }
                member_id = db.add_member(member_data)
                
                if member_id:
                    total_membros += 1
                    
                    # Insere check-ins simulados
                    for i in range(dados['checkins']):
                        db.add_checkin(member_id, datetime.now())
                        total_checkins += 1
            
            print(f"✓ Migração bem-sucedida:")
            print(f"  • {total_membros} membros")
            print(f"  • {total_checkins} check-ins")
            
    except Exception as e:
        print(f"❌ Migração falhou: {e}")
        print("Todos os dados foram revertidos")
    finally:
        db.close()


def exemplo_rollback_intencional():
    """Demonstra como forçar um rollback."""
    db = DatabaseManager()
    db.connect()
    
    try:
        with db.transaction():
            member_id = db.add_member({'nome': 'Teste Rollback', 'plano': 'Mensal'})
            print(f"Membro temporário criado: {member_id}")
            
            # Simula uma condição que requer rollback
            condicao_erro = True
            if condicao_erro:
                raise Exception("Condição de erro detectada - revertendo!")
            
            # Este ponto nunca será alcançado
            print("Esta linha não será executada")
            
    except Exception as e:
        print(f"❌ {e}")
        print("Membro temporário foi removido (rollback)")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("EXEMPLOS DE USO: API de Transações")
    print("=" * 60)
    
    print("\n1. Exemplo Básico:")
    print("-" * 60)
    exemplo_basico()
    
    print("\n2. Múltiplos Membros:")
    print("-" * 60)
    exemplo_multiplos_membros()
    
    print("\n3. Com Validação:")
    print("-" * 60)
    exemplo_com_validacao()
    
    print("\n4. Migração em Batch:")
    print("-" * 60)
    exemplo_migracao_batch()
    
    print("\n5. Rollback Intencional:")
    print("-" * 60)
    exemplo_rollback_intencional()
    
    print("\n" + "=" * 60)
