"""
Serviço para busca de membros.
Usa o data_provider para abstrair a fonte de dados.
"""
from typing import Optional, Dict, List, Any
from src.data.data_provider import get_provider


class MemberSearchService:
    """Gerencia a busca de membros usando o DataProvider."""
    
    def __init__(self):
        """Inicializa o serviço de busca."""
        self.data_provider = get_provider()
    
    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Busca membros por nome (busca por similaridade, case-insensitive).
        
        Args:
            name: Nome ou parte do nome para buscar
            
        Returns:
            Lista de dicionários com dados dos membros encontrados
        """
        if not name or not name.strip():
            return []
        
        # Usa o data_provider para buscar
        members = self.data_provider.find_members_by_name(name.strip())
        
        # Formata resultados para compatibilidade com a UI
        results = []
        for member in members:
            results.append({
                'id': member.get('id', 0),  # ID único do membro
                'nome': member.get('nome', ''),
                'member_data': member  # Armazena dados completos
            })
        
        return results
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém os dados completos de um membro pelo ID.
        
        Args:
            member_id: ID do membro
            
        Returns:
            Dicionário com os dados completos do membro
        """
        return self.data_provider.get_member_by_id(member_id)
