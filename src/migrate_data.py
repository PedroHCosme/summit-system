"""
Script de migração de dados do Google Sheets para SQLite.
Executa a migração de todos os membros e seus check-ins de frequência.
"""
from datetime import datetime, time
from typing import Dict, List
import sys

from google_sheets_service import GoogleSheetsService
from database_manager import DatabaseManager
from models import Pessoa
from utils import parse_date
from config import (
    SPREADSHEET_ID, 
    CREDENTIALS_PATH,
    COL_NOME,
    COL_PLANO,
    COL_VENCIMENTO_PLANO,
    COL_ESTADO_PLANO,
    COL_DATA_NASCIMENTO,
    COL_WHATSAPP,
    COL_GENERO,
    COL_FREQUENCIA,
    COL_CALCADO
)

# Lista de abas (meses) para migrar
SHEET_NAMES = [
    'Jan/25', 'Fev/25', 'Mar/25', 'Abr/25', 
    'Mai/25', 'Jun/25', 'Jul/25', 'Ago/25', 
    'Set/25', 'Out/25', 'Nov/25', 'Dez/25'  # Adicionei os meses restantes
]

# --- NOVAS CONSTANTES PARA A LÓGICA DE CHECK-IN ---
# A primeira coluna de dados de check-in é a 'E', que tem índice 4.
CHECKIN_DATA_START_COL = 4 
# A última coluna de dados relevantes antes de Gênero (BO) é BN. Índice 65.
CHECKIN_DATA_END_COL = 65
# O cabeçalho com os dias do mês (1, 2, 3...) está na segunda linha da planilha.
DAY_HEADER_ROW_INDEX = 1

def get_safe_value(row: List, col_index: int) -> str:
    """Obtém valor de uma coluna de forma segura."""
    if col_index < len(row) and row[col_index]:
        return str(row[col_index]).strip()
    return ""

def parse_sheet_month_year(sheet_name: str) -> tuple:
    """Extrai mês e ano do nome da aba."""
    month_map = {
        'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4,
        'Mai': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
        'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
    }
    try:
        parts = sheet_name.split('/')
        month_abbr = parts[0]
        year = int('20' + parts[1])
        return month_map[month_abbr], year
    except (IndexError, ValueError, KeyError):
        print(f"  Aviso: Não foi possível parsear o nome da aba '{sheet_name}'. Usando padrão.")
        return 1, 2025

def get_time_from_period(period: str) -> time:
    """Converte a letra do período (M, T, N) para um horário específico."""
    period = period.upper()
    if period == 'T':
        return time(14, 0)  # Tarde
    if period == 'N':
        return time(19, 0)  # Noite
    # M (Manhã) ou qualquer outro valor como padrão
    return time(9, 0)

# A função calculate_checkin_date foi removida pois não é mais necessária.

def migrate_data():
    """Executa a migração completa de dados."""
    
    # ... (seções 1, 2 e 3 do seu código permanecem exatamente iguais) ...
    print("=" * 60)
    print("MIGRAÇÃO DE DADOS: Google Sheets → SQLite")
    print("=" * 60)
    
    # 1. Conectar ao Google Sheets
    print("\n[1/5] Conectando ao Google Sheets...")
    sheets_service = GoogleSheetsService(CREDENTIALS_PATH)
    if not sheets_service.authenticate():
        print("❌ Erro ao autenticar no Google Sheets")
        return False
    print("✓ Conectado ao Google Sheets")
    
    # 2. Conectar ao SQLite
    print("\n[2/5] Conectando ao banco de dados SQLite...")
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("❌ Erro ao conectar ao banco de dados")
        return False
    print("✓ Conectado ao SQLite")
    
    # 3. Criar tabelas
    print("\n[3/5] Recriando tabelas no banco de dados...")
    if not db_manager.recreate_tables():
        print("❌ Erro ao recriar tabelas")
        return False
    print("✓ Tabelas recriadas com sucesso")
    
    # --- LÓGICA DE MIGRAÇÃO REFEITA ---
    print("\n[4/5] Migrando membros e check-ins...")
    membros_migrados: Dict[str, int] = {}  # {nome: member_id}
    total_membros = 0
    total_checkins = 0
    
    # Iterar sobre cada aba (mês)
    for sheet_name in SHEET_NAMES:
        print(f"\n  → Processando aba: {sheet_name}")
        
        # Ler dados da aba
        data = sheets_service.read_spreadsheet(
            SPREADSHEET_ID,
            range_name='A:CZ',
            sheet_name=sheet_name
        )
        
        if not data or len(data) <= DAY_HEADER_ROW_INDEX:
            print(f"    ⚠ Dados insuficientes ou não encontrados na aba {sheet_name}")
            continue
        
        # --- PASSO 1: Construir o mapa de datas para este mês ---
        date_map: Dict[int, datetime.date] = {}
        month, year = parse_sheet_month_year(sheet_name)
        day_header_row = data[DAY_HEADER_ROW_INDEX]

        for col_index in range(CHECKIN_DATA_START_COL, len(day_header_row)):
            day_str = get_safe_value(day_header_row, col_index)
            if day_str.isdigit():
                day = int(day_str)
                try:
                    # Cria a data e a mapeia para o índice da coluna do "check"
                    date_obj = datetime(year, month, day).date()
                    date_map[col_index] = date_obj
                except ValueError:
                    # Dia inválido para o mês (ex: 31 em Fev), ignorar.
                    pass
        
        print(f"    ✓ Mapa de datas criado para {sheet_name}. {len(date_map)} dias mapeados.")
        
        # --- PASSO 2: Iterar sobre as linhas dos membros ---
        # Começa a partir da linha 4 (índice 3), que é onde os nomes dos membros começam.
        for row_index, row in enumerate(data[3:], start=4):
            nome = get_safe_value(row, COL_NOME)
            if not nome or nome.lower() in ['gympass', 'totalpass', 'voucher', 'livre', 'anual', 'trimestral']:
                continue
            
            # Extrair todos os dados da linha atual
            data_nasc_str = get_safe_value(row, COL_DATA_NASCIMENTO)
            data_nasc = parse_date(data_nasc_str)
            
            # Se a data não for válida, imprime um aviso mas não pula o membro
            if not data_nasc and data_nasc_str:
                print(f"    ⓘ Aviso: Data de nascimento '{data_nasc_str}' para o membro '{nome}' (linha {row_index}) é inválida e será ignorada.")
            
            # Se é a primeira vez que vemos este membro
            if nome not in membros_migrados:
                # Cria o objeto Pessoa com todos os dados
                pessoa_obj = Pessoa(
                    nome=nome,
                    data_nascimento=data_nasc,  # Pode ser None
                    plano=get_safe_value(row, COL_PLANO),
                    vencimento_plano=get_safe_value(row, COL_VENCIMENTO_PLANO),
                    estado_plano=get_safe_value(row, COL_ESTADO_PLANO),
                    whatsapp=get_safe_value(row, COL_WHATSAPP),
                    genero=get_safe_value(row, COL_GENERO),
                    frequencia=get_safe_value(row, COL_FREQUENCIA),
                    calcado=get_safe_value(row, COL_CALCADO)
                )
                
                # Adiciona o membro através do objeto
                member_id = db_manager.add_member(pessoa_obj)
                
                if member_id:
                    membros_migrados[nome] = member_id
                    total_membros += 1
                    if total_membros % 20 == 0:
                        print(f"    {total_membros} membros migrados...")
                else:
                    print(f"    ⚠ Erro ao inserir membro {nome} no banco de dados.")
                    continue
            else:
                # Membro já existe - atualizar dados se houver mudanças (mantém apenas valores não-vazios)
                member_id = membros_migrados[nome]
                db_manager.update_member(
                    member_id=member_id,
                    plano=get_safe_value(row, COL_PLANO) or None,
                    frequencia=get_safe_value(row, COL_FREQUENCIA) or None,
                    estado_plano=get_safe_value(row, COL_ESTADO_PLANO) or None,
                    vencimento_plano=get_safe_value(row, COL_VENCIMENTO_PLANO) or None,
                    whatsapp=get_safe_value(row, COL_WHATSAPP) or None,
                    genero=get_safe_value(row, COL_GENERO) or None,
                    calcado=get_safe_value(row, COL_CALCADO) or None
                )

            # --- PASSO 3: Migrar os check-ins usando o mapa de datas ---
            member_id = membros_migrados.get(nome)
            if member_id:
                # Itera sobre as colunas que mapeamos como dias válidos
                for check_col, check_date in date_map.items():
                    check_value = get_safe_value(row, check_col)
                    
                    # Se houver um valor que indique presença
                    if check_value and check_value.upper() not in ['FALSE', 'F']:
                        # A coluna do período é a próxima (índice + 1)
                        period_col = check_col + 1
                        period_value = get_safe_value(row, period_col)
                        
                        check_time = get_time_from_period(period_value)
                        
                        # Combina a data da planilha com a hora do período
                        full_checkin_datetime = datetime.combine(check_date, check_time)
                        
                        db_manager.add_checkin(member_id, full_checkin_datetime)
                        total_checkins += 1
                        
    print(f"\n✓ Migração de membros concluída!")
    print(f"  Total de membros únicos: {total_membros}")
    
    # 5. Resumo final
    print(f"\n[5/5] Resumo de check-ins")
    
    db_manager.close()
    
    print("\n" + "=" * 60)
    print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"\n📊 Resumo:")
    print(f"  • Membros migrados: {len(membros_migrados)}")
    print(f"  • Check-ins migrados: {total_checkins}")
    print(f"  • Banco de dados: gym_database.db")
    print("\n")
    
    return True

if __name__ == "__main__":
    try:
        success = migrate_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro fatal durante a migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)