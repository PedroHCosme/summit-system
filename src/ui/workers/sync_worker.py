"""Worker para sincronização de dados do Google Sheets."""

from PyQt6.QtCore import QThread, pyqtSignal
from datetime import datetime
from typing import Dict, List, Any, Optional

from src.data.google_sheets_service import GoogleSheetsService
from src.data.database_manager import DatabaseManager
from src.data.migrations import DatabaseMigrator
from src.config import (
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
    COL_CALCADO,
)
from src.utils.date_utils import parse_date as parse_flexible_date


class SyncWorker(QThread):
    """Worker para executar sincronização em background."""
    
    # Sinais
    progress_updated = pyqtSignal(str, int)  # mensagem, progresso (0-100)
    sync_completed = pyqtSignal(dict)  # resultado da sincronização
    sync_failed = pyqtSignal(str)  # mensagem de erro
    
    # Lista de abas (meses) para sincronizar
    SHEET_NAMES = [
        'Jan/25', 'Fev/25', 'Mar/25', 'Abr/25', 
        'Mai/25', 'Jun/25', 'Jul/25', 'Ago/25', 
        'Set/25', 'Out/25', 'Nov/25', 'Dez/25'
    ]
    
    CHECKIN_DATA_START_COL = 4
    DAY_HEADER_ROW_INDEX = 1
    
    def __init__(self):
        super().__init__()
        self.sheets_service: Optional[GoogleSheetsService] = None
        self.db_manager: Optional[DatabaseManager] = None
    
    def _calculate_estado_from_vencimento(self, vencimento_str: str) -> str:
        """
        Calcula o estado do plano baseado na data de vencimento.
        
        Args:
            vencimento_str: Data no formato DD/MM/YYYY, DD/MM/YY, DD-MM-YY, YY-MM-DD ou YYYY-MM-DD
            
        Returns:
            'ATIVO' se não venceu, 'INATIVO' se já venceu
        """
        if not vencimento_str or not vencimento_str.strip():
            return 'ATIVO'

        parsed = parse_flexible_date(vencimento_str)
        if not parsed:
            return 'ATIVO'

        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        vencimento_dt = parsed.replace(hour=0, minute=0, second=0, microsecond=0)

        return 'INATIVO' if vencimento_dt < hoje else 'ATIVO'
    
    def run(self):
        """Executa a sincronização."""
        try:
            # Fase 1: Conectar ao Google Sheets
            self.progress_updated.emit("🔄 Conectando ao Google Sheets...", 5)
            self.sheets_service = GoogleSheetsService(CREDENTIALS_PATH)
            if not self.sheets_service.authenticate():
                self.sync_failed.emit("❌ Erro ao autenticar no Google Sheets")
                return
            
            # Fase 2: Conectar ao banco de dados
            self.progress_updated.emit("🔄 Conectando ao banco de dados local...", 10)
            self.db_manager = DatabaseManager()
            if not self.db_manager.connect():
                self.sync_failed.emit("❌ Erro ao conectar ao banco de dados")
                return
            
            # Fase 3: Criar tabelas se não existirem
            self.progress_updated.emit("🔄 Verificando estrutura do banco...", 15)
            if not self.db_manager.create_tables():
                self.sync_failed.emit("❌ Erro ao criar/verificar tabelas")
                return

            # Fase 4: Aplicar migrações automáticas
            self.progress_updated.emit("🛠 Aplicando migrações automáticas...", 22)
            DatabaseMigrator(self.db_manager).run_all()

            # Fase 4.1: Otimizar banco após migrações
            self.progress_updated.emit("⚙️ Otimizando banco de dados...", 26)
            try:
                optimize_stats = self.db_manager.optimize_and_reindex()
                indices_checked = optimize_stats.get('indices_processed', 0)
                self.progress_updated.emit(
                    f"✓ Banco otimizado (índices verificados: {indices_checked})",
                    28
                )
            except Exception as exc:
                self.progress_updated.emit(
                    "⚠️ Otimização automática falhou; prosseguindo com a sincronização",
                    28
                )
                print(f"[SyncWorker] Aviso: falha ao otimizar banco automaticamente: {exc}")
            
            # Fase 5: Consolidar membros
            self.progress_updated.emit("📊 Lendo dados do Google Sheets...", 30)
            consolidated_members = self._consolidate_members()
            
            self.progress_updated.emit(
                f"✓ {len(consolidated_members)} membros únicos encontrados", 
                45
            )
            
            # Fase 6: Sincronizar membros
            self.progress_updated.emit("👥 Sincronizando membros...", 55)
            sync_result = self._sync_members(consolidated_members)
            
            self.progress_updated.emit(
                f"✓ {sync_result['novos']} novos, {sync_result['existentes']} existentes",
                75
            )
            
            # Fase 7: Sincronizar check-ins
            self.progress_updated.emit("📋 Sincronizando check-ins...", 82)
            checkin_result = self._sync_checkins(sync_result['mapeamento'])
            
            self.progress_updated.emit(
                f"✓ {checkin_result['novos']} novos check-ins",
                96
            )
            
            # Resultado final
            self.progress_updated.emit("✅ Sincronização concluída!", 100)
            
            # Emite resultado completo
            final_result = {
                'membros_novos': sync_result['novos'],
                'membros_existentes': sync_result['existentes'],
                'membros_total': len(sync_result['mapeamento']),
                'checkins_novos': checkin_result['novos'],
                'checkins_duplicados': checkin_result['duplicados'],
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            self.sync_completed.emit(final_result)
            
        except Exception as e:
            self.sync_failed.emit(f"❌ Erro durante sincronização: {str(e)}")
        finally:
            if self.db_manager:
                self.db_manager.close()
    
    def _get_safe_value(self, row: List, col_index: int) -> str:
        """Obtém valor de uma coluna de forma segura."""
        if col_index < len(row) and row[col_index]:
            value = str(row[col_index]).strip()
            
            # Filtrar valores inválidos/placeholder
            if value in ['----------', '---', '--', 'N/A', 'n/a', '#N/A']:
                return ""
            
            return value
        return ""
    
    def _consolidate_members(self) -> Dict[str, Dict[str, Any]]:
        """Consolida dados de membros de todas as abas."""
        if not self.sheets_service:
            raise RuntimeError("Serviço do Google Sheets não inicializado")
        consolidated = {}
        
        for sheet_name in self.SHEET_NAMES:
            data = self.sheets_service.read_spreadsheet(
                SPREADSHEET_ID, 'A:CZ', sheet_name
            )
            
            if not data or len(data) <= 3:
                continue
            
            for row in data[3:]:
                nome = self._get_safe_value(row, COL_NOME)
                plano = self._get_safe_value(row, COL_PLANO)
                
                if not nome or not plano:
                    continue
                
                if nome not in consolidated:
                    consolidated[nome] = {'nome': nome}
                
                member_data = {
                    'plano': plano,
                    'vencimento_plano': self._get_safe_value(row, COL_VENCIMENTO_PLANO),
                    'estado_plano': self._get_safe_value(row, COL_ESTADO_PLANO),
                    'data_nascimento': self._get_safe_value(row, COL_DATA_NASCIMENTO),
                    'whatsapp': self._get_safe_value(row, COL_WHATSAPP),
                    'genero': self._get_safe_value(row, COL_GENERO),
                    'frequencia': self._get_safe_value(row, COL_FREQUENCIA),
                    'calcado': self._get_safe_value(row, COL_CALCADO),
                }
                
                for key, value in member_data.items():
                    if value:
                        consolidated[nome][key] = value
        
        return consolidated
    
    def _sync_members(self, consolidated_members: Dict[str, Dict[str, Any]]) -> Dict:
        """Sincroniza membros no banco de dados."""
        if not self.db_manager:
            raise RuntimeError("Banco de dados não inicializado")
        # Carrega membros existentes
        existing_members = self.db_manager.get_all_members()
        existing_map = {m['nome']: m['id'] for m in existing_members}
        
        membros_migrados = {}
        novos = 0
        existentes = 0
        
        # Usa transação para garantir atomicidade
        with self.db_manager.transaction():
            for nome, data_dict in consolidated_members.items():
                vencimento = data_dict.get('vencimento_plano', '')
                
                # CORREÇÃO: Calcular estado automaticamente baseado no vencimento
                # Ignora o estado vindo do Sheets e calcula baseado na data
                estado_calculado = self._calculate_estado_from_vencimento(vencimento)
                
                member_data = {
                    'nome': nome,
                    'plano': data_dict.get('plano', 'N/A'),
                    'vencimento_plano': vencimento,
                    'estado_plano': estado_calculado,  # Usar o estado calculado, não o do Sheets
                    'data_nascimento': data_dict.get('data_nascimento', ''),
                    'whatsapp': data_dict.get('whatsapp', ''),
                    'genero': data_dict.get('genero', ''),
                    'frequencia': data_dict.get('frequencia', ''),
                    'calcado': data_dict.get('calcado', '')
                }
                
                if nome in existing_map:
                    member_id = existing_map[nome]
                    member_data['id'] = member_id
                    self.db_manager.update_member_from_dict(
                        member_data,
                        register_payment=True,
                        metodo_pagamento="Sincronização (Sheets)"
                    )
                    membros_migrados[nome] = member_id
                    existentes += 1
                else:
                    # Novo membro - remover campos vazios antes de inserir
                    final_data = {k: v for k, v in member_data.items() if v}
                    final_data['nome'] = nome
                    member_id = self.db_manager.add_member(final_data)
                    if member_id:
                        membros_migrados[nome] = member_id
                        novos += 1
                        self.db_manager.auto_register_plan_payment(
                            member_id=member_id,
                            plan_name=member_data.get('plano'),
                            vencimento=member_data.get('vencimento_plano'),
                            metodo_pagamento="Sincronização (Sheets)"
                        )
        
        return {
            'mapeamento': membros_migrados,
            'novos': novos,
            'existentes': existentes
        }
    
    def _sync_checkins(self, membros_migrados: Dict[str, int]) -> Dict:
        """Sincroniza check-ins no banco de dados."""
        if not self.db_manager:
            raise RuntimeError("Banco de dados não inicializado")
        if not self.sheets_service:
            raise RuntimeError("Serviço do Google Sheets não inicializado")
        from datetime import datetime, time, date
        
        total_novos = 0
        total_duplicados = 0
        
        def parse_sheet_month_year(sheet_name: str) -> tuple:
            month_map = {
                'Jan': 1, 'Fev': 2, 'Mar': 3, 'Abr': 4,
                'Mai': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
                'Set': 9, 'Out': 10, 'Nov': 11, 'Dez': 12
            }
            parts = sheet_name.split('/')
            month_abbr = parts[0]
            year = int('20' + parts[1])
            return month_map[month_abbr], year
        
        def get_time_from_period(period: str) -> time:
            period = period.upper()
            if period == 'T':
                return time(14, 0)
            if period == 'N':
                return time(19, 0)
            return time(9, 0)

        with self.db_manager.transaction():
            for sheet_name in self.SHEET_NAMES:
                data = self.sheets_service.read_spreadsheet(
                    SPREADSHEET_ID, 'A:CZ', sheet_name
                )
                
                if not data or len(data) <= self.DAY_HEADER_ROW_INDEX:
                    continue
                
                date_map = {}
                month, year = parse_sheet_month_year(sheet_name)
                day_header_row = data[self.DAY_HEADER_ROW_INDEX]
                
                for col_index in range(self.CHECKIN_DATA_START_COL, len(day_header_row)):
                    day_str = self._get_safe_value(day_header_row, col_index)
                    if day_str.isdigit():
                        try:
                            date_obj = datetime(year, month, int(day_str)).date()
                            date_map[col_index] = date_obj
                        except ValueError:
                            pass
                
                for row in data[3:]:
                    nome = self._get_safe_value(row, COL_NOME)
                    plano_na_aba = self._get_safe_value(row, COL_PLANO)
                    member_id = membros_migrados.get(nome)
                    
                    if member_id:
                        for check_col, check_date in date_map.items():
                            check_value = self._get_safe_value(row, check_col)
                            
                            if check_value and check_value.upper() not in ['FALSE', 'F']:
                                period_col = check_col + 1
                                period_value = self._get_safe_value(row, period_col)
                                check_time = get_time_from_period(period_value)
                                full_datetime = datetime.combine(check_date, check_time)
                                
                                # Verifica duplicação
                                if self.db_manager.checkin_exists(member_id, full_datetime):
                                    self.db_manager.ensure_payment_for_checkin(
                                        member_id,
                                        full_datetime,
                                        plan_context=plano_na_aba
                                    )
                                    total_duplicados += 1
                                    continue
                                
                                try:
                                    self.db_manager.add_checkin(
                                        member_id,
                                        full_datetime,
                                        plan_context=plano_na_aba,
                                        consume_voucher=False  # Não consumir vouchers para histórico
                                    )
                                    total_novos += 1
                                except ValueError as e:
                                    # Check-in duplicado (mesma data)
                                    if "duplicado" in str(e).lower():
                                        total_duplicados += 1
                                    else:
                                        raise
        
        return {
            'novos': total_novos,
            'duplicados': total_duplicados
        }
