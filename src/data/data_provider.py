"""
Camada de abstração de dados.
Decide automaticamente se busca dados do SQLite ou Google Sheets.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from src import config
from src.data.google_sheets_service import GoogleSheetsService
from src.data.database_manager import DatabaseManager
from src.utils.utils import parse_date, get_current_sheet_name
from src.core.models import Pessoa


# ============================================================================
# FLAG DE CONTROLE PRINCIPAL
# ============================================================================
USE_SQLITE = True  # Comece com False. Mude para True para ativar SQLite.
# ============================================================================


class DataProvider:
    """
    Provedor de dados unificado.
    Abstrai a fonte de dados (SQLite ou Google Sheets).
    """
    
    def __init__(self):
        """Inicializa o provedor de dados."""
        self.use_sqlite = USE_SQLITE
        
        # Inicializar conexões
        if self.use_sqlite:
            self.db_manager = DatabaseManager()
            self.db_manager.connect()
        else:
            self.sheets_service = GoogleSheetsService(config.CREDENTIALS_PATH)
            self.sheets_service.authenticate()
    
    def get_all_members(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os membros.
        
        Returns:
            Lista de dicionários com dados dos membros
        """
        if self.use_sqlite:
            return self._get_all_members_from_sqlite()
        else:
            return self._get_all_members_from_sheets()
    
    def find_members_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Busca membros por nome (busca parcial).
        
        Args:
            name: Nome ou parte do nome a buscar
            
        Returns:
            Lista de dicionários com dados dos membros encontrados
        """
        if self.use_sqlite:
            return self._find_members_by_name_from_sqlite(name)
        else:
            return self._find_members_by_name_from_sheets(name)
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um membro por ID.
        
        Args:
            member_id: ID do membro (ou índice da linha para Sheets)
            
        Returns:
            Dicionário com dados do membro ou None
        """
        if self.use_sqlite:
            return self._get_member_by_id_from_sqlite(member_id)
        else:
            return self._get_member_by_index_from_sheets(member_id)
    
    def get_birthdays_for_month(self, month: int) -> List[Dict[str, Any]]:
        """
        Retorna membros que fazem aniversário no mês especificado.
        
        Args:
            month: Número do mês (1-12)
            
        Returns:
            Lista de dicionários com dados dos aniversariantes
        """
        if self.use_sqlite:
            return self._get_birthdays_from_sqlite(month)
        else:
            return self._get_birthdays_from_sheets(month)
    
    def get_member_checkin_history(self, member_id: int) -> List[Dict[str, Any]]:
        """Busca o histórico de check-ins de um membro."""
        if self.db_manager:
            return self.db_manager.get_member_checkin_history(member_id)
        return []

    def add_member(self, member_data: Dict[str, Any]) -> Optional[int]:
        """Delega a adição de um novo membro para o db_manager."""
        if self.db_manager:
            return self.db_manager.add_member(member_data)
        return None

    def update_member(
        self, 
        member_data: Dict[str, Any], 
        register_payment: bool = False,
        metodo_pagamento: str = ""
    ) -> bool:
        """
        Atualiza os dados de um membro existente.
        
        Args:
            member_data: Dicionário com os dados atualizados do membro (deve incluir 'id')
            register_payment: Se True, registra pagamento ao atualizar plano/vencimento
            metodo_pagamento: Método de pagamento usado
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            return self.db_manager.update_member_from_dict(
                member_data, 
                register_payment, 
                metodo_pagamento
            )
        else:
            # Funcionalidade não suportada para Google Sheets
            print("Aviso: A funcionalidade de atualização não é suportada para Google Sheets.")
            return False

    def add_checkin(self, member_id: int, checkin_datetime: datetime) -> Optional[int]:
        """
        Registra um check-in para um membro.
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data e hora do check-in
            
        Returns:
            ID do novo registro de check-in ou None
        """
        if self.use_sqlite:
            return self.db_manager.add_checkin(member_id, checkin_datetime)
        else:
            # Funcionalidade não suportada para Google Sheets
            print("Aviso: A funcionalidade de check-in não é suportada para Google Sheets.")
            return None
    
    def delete_member(self, member_id: int) -> bool:
        """
        Deleta um membro do sistema.
        
        Args:
            member_id: ID do membro a ser deletado
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            return self.db_manager.delete_member(member_id)
        else:
            # Funcionalidade não suportada para Google Sheets
            print("Aviso: A funcionalidade de exclusão de membro não é suportada para Google Sheets.")
            return False
    
    def delete_checkin(self, checkin_id: int) -> bool:
        """
        Remove um registro de check-in.
        
        Args:
            checkin_id: ID do check-in a ser removido
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            return self.db_manager.delete_checkin(checkin_id)
        else:
            # Funcionalidade não suportada para Google Sheets
            print("Aviso: A funcionalidade de exclusão de check-in não é suportada para Google Sheets.")
            return False

    def get_checkins_today(self) -> int:
        """Retorna o número de check-ins de hoje."""
        if self.use_sqlite:
            return self.db_manager.get_checkins_today()
        return 0

    def get_checkins_today_details(self) -> List[Dict[str, Any]]:
        """Retorna os detalhes dos check-ins de hoje."""
        if self.use_sqlite:
            return self.db_manager.get_checkins_today_details()
        return []

    def get_last_checkins(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retorna os últimos check-ins."""
        if self.use_sqlite:
            return self.db_manager.get_last_checkins(limit)
        return []

    def update_expired_plans(self):
        """Delega a atualização de planos expirados para o db_manager."""
        if self.db_manager:
            return self.db_manager.update_expired_plans()
        return 0

    # ========================================================================
    # MÉTODOS PRIVADOS - SQLite
    # ========================================================================
    
    def _get_all_members_from_sqlite(self) -> List[Dict[str, Any]]:
        """Busca todos os membros do SQLite."""
        return self.db_manager.get_all_members()
    
    def _find_members_by_name_from_sqlite(self, name: str) -> List[Dict[str, Any]]:
        """Busca membros por nome no SQLite."""
        return self.db_manager.find_members_by_name(name)
    
    def _get_member_by_id_from_sqlite(self, member_id: int) -> Optional[Dict[str, Any]]:
        """Busca membro por ID no SQLite."""
        return self.db_manager.get_member_by_id(member_id)
    
    def _get_birthdays_from_sqlite(self, month: int) -> List[Dict[str, Any]]:
        """
        Busca aniversariantes do mês no SQLite.
        Delega a filtragem para o banco de dados para melhor performance.
        """
        return self.db_manager.get_members_by_birthday_month(month)
    
    def _get_member_checkin_history_from_sqlite(self, member_id: int) -> List[Dict[str, Any]]:
        """Busca histórico de check-ins do membro no SQLite."""
        return self.db_manager.get_member_checkin_history(member_id)
    
    # ========================================================================
    # MÉTODOS PRIVADOS - Google Sheets
    # ========================================================================
    
    def _get_all_members_from_sheets(self) -> List[Dict[str, Any]]:
        """Busca todos os membros do Google Sheets."""
        sheet_name = get_current_sheet_name()
        data = self.sheets_service.read_spreadsheet(
            config.SPREADSHEET_ID,
            range_name='A:BT',
            sheet_name=sheet_name
        )
        
        if not data:
            return []
        
        members = []
        for row_index, row in enumerate(data):
            if row_index == 0:  # Pular cabeçalho
                continue
            
            member_dict = self._row_to_dict(row, row_index)
            if member_dict and member_dict.get('nome'):
                members.append(member_dict)
        
        return members
    
    def _find_members_by_name_from_sheets(self, name: str) -> List[Dict[str, Any]]:
        """Busca membros por nome no Google Sheets."""
        all_members = self._get_all_members_from_sheets()
        name_lower = name.lower()
        
        results = []
        for member in all_members:
            if name_lower in member.get('nome', '').lower():
                results.append(member)
        
        return results
    
    def _get_member_by_index_from_sheets(self, row_index: int) -> Optional[Dict[str, Any]]:
        """Busca membro por índice da linha no Google Sheets."""
        sheet_name = get_current_sheet_name()
        data = self.sheets_service.read_spreadsheet(
            config.SPREADSHEET_ID,
            range_name='A:BT',
            sheet_name=sheet_name
        )
        
        if not data or row_index >= len(data):
            return None
        
        return self._row_to_dict(data[row_index], row_index)
    
    def _get_birthdays_from_sheets(self, month: int) -> List[Dict[str, Any]]:
        """Busca aniversariantes do mês no Google Sheets."""
        all_members = self._get_all_members_from_sheets()
        birthdays = []
        
        for member in all_members:
            birth_date_str = member.get('data_nascimento')
            if birth_date_str:
                birth_date = parse_date(birth_date_str)
                if birth_date and birth_date.month == month:
                    birthdays.append(member)
        
        # Função auxiliar para ordenação segura
        def get_day(member_dict: Dict[str, Any]) -> int:
            date_str = member_dict.get('data_nascimento')
            if not date_str:
                return 0
            date_obj = parse_date(date_str)
            return date_obj.day if date_obj else 0

        # Ordenar por dia
        birthdays.sort(key=get_day)
        return birthdays
    
    def _get_member_checkin_history_from_sheets(self, member_id: int) -> List[Dict[str, Any]]:
        """
        Busca histórico de check-ins do membro no Google Sheets.
        Nota: Esta funcionalidade não está disponível para Google Sheets,
        pois o histórico de check-ins só é armazenado no SQLite.
        """
        return []
    
    def _row_to_dict(self, row: list, row_index: int) -> Dict[str, Any]:
        """
        Converte uma linha da planilha em dicionário.
        
        Args:
            row: Lista com os valores da linha
            row_index: Índice da linha (para usar como ID)
            
        Returns:
            Dicionário com os dados do membro
        """
        def get_value(col_index: int) -> str:
            if col_index < len(row) and row[col_index]:
                return str(row[col_index]).strip()
            return ""
        
        return {
            'id': row_index,  # Usar índice da linha como ID
            'nome': get_value(config.COL_NOME),
            'plano': get_value(config.COL_PLANO),
            'vencimento_plano': get_value(config.COL_VENCIMENTO_PLANO),
            'estado_plano': get_value(config.COL_ESTADO_PLANO),
            'data_nascimento': get_value(config.COL_DATA_NASCIMENTO),
            'whatsapp': get_value(config.COL_WHATSAPP),
            'genero': get_value(config.COL_GENERO),
            'frequencia': get_value(config.COL_FREQUENCIA),
            'calcado': get_value(config.COL_CALCADO),
        }
    
    def close(self):
        """Fecha conexões abertas."""
        if self.use_sqlite and hasattr(self, 'db_manager'):
            self.db_manager.close()


# ============================================================================
# FUNÇÕES DE CONVENIÊNCIA (API Funcional)
# ============================================================================

# Instância global do provider
_provider = None


def get_provider() -> DataProvider:
    """Retorna a instância global do DataProvider."""
    global _provider
    if _provider is None:
        _provider = DataProvider()
    return _provider


def get_all_members() -> List[Dict[str, Any]]:
    """Retorna todos os membros."""
    return get_provider().get_all_members()


def find_members_by_name(name: str) -> List[Dict[str, Any]]:
    """Busca membros por nome."""
    return get_provider().find_members_by_name(name)


def get_member_by_id(member_id: int) -> Optional[Dict[str, Any]]:
    """Busca membro por ID."""
    return get_provider().get_member_by_id(member_id)


def get_birthdays_for_month(month: int) -> List[Dict[str, Any]]:
    """Retorna aniversariantes do mês."""
    return get_provider().get_birthdays_for_month(month)


def get_member_checkin_history(member_id: int) -> List[Dict[str, Any]]:
    """Retorna histórico completo de check-ins de um membro."""
    return get_provider().get_member_checkin_history(member_id)


def add_member(member_data: Dict[str, Any]) -> Optional[int]:
    """Adiciona um novo membro."""
    return get_provider().add_member(member_data)


def add_checkin(member_id: int, checkin_datetime: datetime) -> Optional[int]:
    """Registra um check-in para um membro."""
    return get_provider().add_checkin(member_id, checkin_datetime)

def get_checkins_today() -> int:
    """Retorna o número de check-ins de hoje."""
    return get_provider().get_checkins_today()

def get_checkins_today_details() -> List[Dict[str, Any]]:
    """Retorna os detalhes dos check-ins de hoje."""
    return get_provider().get_checkins_today_details()

def get_last_checkins(limit: int = 5) -> List[Dict[str, Any]]:
    """Retorna os últimos check-ins."""
    return get_provider().get_last_checkins(limit)


def update_member(
    member_data: Dict[str, Any], 
    register_payment: bool = False,
    metodo_pagamento: str = ""
) -> bool:
    """
    Atualiza os dados de um membro existente.
    
    Args:
        member_data: Dicionário com os dados atualizados do membro (deve incluir 'id')
        register_payment: Se True, registra pagamento ao atualizar plano/vencimento
        metodo_pagamento: Método de pagamento usado
        
    Returns:
        True se a atualização foi bem-sucedida, False caso contrário
    """
    return get_provider().update_member(member_data, register_payment, metodo_pagamento)


def delete_member(member_id: int) -> bool:
    """
    Deleta um membro do sistema.
    
    Args:
        member_id: ID do membro a ser deletado
        
    Returns:
        True se a exclusão foi bem-sucedida, False caso contrário
    """
    return get_provider().delete_member(member_id)


def delete_checkin(checkin_id: int) -> bool:
    """
    Remove um registro de check-in.
    
    Args:
        checkin_id: ID do check-in a ser removido
        
    Returns:
        True se a exclusão foi bem-sucedida, False caso contrário
    """
    return get_provider().delete_checkin(checkin_id)
