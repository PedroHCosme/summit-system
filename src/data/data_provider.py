"""
Camada de abstração de dados.
Agora utiliza SQLAlchemy e serviços para acesso aos dados.
Mantém compatibilidade com Google Sheets para modo legado.
"""
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from src import config
from src.data.db import get_session_factory, create_session
from src.services.member_service import MemberService
from src.services.checkin_service import CheckinService
from src.services.payment_service import PaymentService
from src.services.plan_service import PlanService
from src.utils.utils import parse_date, get_current_sheet_name

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

USE_SQLITE = True  # Sempre usar SQLite com SQLAlchemy agora


class DataProvider:
    """
    Provedor de dados unificado.
    Utiliza SQLAlchemy ORM e serviços para acesso aos dados.
    Mantém compatibilidade com API existente.
    """
    
    def __init__(self):
        """Inicializa o provedor de dados."""
        self.use_sqlite = USE_SQLITE
        
        # SQLAlchemy session factory
        self._session_factory = get_session_factory()
        self._session: Optional["Session"] = None
        
        # Serviços (lazy initialization)
        self._member_service: Optional[MemberService] = None
        self._checkin_service: Optional[CheckinService] = None
        self._payment_service: Optional[PaymentService] = None
        self._plan_service: Optional[PlanService] = None
        
        # Google Sheets (para modo legado)
        if not self.use_sqlite:
            from src.data.google_sheets_service import GoogleSheetsService
            self.sheets_service = GoogleSheetsService(config.CREDENTIALS_PATH)
            self.sheets_service.authenticate()
    
    @property
    def session(self) -> "Session":
        """Retorna a sessão SQLAlchemy atual (lazy initialization)."""
        if self._session is None:
            self._session = self._session_factory()
        return self._session
    
    @property
    def member_service(self) -> MemberService:
        """Retorna o serviço de membros (lazy initialization)."""
        if self._member_service is None:
            self._member_service = MemberService(db_session=self.session)
        return self._member_service
    
    @property
    def checkin_service(self) -> CheckinService:
        """Retorna o serviço de check-in (lazy initialization)."""
        if self._checkin_service is None:
            self._checkin_service = CheckinService(db_session=self.session)
        return self._checkin_service
    
    @property
    def payment_service(self) -> PaymentService:
        """Retorna o serviço de pagamentos (lazy initialization)."""
        if self._payment_service is None:
            self._payment_service = PaymentService(db_session=self.session)
        return self._payment_service
    
    @property
    def plan_service(self) -> PlanService:
        """Retorna o serviço de planos (lazy initialization)."""
        if self._plan_service is None:
            self._plan_service = PlanService(db_session=self.session)
        return self._plan_service
    
    def get_all_members(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os membros.
        
        Returns:
            Lista de dicionários com dados dos membros
        """
        if self.use_sqlite:
            return self.member_service.get_all_as_dicts()
        else:
            return self._get_all_members_from_sheets()
    
    def get_members_paginated(self, page: int = 1, page_size: int = 50,
                              filter_text: str = "", filter_plan: str = "",
                              filter_status: str = "",
                              sort_by: str = "nome", sort_dir: str = "asc") -> Dict[str, Any]:
        """
        Retorna membros com paginação e filtros.
        
        Args:
            page: Número da página (começa em 1)
            page_size: Quantidade de itens por página
            filter_text: Texto para filtrar por nome
            filter_plan: Filtrar por plano específico
            filter_status: Filtrar por status (ATIVO/INATIVO)
            sort_by: Coluna para ordenação (nome, data_cadastro, vencimento_plano)
            sort_dir: Direção da ordenação (asc, desc)
            
        Returns:
            Dicionário com dados paginados
        """
        if self.use_sqlite:
            result = self.member_service.get_paginated(
                page=page,
                page_size=page_size,
                filter_text=filter_text,
                filter_plan=filter_plan,
                filter_status=filter_status,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
            return {
                'members': result.members,
                'total': result.total,
                'page': result.page,
                'total_pages': result.total_pages,
                'page_size': result.page_size
            }
        else:
            all_members = self._get_all_members_from_sheets()
            
            filtered = all_members
            if filter_text:
                tokens = filter_text.lower().split()
                filtered = [m for m in filtered if all(token in m.get('nome', '').lower() for token in tokens)]
            if filter_plan:
                filtered = [m for m in filtered if m.get('plano') == filter_plan]
            if filter_status:
                filtered = [m for m in filtered if m.get('estado_plano') == filter_status]
            
            reverse = (sort_dir == "desc")
            filtered.sort(key=lambda x: (x.get(sort_by) is None, x.get(sort_by, '')), reverse=reverse)
            
            total = len(filtered)
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            page = max(1, min(page, total_pages)) if total_pages > 0 else 1
            start = (page - 1) * page_size
            end = start + page_size
            
            return {
                'members': filtered[start:end],
                'total': total,
                'page': page,
                'total_pages': total_pages,
                'page_size': page_size
            }

    
    def find_members_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Busca membros por nome (busca parcial).
        
        Args:
            name: Nome ou parte do nome a buscar
            
        Returns:
            Lista de dicionários com dados dos membros encontrados
        """
        if self.use_sqlite:
            return self.member_service.search_by_name_as_dicts(name)
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
            return self.member_service.get_by_id_as_dict(member_id)
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
            return self.member_service.get_birthdays(month)
        else:
            return self._get_birthdays_from_sheets(month)
    
    def add_member(self, member_data: Dict[str, Any]) -> Optional[int]:
        """Adiciona um novo membro."""
        if self.use_sqlite:
            result = self.member_service.create(member_data)
            return result.member_id if result.success else None
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
            result = self.member_service.update_from_dict(
                member_data, 
                register_payment, 
                metodo_pagamento
            )
            return result.success
        else:
            print("Aviso: A funcionalidade de atualização não é suportada para Google Sheets.")
            return False
    
    def delete_member(self, member_id: int) -> bool:
        """
        Deleta um membro do sistema.
        
        Args:
            member_id: ID do membro a ser deletado
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            result = self.member_service.delete(member_id)
            return result.success
        else:
            print("Aviso: A funcionalidade de exclusão de membro não é suportada para Google Sheets.")
            return False
    
    def update_expired_plans(self) -> int:
        """Atualiza planos expirados para INATIVO (ver plan_status.py)."""
        if self.use_sqlite:
            return self.member_service.update_expired_plans()
        return 0
    
    def get_member_checkin_history(self, member_id: int) -> List[Dict[str, Any]]:
        """Busca o histórico de check-ins de um membro."""
        if self.use_sqlite:
            return self.checkin_service.get_member_history(member_id)
        return []

    def add_checkin(
        self,
        member_id: int,
        checkin_datetime: datetime,
        plan_context: Optional[str] = None
    ) -> Optional[int]:
        """
        Registra um check-in para um membro.
        
        Utiliza o CheckinService para validação e lógica de negócio.
        
        Args:
            member_id: ID do membro
            checkin_datetime: Data e hora do check-in
            plan_context: Contexto de plano opcional para pagamento
            
        Returns:
            ID do novo registro de check-in ou None
            
        Raises:
            ValueError: Se o check-in for inválido (duplicado, membro não existe, etc.)
        """
        if self.use_sqlite:
            result = self.checkin_service.perform_checkin(
                member_id, checkin_datetime, plan_context
            )
            if result.success:
                return result.checkin_id
            else:
                raise ValueError(result.message)
        else:
            print("Aviso: A funcionalidade de check-in não é suportada para Google Sheets.")
            return None
    
    def delete_checkin(self, checkin_id: int) -> bool:
        """
        Remove um registro de check-in.
        
        Args:
            checkin_id: ID do check-in a ser removido
            
        Returns:
            True se a exclusão foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            result = self.checkin_service.delete_checkin(checkin_id)
            return result.success
        else:
            print("Aviso: A funcionalidade de exclusão de check-in não é suportada para Google Sheets.")
            return False
    
    def update_checkin_datetime(self, checkin_id: int, new_datetime) -> bool:
        """
        Atualiza a data/hora de um check-in existente.
        
        Args:
            checkin_id: ID do check-in a ser atualizado
            new_datetime: Nova data/hora para o check-in (datetime object)
            
        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        if self.use_sqlite:
            result = self.checkin_service.update_datetime(checkin_id, new_datetime)
            return result.success
        else:
            print("Aviso: A funcionalidade de edição de check-in não é suportada para Google Sheets.")
            return False

    def get_checkins_today(self) -> int:
        """Retorna o número de check-ins de hoje."""
        if self.use_sqlite:
            return self.checkin_service.count_today()
        return 0

    def get_checkins_today_details(self) -> List[Dict[str, Any]]:
        """Retorna os detalhes dos check-ins de hoje."""
        if self.use_sqlite:
            return self.checkin_service.get_today_details()
        return []
    
    def get_checkins_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Retorna os detalhes dos check-ins de uma data específica."""
        if self.use_sqlite:
            return self.checkin_service.get_by_date(date_str)
        return []

    def get_last_checkins(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Retorna os últimos check-ins."""
        if self.use_sqlite:
            return self.checkin_service.get_recent(limit)
        return []
    
    def get_checkins_today_list(self) -> List[Dict[str, Any]]:
        """Retorna todos os check-ins de hoje."""
        if self.use_sqlite:
            return self.checkin_service.get_today_list()
        return []
    
    def get_member_payment_history(self, member_id: int) -> List[Dict[str, Any]]:
        """Retorna o histórico de pagamentos de um membro."""
        if self.use_sqlite:
            return self.payment_service.get_member_history(member_id)
        return []
    
    def get_financial_summary(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Retorna um resumo financeiro para um período.
        
        Returns:
            Dicionário com total_receita, total_transacoes, ticket_medio
        """
        if self.use_sqlite:
            summary = self.payment_service.get_summary(start_date, end_date)
            return {
                'total_receita': summary.total_receita,
                'total_transacoes': summary.total_transacoes,
                'ticket_medio': summary.ticket_medio
            }
        return {'total_receita': 0, 'total_transacoes': 0, 'ticket_medio': 0}
    
    def get_revenue_breakdown(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna a receita agrupada por tipo de transação.
        """
        if self.use_sqlite:
            breakdown = self.payment_service.get_breakdown(start_date, end_date)
            return [
                {
                    'tipo_transacao': item.tipo_transacao,
                    'total_valor': item.total_valor,
                    'quantidade': item.quantidade
                }
                for item in breakdown
            ]
        return []
    
    def get_transactions_in_range(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retorna transações em um período."""
        if self.use_sqlite:
            return self.payment_service.get_transactions(start_date, end_date, limit)
        return []
    
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
            if row_index == 0:
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
        
        def get_day(member_dict: Dict[str, Any]) -> int:
            """Extrai o dia da data de nascimento para ordenação."""
            date_str = member_dict.get('data_nascimento')
            if not date_str:
                return 0
            date_obj = parse_date(date_str)
            return date_obj.day if date_obj else 0

        birthdays.sort(key=get_day)
        return birthdays
    
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
            """Obtém valor da coluna com fallback para string vazia."""
            if col_index < len(row) and row[col_index]:
                return str(row[col_index]).strip()
            return ""
        
        return {
            'id': row_index,
            'nome': get_value(config.COL_NOME),
            'plano': get_value(config.COL_PLANO),
            'vencimento_plano': get_value(config.COL_VENCIMENTO_PLANO),
            'estado_plano': get_value(config.COL_ESTADO_PLANO),
            'data_nascimento': get_value(config.COL_DATA_NASCIMENTO),
            'whatsapp': get_value(config.COL_WHATSAPP),
            'genero': get_value(config.COL_GENERO),
            'frequencia': get_value(config.COL_FREQUENCIA),
            'calcado': get_value(config.COL_CALCADO),
            'profissao': get_value(config.COL_PROFISSAO),
            'contato_emergencia': get_value(config.COL_CONTATO_EMERGENCIA),
        }
    
    def close(self):
        """Fecha conexões abertas."""
        if self._session is not None:
            self._session.close()
            self._session = None


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


def add_checkin(
    member_id: int,
    checkin_datetime: datetime,
    plan_context: Optional[str] = None
) -> Optional[int]:
    """Registra um check-in para um membro."""
    return get_provider().add_checkin(member_id, checkin_datetime, plan_context)

def get_checkins_today() -> int:
    """Retorna o número de check-ins de hoje."""
    return get_provider().get_checkins_today()

def get_checkins_today_details() -> List[Dict[str, Any]]:
    """Retorna os detalhes dos check-ins de hoje."""
    return get_provider().get_checkins_today_details()

def get_checkins_by_date(date_str: str) -> List[Dict[str, Any]]:
    """Retorna os detalhes dos check-ins de uma data específica."""
    return get_provider().get_checkins_by_date(date_str)

def get_last_checkins(limit: int = 5) -> List[Dict[str, Any]]:
    """Retorna os últimos check-ins."""
    return get_provider().get_last_checkins(limit)

def get_checkins_today_list() -> List[Dict[str, Any]]:
    """Retorna todos os check-ins de hoje."""
    return get_provider().get_checkins_today_list()


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


def update_checkin_datetime(checkin_id: int, new_datetime) -> bool:
    """
    Atualiza a data/hora de um check-in existente.
    
    Args:
        checkin_id: ID do check-in a ser atualizado
        new_datetime: Nova data/hora para o check-in (datetime object)
        
    Returns:
        True se a atualização foi bem-sucedida, False caso contrário
    """
    return get_provider().update_checkin_datetime(checkin_id, new_datetime)
