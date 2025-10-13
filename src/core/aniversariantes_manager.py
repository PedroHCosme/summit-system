"""
Gerenciador de aniversariantes.
Responsável por extrair e processar pessoas que fazem aniversário no mês.
"""
from datetime import datetime
from typing import List, Optional

from src.core.models import Pessoa
from src.utils.utils import parse_date, get_current_month_name
from src.data.data_provider import get_provider


class AniversariantesManager:
    """Gerencia a extração e processamento de aniversariantes usando o DataProvider."""
    
    def __init__(self):
        """Inicializa o gerenciador."""
        self.data_provider = get_provider()
    
    def get_aniversariantes_mes_atual(self) -> List[Pessoa]:
        """
        Busca os aniversariantes do mês atual usando o DataProvider.
        
        Returns:
            Lista de objetos Pessoa ordenada por dia
        """
        mes_atual = datetime.now().month
        
        # Busca aniversariantes do mês através do data_provider
        members_data = self.data_provider.get_birthdays_for_month(mes_atual)
        
        # Converte dicionários em objetos Pessoa
        aniversariantes = []
        for member_dict in members_data:
            pessoa = self._dict_to_pessoa(member_dict)
            if pessoa:
                aniversariantes.append(pessoa)
        
        # Ordena por dia do mês
        aniversariantes.sort()
        return aniversariantes
    
    def _dict_to_pessoa(self, member_dict: dict) -> Optional[Pessoa]:
        """
        Converte um dicionário de membro em objeto Pessoa.
        
        Args:
            member_dict: Dicionário com dados do membro
            
        Returns:
            Objeto Pessoa ou None se dados inválidos
        """
        nome = member_dict.get('nome', '')
        data_nasc_str = member_dict.get('data_nascimento', '')
        whatsapp = member_dict.get('whatsapp', '')
        plano = member_dict.get('plano', 'N/A')
        
        if not nome or not data_nasc_str:
            return None
        
        # Parse da data
        data_nascimento = parse_date(data_nasc_str)
        if not data_nascimento:
            return None
        
        # Cria objeto Pessoa
        return Pessoa(
            nome=nome,
            data_nascimento=data_nascimento,
            whatsapp=whatsapp or "",
            plano=plano or "N/A"
        )
    
    @staticmethod
    def get_nome_mes_atual() -> str:
        """Retorna o nome do mês atual."""
        return get_current_month_name()
