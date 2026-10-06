"""Adapter legado para sincronização com Google Sheets + infraestrutura local."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.data.google_sheets_service import GoogleSheetsService
from src.data.maintenance import create_tables, optimize_and_reindex


class LegacySyncGateway:
    """
    Adaptador de integração legada para sincronização.

    Responsabilidades:
    - Conectar Google Sheets (read-only)
    - Conectar infraestrutura legada de banco
    - Expor leitura de abas sem acoplar regras de negócio
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str) -> None:
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.sheets_service: Optional[GoogleSheetsService] = None
        self._db_path: Optional[str] = None

    # ------------------------------------------------------------------
    # Infra setup
    # ------------------------------------------------------------------

    def connect_google_sheets(self) -> bool:
        self.sheets_service = GoogleSheetsService(self.credentials_path)
        return self.sheets_service.authenticate()

    def connect_database(self) -> bool:
        from src.config import DB_FILENAME

        project_root = Path(__file__).parent.parent.parent
        db_path = os.path.join(project_root, DB_FILENAME)
        try:
            sqlite3.connect(db_path, check_same_thread=False, timeout=60).close()
        except sqlite3.Error:
            return False
        self._db_path = db_path
        return True

    def ensure_database_schema(self) -> bool:
        if not self._db_path:
            return False
        return create_tables(self._db_path)

    def optimize_database(self) -> Dict[str, Any]:
        if not self._db_path:
            raise RuntimeError("Banco de dados não conectado")
        return optimize_and_reindex(self._db_path)

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
        self._db_path = None
