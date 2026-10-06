"""Worker de UI para sincronização — delega para pipeline de importação."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal

from src.config import CREDENTIALS_PATH, SPREADSHEET_ID
from src.data.legacy_sync_gateway import LegacySyncGateway
from src.services.sync_import_service import SyncImportService


class SyncWorker(QThread):
    """Worker para executar sincronização em background."""

    progress_updated = pyqtSignal(str, int)  # mensagem, progresso (0-100)
    sync_completed = pyqtSignal(dict)  # resultado da sincronização
    sync_failed = pyqtSignal(str)  # mensagem de erro

    SHEET_NAMES = [
        "Jan/25",
        "Fev/25",
        "Mar/25",
        "Abr/25",
        "Mai/25",
        "Jun/25",
        "Jul/25",
        "Ago/25",
        "Set/25",
        "Out/25",
        "Nov/25",
        "Dez/25",
    ]

    def __init__(self):
        super().__init__()
        self.gateway: Optional[LegacySyncGateway] = None
        self.sync_service: Optional[SyncImportService] = None

    def _emit_progress(self, message: str, progress: int) -> None:
        self.progress_updated.emit(message, progress)

    def run(self):
        """Executa a sincronização."""
        try:
            self.gateway = LegacySyncGateway(
                credentials_path=CREDENTIALS_PATH,
                spreadsheet_id=SPREADSHEET_ID,
            )
            self.sync_service = SyncImportService(
                gateway=self.gateway,
                sheet_names=self.SHEET_NAMES,
            )

            result = self.sync_service.execute(progress_callback=self._emit_progress)
            self.sync_completed.emit(result)
        except Exception as e:
            self.sync_failed.emit(f"❌ Erro durante sincronização: {str(e)}")
        finally:
            if self.gateway:
                self.gateway.close()
