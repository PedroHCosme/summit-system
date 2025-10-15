"""
Script de migração de dados do Google Sheets para SQLite. (VERSÃO FINAL E CORRIGIDA)
Executa a migração de todos os membros e seus check-ins de frequência,
validando corretamente as linhas de membros e consolidando os dados.
"""
from datetime import datetime, time, date
from typing import Dict, List, Any
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
    'Set/25', 'Out/25', 'Nov/25', 'Dez/25'
]

# --- CONSTANTES PARA A LÓGICA DE CHECK-IN ---
CHECKIN_DATA_START_COL = 4 
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
        return time(14, 0)
    if period == 'N':
        return time(19, 0)
    return time(9, 0)

def migrate_data():
    """Executa a migração completa de dados."""
    
    print("=" * 60)
    print("MIGRAÇÃO DE DADOS: Google Sheets → SQLite (VERSÃO FINAL)")
    print("=" * 60)
    
    # --- ETAPAS 1, 2 e 3: CONEXÕES E SETUP ---
    print("\n[1/6] Conectando ao Google Sheets...")
    sheets_service = GoogleSheetsService(CREDENTIALS_PATH)
    if not sheets_service.authenticate():
        print("❌ Erro ao autenticar no Google Sheets")
        return False
    print("✓ Conectado ao Google Sheets")
    
    print("\n[2/6] Conectando ao banco de dados SQLite...")
    db_manager = DatabaseManager()
    if not db_manager.connect():
        print("❌ Erro ao conectar ao banco de dados")
        return False
    print("✓ Conectado ao SQLite")
    
    print("\n[3/6] Limpando e recriando tabelas...")
    if not db_manager.recreate_tables():
        print("❌ Erro ao recriar tabelas")
        return False
    print("✓ Tabelas recriadas com sucesso")
    
    # --- PASSO 4: CONSOLIDAR DADOS DE MEMBROS EM MEMÓRIA ---
    print("\n[4/6] Lendo e consolidando dados dos membros de todas as abas...")
    consolidated_members: Dict[str, Dict[str, Any]] = {}
    
    for sheet_name in SHEET_NAMES:
        print(f"  → Lendo aba: {sheet_name}")
        data = sheets_service.read_spreadsheet(SPREADSHEET_ID, 'A:CZ', sheet_name)
        if not data or len(data) <= 3:
            print(f"    ⚠ Dados insuficientes na aba {sheet_name}, pulando.")
            continue
        
        for row in data[3:]:
            nome = get_safe_value(row, COL_NOME)
            plano = get_safe_value(row, COL_PLANO)

            if not nome or not plano:
                continue
            
            if nome not in consolidated_members:
                consolidated_members[nome] = {'nome': nome}

            member_data_from_row = {
                'plano': plano,
                'vencimento_plano': get_safe_value(row, COL_VENCIMENTO_PLANO),
                'estado_plano': get_safe_value(row, COL_ESTADO_PLANO),
                'data_nascimento': get_safe_value(row, COL_DATA_NASCIMENTO),
                'whatsapp': get_safe_value(row, COL_WHATSAPP),
                'genero': get_safe_value(row, COL_GENERO),
                'frequencia': get_safe_value(row, COL_FREQUENCIA),
                'calcado': get_safe_value(row, COL_CALCADO),
            }
            
            for key, value in member_data_from_row.items():
                if value:
                    consolidated_members[nome][key] = value

    print(f"✓ {len(consolidated_members)} membros únicos consolidados.")

    # --- PASSO 5: INSERIR MEMBROS CONSOLIDADOS NO BANCO DE DADOS ---
    print("\n[5/6] Inserindo membros consolidados no banco de dados...")
    membros_migrados: Dict[str, int] = {}
    for nome, data_dict in consolidated_members.items():
        pessoa = Pessoa(
            nome=nome,
            data_nascimento=parse_date(data_dict.get('data_nascimento')),
            whatsapp=data_dict.get('whatsapp', ''),
            plano=data_dict.get('plano', 'N/A'),
            vencimento_plano=data_dict.get('vencimento_plano', ''),
            estado_plano=data_dict.get('estado_plano', ''),
            genero=data_dict.get('genero', ''),
            frequencia=data_dict.get('frequencia', ''),
            calcado=data_dict.get('calcado', '')
        )
        
        member_id = db_manager.add_member(pessoa)
        if member_id:
            membros_migrados[nome] = member_id
    
    print(f"✓ {len(membros_migrados)} membros inseridos no banco de dados.")

    # --- PASSO 6: MIGRAR CHECK-INS ---
    print("\n[6/6] Migrando registros de check-in...")
    total_checkins = 0
    for sheet_name in SHEET_NAMES:
        print(f"  → Processando check-ins da aba: {sheet_name}")
        data = sheets_service.read_spreadsheet(SPREADSHEET_ID, 'A:CZ', sheet_name)
        
        if not data or len(data) <= DAY_HEADER_ROW_INDEX:
            print(f"    ⚠ Dados insuficientes para check-ins na aba {sheet_name}")
            continue
        
        date_map: Dict[int, date] = {}
        month, year = parse_sheet_month_year(sheet_name)
        day_header_row = data[DAY_HEADER_ROW_INDEX]

        for col_index in range(CHECKIN_DATA_START_COL, len(day_header_row)):
            day_str = get_safe_value(day_header_row, col_index)
            if day_str.isdigit():
                try:
                    date_obj = datetime(year, month, int(day_str)).date()
                    date_map[col_index] = date_obj
                except ValueError:
                    pass
        
        for row in data[3:]:
            nome = get_safe_value(row, COL_NOME)
            member_id = membros_migrados.get(nome)
            
            if member_id:
                for check_col, check_date in date_map.items():
                    check_value = get_safe_value(row, check_col)
                    
                    if check_value and check_value.upper() not in ['FALSE', 'F']:
                        period_col = check_col + 1
                        period_value = get_safe_value(row, period_col)
                        check_time = get_time_from_period(period_value)
                        full_checkin_datetime = datetime.combine(check_date, check_time)
                        
                        db_manager.add_checkin(member_id, full_checkin_datetime)
                        total_checkins += 1
                        
    print(f"✓ {total_checkins} registros de check-in migrados.")
    
    # --- RESUMO FINAL ---
    db_manager.close()
    print("\n" + "=" * 60)
    print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print(f"\n📊 Resumo:")
    print(f"  • Membros únicos migrados: {len(membros_migrados)}")
    print(f"  • Total de Check-ins: {total_checkins}")
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