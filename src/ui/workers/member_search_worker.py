"""Worker para buscar membros."""

from PyQt6.QtCore import QThread, pyqtSignal


class MemberSearchWorker(QThread):
    """Thread para buscar membros sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    search_completed = pyqtSignal(list)  # Retorna lista de resultados
    
    def __init__(self, search_service, search_term):
        """
        Inicializa o worker.
        
        Args:
            search_service: Instância do MemberSearchService
            search_term: Termo de busca
        """
        super().__init__()
        self.search_service = search_service
        self.search_term = search_term
    
    def run(self):
        """Executa a busca de membro por nome."""
        self.status_updated.emit("Buscando...")
        
        # Busca por nome retorna lista de resultados
        results = self.search_service.search_by_name(self.search_term)
        if results:
            self.status_updated.emit(f"{len(results)} resultado(s) encontrado(s)!")
            self.search_completed.emit(results)
        else:
            self.status_updated.emit("Nenhum membro encontrado.")
            self.search_completed.emit([])
