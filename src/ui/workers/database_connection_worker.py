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
    
    def _run_migrations(self):
        """Executa migrações do banco usando Alembic."""
        try:
            import os
            from alembic import command
            from alembic.config import Config
            
            print("[DatabaseConnection] Executando migrações Alembic...")
            self.status_updated.emit("Executando migrações do banco de dados (Alembic)...")
            
            # Ponto de entrada p/ alembic.ini na raiz do projeto
            project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            alembic_ini_path = os.path.join(project_dir, "alembic.ini")
            
            alembic_cfg = Config(alembic_ini_path)
            # Definir o diretório raiz para o alembic rodar corretamente
            alembic_cfg.set_main_option("script_location", os.path.join(project_dir, "alembic_migrations"))
            
            print("[DatabaseConnection] Upgrading to head...")
            command.upgrade(alembic_cfg, "head")
            
            print("[DatabaseConnection] ✓ Migrações Alembic executadas com sucesso")
            return True
        except Exception as e:
            print(f"[DatabaseConnection] ⚠ Erro nas migrações: {e}")
            traceback.print_exc()
            # Não bloqueia - continua mesmo com erro nas migrações
            return False
    
    def run(self):
        """Executa a conexão com a fonte de dados."""
        try:
            print("[DatabaseConnection] Iniciando conexão...")
            from src.data.data_provider import USE_SQLITE, get_provider
            
            if USE_SQLITE:
                print("[DatabaseConnection] Modo: SQLite")
                self.status_updated.emit("Conectando ao banco de dados SQLite...")
                
                # IMPORTANTE: Rodar migrações ANTES de usar SQLAlchemy
                # Isso garante que todas as colunas existem antes das queries
                self._run_migrations()
                
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
            
            # Tenta inicializar o provider (agora com banco migrado)
            print("[DatabaseConnection] Inicializando provider...")
            provider = get_provider()
            print(f"[DatabaseConnection] Provider criado: {type(provider).__name__}")

            if USE_SQLITE:
                self.status_updated.emit("Verificando e atualizando planos expirados...")
                print("[DatabaseConnection] Atualizando planos expirados...")
                updated_count = provider.update_expired_plans()
                if updated_count > 0:
                    from src.core.plan_status import INATIVO
                    msg = f"{updated_count} plano(s) atualizado(s) para {INATIVO}."
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


