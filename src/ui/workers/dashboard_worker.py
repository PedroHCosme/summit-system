"""Worker para dados do dashboard."""

from PyQt6.QtCore import QThread, pyqtSignal


class DashboardWorker(QThread):
    """Thread para buscar dados do dashboard."""
    
    dashboard_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
    
    def run(self):
        """Executa a busca de dados do dashboard."""
        try:
            from src.data.data_provider import get_checkins_today, get_checkins_today_list
            
            checkins_count = get_checkins_today()
            checkins_today = get_checkins_today_list()
            
            dashboard_data = {
                "checkins_today": checkins_count,
                "last_checkins": checkins_today  # Agora são todos os check-ins de hoje
            }
            self.dashboard_updated.emit(dashboard_data)
            
        except Exception as e:
            self.error_occurred.emit(f"Erro ao atualizar dashboard: {e}")
