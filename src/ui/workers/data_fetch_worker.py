"""Worker para buscar dados de aniversariantes."""

from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal


class DataFetchWorker(QThread):
    """Thread para buscar dados sem travar a GUI."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    fetch_completed = pyqtSignal(list, str)
    
    def __init__(self, manager, mes: Optional[int] = None):
        """
        Inicializa o worker.
        
        Args:
            manager: Instância do AniversariantesManager
            mes: Número do mês (1-12). Se None, usa o mês atual
        """
        super().__init__()
        self.manager = manager
        self.mes = mes
    
    def run(self):
        """Executa a busca de dados."""
        # Busca aniversariantes
        self.status_updated.emit("Buscando aniversariantes...")
        
        if self.mes is None:
            aniversariantes = self.manager.get_aniversariantes_mes_atual()
            mes_nome = self.manager.get_nome_mes_atual()
        else:
            aniversariantes = self.manager.get_aniversariantes_mes(self.mes)
            mes_nome = self.manager.get_nome_mes(self.mes)
        
        if not aniversariantes:
            self.status_updated.emit("Nenhum aniversariante encontrado.")
        else:
            self.status_updated.emit(f"{len(aniversariantes)} aniversariante(s) encontrado(s)!")
        
        self.fetch_completed.emit(aniversariantes, mes_nome)
