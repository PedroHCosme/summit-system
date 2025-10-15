"""Worker para conexão com banco de dados."""

import os
from PyQt6.QtCore import QThread, pyqtSignal

from src.config import CREDENTIALS_PATH


class DatabaseConnectionWorker(QThread):
    """Thread para conexão inicial com a fonte de dados."""
    
    # Sinais
    status_updated = pyqtSignal(str)
    connection_completed = pyqtSignal(bool)
    
    def __init__(self):
        """Inicializa o worker."""
        super().__init__()
    
    def run(self):
        """Executa a conexão com a fonte de dados."""
        try:
            from src.data.data_provider import USE_SQLITE, get_provider
            
            if USE_SQLITE:
                self.status_updated.emit("Conectando ao banco de dados SQLite...")
            else:
                self.status_updated.emit("Verificando credenciais...")
                
                # Verifica credenciais
                if not os.path.exists(CREDENTIALS_PATH):
                    self.status_updated.emit("Erro: Arquivo de credenciais não encontrado.")
                    self.connection_completed.emit(False)
                    return
                
                self.status_updated.emit("Conectando ao Google Sheets...")
            
            # Tenta inicializar o provider
            provider = get_provider()

            if USE_SQLITE:
                self.status_updated.emit("Verificando e atualizando planos expirados...")
                # A instância do provider é o DatabaseManager
                updated_count = provider.update_expired_plans()
                if updated_count > 0:
                    self.status_updated.emit(f"{updated_count} plano(s) atualizado(s) para INATIVO.")
            
            self.status_updated.emit("Conexão estabelecida com sucesso!")
            self.connection_completed.emit(True)
            
        except Exception as e:
            self.status_updated.emit(f"Erro na conexão: {e}")
            self.connection_completed.emit(False)
