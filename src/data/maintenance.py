"""Manutenção do banco de dados SQLite (índices, VACUUM, ANALYZE)."""

import os
import sqlite3
from typing import Any, Dict


def optimize_and_reindex(db_path: str) -> Dict[str, Any]:
    """Cria índices principais e executa ANALYZE/PRAGMA optimize no banco em db_path."""
    connection = sqlite3.connect(db_path, check_same_thread=False, timeout=60)
    stats = {
        "indices_processed": 0,
        "vacuum_executed": False,
        "analyze_executed": False,
        "pragma_optimize_executed": False,
    }

    try:
        cursor = connection.cursor()
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_membros_nome ON membros(nome)",
            "CREATE INDEX IF NOT EXISTS idx_membros_plano ON membros(plano)",
            "CREATE INDEX IF NOT EXISTS idx_membros_estado_plano ON membros(estado_plano)",
            "CREATE INDEX IF NOT EXISTS idx_membros_vencimento ON membros(vencimento_plano)",
            "CREATE INDEX IF NOT EXISTS idx_frequencia_member_id ON frequencia(member_id)",
            "CREATE INDEX IF NOT EXISTS idx_frequencia_datetime ON frequencia(checkin_datetime)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_frequencia_unique ON frequencia(member_id, DATE(checkin_datetime))",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_member_id ON pagamentos(member_id)",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_data ON pagamentos(data_pagamento)",
            "CREATE INDEX IF NOT EXISTS idx_pagamentos_tipo ON pagamentos(tipo_transacao)",
        ]
        for statement in index_statements:
            cursor.execute(statement)
            stats["indices_processed"] += 1
        cursor.close()

        # Garante que ANALYZE rode fora de uma transação ativa
        connection.commit()

        # VACUUM omitido: causa erro "database is locked" se houver outras conexões ativas (ex: UI)
        try:
            connection.execute("ANALYZE")
            stats["analyze_executed"] = True
        except sqlite3.Error as exc:
            print(f"Aviso: ANALYZE falhou: {exc}")

        try:
            connection.execute("PRAGMA optimize")
            stats["pragma_optimize_executed"] = True
        except sqlite3.Error as exc:
            print(f"Aviso: PRAGMA optimize falhou: {exc}")

        connection.commit()
        return stats
    finally:
        connection.close()
