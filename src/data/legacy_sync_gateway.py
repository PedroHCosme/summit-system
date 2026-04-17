"""Adapter legado para sincronização com Google Sheets + infraestrutura local."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.data.database_manager import DatabaseManager
from src.data.google_sheets_service import GoogleSheetsService


class LegacySyncGateway:
    """
    Adaptador de integração legada para sincronização.

    Responsabilidades:
    - Conectar Google Sheets (read-only)
    - Conectar infraestrutura legada de banco (DatabaseManager)
    - Expor leitura de abas sem acoplar regras de negócio
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service: Optional[GoogleSheetsService] = None
        self.db_manager: Optional[DatabaseManager] = None

    # ------------------------------------------------------------------
    # Infra setup
    # ------------------------------------------------------------------

    def connect_google_sheets(self) -> bool:
        self.sheets_service = GoogleSheetsService(self.credentials_path)
        return self.sheets_service.authenticate()

    def connect_database(self) -> bool:
        self.db_manager = DatabaseManager()
        return self.db_manager.connect()

    def ensure_database_schema(self) -> bool:
        if not self.db_manager:
            return False
        return self.db_manager.create_tables()

    def optimize_database(self) -> Dict[str, Any]:
        if not self.db_manager:
            raise RuntimeError("DatabaseManager não inicializado")
        return self.db_manager.optimize_and_reindex()

    # ------------------------------------------------------------------
    # Data access
    # ------------------------------------------------------------------

    def read_sheet(self, sheet_name: str, range_name: str = "A:CZ") -> List[list]:
        if not self.sheets_service:
            raise RuntimeError("GoogleSheetsService não inicializado")
        return self.sheets_service.read_spreadsheet(
            self.spreadsheet_id, range_name, sheet_name
        )

    def close(self) -> None:
        if self.db_manager:
            self.db_manager.close()
            self.db_manager = None
