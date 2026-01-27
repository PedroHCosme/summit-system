"""Worker para conexão com banco de dados."""

import os
import traceback
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
            print("[DatabaseConnection] Iniciando conexão...")
            from src.data.data_provider import USE_SQLITE, get_provider
            
            if USE_SQLITE:
                print("[DatabaseConnection] Modo: SQLite")
                self.status_updated.emit("Conectando ao banco de dados SQLite...")
            else:
                print("[DatabaseConnection] Modo: Google Sheets")
                self.status_updated.emit("Verificando credenciais...")
                
                # Verifica credenciais
                if not os.path.exists(CREDENTIALS_PATH):
                    msg = "Erro: Arquivo de credenciais não encontrado."
                    print(f"[DatabaseConnection] {msg}")
                    self.status_updated.emit(msg)
                    self.connection_completed.emit(False)
                    return
                
                self.status_updated.emit("Conectando ao Google Sheets...")
            
            # Tenta inicializar o provider
            print("[DatabaseConnection] Inicializando provider...")
            provider = get_provider()
            print(f"[DatabaseConnection] Provider criado: {type(provider).__name__}")

            if USE_SQLITE:
                self.status_updated.emit("Verificando e atualizando planos expirados...")
                print("[DatabaseConnection] Atualizando planos expirados...")
                # A instância do provider é o DatabaseManager
                updated_count = provider.update_expired_plans()
                if updated_count > 0:
                    msg = f"{updated_count} plano(s) atualizado(s) para INATIVO."
                    print(f"[DatabaseConnection] {msg}")
                    self.status_updated.emit(msg)
            
            print("[DatabaseConnection] ✓ Conexão estabelecida com sucesso!")
            self.status_updated.emit("Conexão estabelecida com sucesso!")
            self.connection_completed.emit(True)
            
        except Exception as e:
            error_msg = f"Erro na conexão: {e}"
            print(f"[DatabaseConnection] ❌ {error_msg}")
            print("[DatabaseConnection] Traceback completo:")
            traceback.print_exc()
            self.status_updated.emit(error_msg)
            self.connection_completed.emit(False)

