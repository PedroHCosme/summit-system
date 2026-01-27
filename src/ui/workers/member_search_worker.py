"""Worker para buscar membros."""

from PyQt6.QtCore import QThread, pyqtSignal
from src.data.db import get_db_session
from src.services.member_service import MemberService


class MemberSearchWorker(QThread):
    """Thread para buscar membros sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    search_completed = pyqtSignal(list)  # Retorna lista de resultados
    
    def __init__(self, search_term):
        """
        Inicializa o worker.
        
        Args:
            search_term: Termo de busca
        """
        super().__init__()
        self.search_term = search_term
    
    def run(self):
        """Executa a busca de membro por nome."""
        self.status_updated.emit("Buscando...")
        
        try:
            # Criar uma nova sessão e serviço para esta thread
            with get_db_session() as session:
                service = MemberService(db_session=session)
                
                # Busca por nome retorna lista de resultados
                # Importante: converter para dicts para passar entre threads com segurança
                results = service.search_by_name_as_dicts(self.search_term)
                
                if results:
                    self.status_updated.emit(f"{len(results)} resultado(s) encontrado(s)!")
                    self.search_completed.emit(results)
                else:
                    self.status_updated.emit("Nenhum membro encontrado.")
                    self.search_completed.emit([])
                    
        except Exception as e:
            self.status_updated.emit(f"Erro na busca: {str(e)}")
            self.search_completed.emit([])
