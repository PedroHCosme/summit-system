"""Worker para buscar dados de aniversariantes."""

from PyQt6.QtCore import QThread, pyqtSignal


class DataFetchWorker(QThread):
    """Thread para buscar dados sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    fetch_completed = pyqtSignal(list, str)
    
    def __init__(self, manager):
        """
        Inicializa o worker.
        
        Args:
            manager: Instância do AniversariantesManager
        """
        super().__init__()
        self.manager = manager
    
    def run(self):
        """Executa a busca de dados."""
        # Busca aniversariantes
        self.status_updated.emit("Buscando aniversariantes...")
        
        aniversariantes = self.manager.get_aniversariantes_mes_atual()
        mes_nome = self.manager.get_nome_mes_atual()
        
        if not aniversariantes:
            self.status_updated.emit("Nenhum aniversariante encontrado.")
        else:
            self.status_updated.emit(f"{len(aniversariantes)} aniversariante(s) encontrado(s)!")
        
        self.fetch_completed.emit(aniversariantes, mes_nome)
