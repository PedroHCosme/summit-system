"""Utilitários para migrações automáticas do banco de dados.

Este módulo concentra as correções que antes dependiam de scripts
manuais (ex: add_email_column, fix_payment_datetime, fix_birth_dates, etc).
A ideia é que, ao sincronizar com o Google Sheets, todas as migrações
necessárias sejam aplicadas automaticamente, reduzindo a carga para o
usuário final.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple
from src.data.database_manager import DatabaseManager
from src.data.migration_tasks.backfill_payments import backfill_plan_payments


class DatabaseMigrator:
    """Aplica migrações e correções idempotentes ao banco."""

    def __init__(self, db_manager: DatabaseManager):
        if not db_manager.connection:
            raise ValueError("DatabaseMigrator requer uma conexão ativa")
        self.db = db_manager
        self.conn = db_manager.connection

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def run_all(self) -> None:
        """Executa todas as migrações de forma idempotente."""
        steps = [
            # IMPORTANTE: ensure_all_member_columns deve ser primeiro!
            # Garante que todas as colunas do modelo existem antes de qualquer query
            ("Garantindo todas as colunas da tabela membros", self.ensure_all_member_columns),
            ("Garantindo coluna de e-mail", self.ensure_email_column),
            ("Garantindo colunas de treino", self.ensure_training_columns),
            ("Garantindo coluna de profissão", self.ensure_profession_column),
            ("Garantindo coluna de contato de emergência", self.ensure_emergency_contact_column),
            ("Garantindo tabela/colunas de pagamentos", self.ensure_payments_schema),
            ("Ajustando formato das datas de pagamento", self.ensure_payment_datetime),
            ("Ajustando timestamps sem hora", self.ensure_payment_times),
            ("Removendo datas de nascimento inválidas", self.fix_invalid_birth_dates),
            ("Recalculando estados de planos", self.recalculate_plan_states),
            ("Removendo check-ins duplicados", self.remove_duplicate_checkins),
            ("Criando índices de performance", self.ensure_indexes),
            ("Garantindo coluna de créditos de voucher", self.ensure_voucher_credits_column),
            ("Garantindo colunas quota na tabela planos", self.ensure_quota_plan_columns),
            ("Garantindo existência de todos os planos base", self.seed_all_plans),
            ("Reprocessando pagamentos recorrentes históricos", self.backfill_plan_payments),
        ]

        for description, func in steps:
            try:
                func()
            except Exception as exc:  # pragma: no cover - apenas erro inesperado
                raise RuntimeError(f"Erro durante '{description}': {exc}") from exc

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _table_exists(self, table_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        exists = cursor.fetchone() is not None
        cursor.close()
        return exists

    def _get_table_info(self, table_name: str) -> Dict[str, Dict[str, object]]:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        cursor.close()
        info: Dict[str, Dict[str, object]] = {}
        for cid, name, col_type, notnull, default_value, pk in rows:
            info[name] = {
                "cid": cid,
                "type": col_type.upper() if col_type else "",
                "notnull": bool(notnull),
                "default": default_value,
                "pk": bool(pk),
            }
        return info

    def _execute_many(self, statements: List[str]) -> None:
        cursor = self.conn.cursor()
        try:
            for statement in statements:
                cursor.execute(statement)
        finally:
            cursor.close()
        self.conn.commit()

    # ------------------------------------------------------------------
    # Migrações individuais
    # ------------------------------------------------------------------
    
    def ensure_all_member_columns(self) -> None:
        """Garante que todas as colunas do modelo Membro existem na tabela.
        
        Esta é a PRIMEIRA migração e deve rodar antes de qualquer query
        SQLAlchemy para evitar erros de 'column not found'.
        """
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        
        # Lista de todas as colunas que devem existir no modelo Membro
        # (nome_coluna, tipo_sql, valor_default)
        required_columns = [
            ('nome', 'TEXT', None),
            ('plano', 'TEXT', None),
            ('vencimento_plano', 'TEXT', None),
            ('estado_plano', 'TEXT', None),
            ('data_nascimento', 'TEXT', None),
            ('whatsapp', 'TEXT', None),
            ('genero', 'TEXT', None),
            ('email', 'TEXT', None),
            ('apelido', 'TEXT', None),
            ('profissao', 'TEXT', "''"),
            ('contato_emergencia', 'TEXT', "''"),
            ('frequencia', 'TEXT', None),
            ('observacoes', 'TEXT', None),
            ('calcado', 'TEXT', None),
            ('voucher_credits', 'INTEGER', '0'),
            ('treina', 'TEXT', "'Não'"),
            ('vencimento_treino', 'TEXT', None),
            ('created_at', 'TIMESTAMP', 'CURRENT_TIMESTAMP'),
            ('updated_at', 'TIMESTAMP', 'CURRENT_TIMESTAMP'),
        ]
        
        missing_columns = []
        for col_name, col_type, default in required_columns:
            if col_name not in info:
                if default is not None:
                    missing_columns.append(
                        f"ALTER TABLE membros ADD COLUMN {col_name} {col_type} DEFAULT {default}"
                    )
                else:
                    missing_columns.append(
                        f"ALTER TABLE membros ADD COLUMN {col_name} {col_type}"
                    )
        
        if missing_columns:
            print(f"[migrations] Adicionando {len(missing_columns)} coluna(s) faltando em membros...")
            self._execute_many(missing_columns)

    def ensure_email_column(self) -> None:
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        if 'email' in info:
            return

        cursor = self.conn.cursor()
        cursor.execute("ALTER TABLE membros ADD COLUMN email TEXT")
        cursor.close()
        self.conn.commit()
    
    def ensure_profession_column(self) -> None:
        """Adiciona coluna de profissão se não existir."""
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        if 'profissao' in info:
            return

        cursor = self.conn.cursor()
        cursor.execute("ALTER TABLE membros ADD COLUMN profissao TEXT DEFAULT ''")
        cursor.close()
        self.conn.commit()

    def ensure_emergency_contact_column(self) -> None:
        """Adiciona coluna de contato de emergência se não existir."""
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        if 'contato_emergencia' in info:
            return

        cursor = self.conn.cursor()
        cursor.execute("ALTER TABLE membros ADD COLUMN contato_emergencia TEXT DEFAULT ''")
        cursor.close()
        self.conn.commit()

    def ensure_training_columns(self) -> None:
        """Adiciona colunas para controle de treino como serviço adicional."""
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        missing_columns = []
        
        # treina: 'Sim' ou 'Não' (default 'Não')
        if 'treina' not in info:
            missing_columns.append("ALTER TABLE membros ADD COLUMN treina TEXT DEFAULT 'Não'")
        
        # vencimento_treino: data de validade do treino (formato YYYY-MM-DD)
        if 'vencimento_treino' not in info:
            missing_columns.append("ALTER TABLE membros ADD COLUMN vencimento_treino TEXT")
        
        if missing_columns:
            self._execute_many(missing_columns)
            
            # Atualizar membros existentes para "Não treina" se o campo for NULL
            cursor = self.conn.cursor()
            cursor.execute("UPDATE membros SET treina = 'Não' WHERE treina IS NULL")
            cursor.close()
            self.conn.commit()

    def ensure_voucher_credits_column(self) -> None:
        """Adiciona coluna de créditos de voucher se não existir."""
        if not self._table_exists('membros'):
            return

        info = self._get_table_info('membros')
        if 'voucher_credits' in info:
            return

        cursor = self.conn.cursor()
        cursor.execute("ALTER TABLE membros ADD COLUMN voucher_credits INTEGER DEFAULT 0")
        cursor.close()
        self.conn.commit()

    def ensure_quota_plan_columns(self) -> None:
        """Adiciona colunas is_quota e quota_amount à tabela planos se não existirem."""
        if not self._table_exists('planos'):
            return

        info = self._get_table_info('planos')
        missing_columns = []
        
        if 'is_quota' not in info:
            missing_columns.append("ALTER TABLE planos ADD COLUMN is_quota INTEGER DEFAULT 0")
        
        if 'quota_amount' not in info:
            missing_columns.append("ALTER TABLE planos ADD COLUMN quota_amount INTEGER DEFAULT 0")
        
        if missing_columns:
            self._execute_many(missing_columns)

    def seed_all_plans(self) -> None:
        """Garante que todos os planos base existem no banco.
        
        Esta migração é idempotente - apenas CRIA planos que não existem.
        Planos existentes NÃO são modificados (preserva configurações do usuário).
        """
        if not self._table_exists('planos'):
            return

        cursor = self.conn.cursor()
        
        # Lista completa de planos base
        # (nome, preco, valor_por_checkin, requer_vencimento, is_quota, quota_amount)
        base_plans = [
            # Planos de tempo (mensalidades)
            ('Mensal', 190.0, 0.0, True, False, 0),
            ('Mens. c/ Treino', 280.0, 0.0, True, False, 0),
            ('Trimestral', 500.0, 0.0, True, False, 0),
            ('Semestral', 950.0, 0.0, True, False, 0),
            ('Anual', 1900.0, 0.0, True, False, 0),
            
            # Planos por check-in
            ('Diária', 0.0, 35.0, False, False, 0),
            ('Gympass', 0.0, 15.0, False, False, 0),
            ('Totalpass', 0.0, 15.0, False, False, 0),
            
            # Planos especiais
            ('Cortesia', 0.0, 0.0, False, False, 0),
            ('Escolinha 1x', 0.0, 0.0, True, False, 0),
            ('Escolinha 2x', 0.0, 0.0, True, False, 0),
            
            # Planos de quota (voucher)
            ('Voucher', 0.0, 0.0, False, True, 0),
            ('Pacote 10', 200.0, 0.0, False, True, 10),
        ]
        
        created_count = 0
        for nome, preco, valor_checkin, req_venc, is_quota, quota_amt in base_plans:
            # Verifica se já existe
            cursor.execute("SELECT id FROM planos WHERE nome = ?", (nome,))
            row = cursor.fetchone()
            
            if not row:
                # Plano não existe - criar
                cursor.execute("""
                    INSERT INTO planos (nome, preco, valor_por_checkin, requer_vencimento, ativo, is_quota, quota_amount)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (nome, preco, valor_checkin, req_venc, is_quota, quota_amt))
                created_count += 1
        
        cursor.close()
        self.conn.commit()
        
        if created_count > 0:
            print(f"[migrations] {created_count} planos base criados na tabela planos")


    def ensure_payments_schema(self) -> None:
        cursor = self.conn.cursor()

        if not self._table_exists('pagamentos'):
            cursor.execute(
                """
                CREATE TABLE pagamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    member_id INTEGER NOT NULL,
                    data_pagamento DATETIME NOT NULL,
                    tipo_transacao TEXT NOT NULL,
                    descricao TEXT,
                    valor REAL NOT NULL,
                    metodo_pagamento TEXT,
                    nova_data_vencimento TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (valor >= 0),
                    FOREIGN KEY (member_id) REFERENCES membros(id) ON DELETE CASCADE
                )
                """
            )
            cursor.close()
            self.conn.commit()
            return

        cursor.close()

        info = self._get_table_info('pagamentos')
        missing_columns = []
        if 'metodo_pagamento' not in info:
            missing_columns.append("ALTER TABLE pagamentos ADD COLUMN metodo_pagamento TEXT")
        if 'nova_data_vencimento' not in info:
            missing_columns.append("ALTER TABLE pagamentos ADD COLUMN nova_data_vencimento TEXT")
        if 'created_at' not in info:
            missing_columns.append(
                "ALTER TABLE pagamentos ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )
        if missing_columns:
            self._execute_many(missing_columns)

    def ensure_payment_datetime(self) -> None:
        info = self._get_table_info('pagamentos')
        if not info:
            return

        column = info.get('data_pagamento')
        if not column:
            raise RuntimeError("Tabela 'pagamentos' sem coluna data_pagamento")

        if column['type'] in {'DATETIME', 'TIMESTAMP'}:
            return

        # Migração: recriar tabela com schema atualizado
        cursor = self.conn.cursor()

        metodo_exists = 'metodo_pagamento' in info
        nova_venc_exists = 'nova_data_vencimento' in info
        created_at_exists = 'created_at' in info

        cursor.execute(
            """
            CREATE TABLE pagamentos_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                data_pagamento DATETIME NOT NULL,
                tipo_transacao TEXT NOT NULL,
                descricao TEXT,
                valor REAL NOT NULL,
                metodo_pagamento TEXT,
                nova_data_vencimento TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (valor >= 0),
                FOREIGN KEY (member_id) REFERENCES membros(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            f"""
            INSERT INTO pagamentos_new (
                id,
                member_id,
                data_pagamento,
                tipo_transacao,
                descricao,
                valor,
                metodo_pagamento,
                nova_data_vencimento,
                created_at
            )
            SELECT
                id,
                member_id,
                data_pagamento,
                tipo_transacao,
                descricao,
                valor,
                {{metodo}},
                {{nova_venc}},
                {{created}}
            FROM pagamentos
            """.replace('{{metodo}}', 'metodo_pagamento' if metodo_exists else 'NULL')
                   .replace('{{nova_venc}}', 'nova_data_vencimento' if nova_venc_exists else 'NULL')
                   .replace('{{created}}', 'created_at' if created_at_exists else 'CURRENT_TIMESTAMP')
        )

        cursor.execute("DROP TABLE pagamentos")
        cursor.execute("ALTER TABLE pagamentos_new RENAME TO pagamentos")

        for name, columns in [
            ('idx_pagamentos_member_id', 'member_id'),
            ('idx_pagamentos_data', 'data_pagamento'),
            ('idx_pagamentos_tipo', 'tipo_transacao'),
        ]:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {name} ON pagamentos({columns})"
            )

        cursor.close()
        self.conn.commit()

    def ensure_payment_times(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE pagamentos
            SET data_pagamento = data_pagamento || ' 12:00:00'
            WHERE length(data_pagamento) = 10
            """
        )
        updated = cursor.rowcount
        cursor.close()
        if updated:
            self.conn.commit()

    def fix_invalid_birth_dates(self) -> None:
        if not self._table_exists('membros'):
            return
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE membros
            SET data_nascimento = ''
            WHERE data_nascimento IN ('----------', '---', '--', 'N/A', 'n/a', '#N/A')
            """
        )
        changed = cursor.rowcount
        cursor.close()
        if changed:
            self.conn.commit()

    def recalculate_plan_states(self) -> None:
        if not self._table_exists('membros'):
            return

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, vencimento_plano, estado_plano
            FROM membros
            WHERE vencimento_plano IS NOT NULL AND vencimento_plano != ''
            """
        )
        rows = cursor.fetchall()

        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        updates: List[Tuple[str, int]] = []

        for row in rows:
            vencimento = row[1]
            parsed = self.db._parse_date_multi_format(vencimento)  # type: ignore[attr-defined]
            if not parsed:
                continue
            parsed = parsed.replace(hour=0, minute=0, second=0, microsecond=0)
            estado_correto = 'INATIVO' if parsed < hoje else 'ATIVO'
            if estado_correto != row[2]:
                updates.append((estado_correto, row[0]))

        cursor.close()

        if updates:
            cursor_update = self.conn.cursor()
            cursor_update.executemany(
                "UPDATE membros SET estado_plano = ? WHERE id = ?",
                updates
            )
            cursor_update.close()
            self.conn.commit()

    def remove_duplicate_checkins(self) -> None:
        if not self._table_exists('frequencia'):
            return

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT member_id, DATE(checkin_datetime) as dia, COUNT(*) as total
            FROM frequencia
            GROUP BY member_id, DATE(checkin_datetime)
            HAVING total > 1
            """
        )
        duplicates = cursor.fetchall()

        removed = 0
        for member_id, dia, _ in duplicates:
            cursor.execute(
                """
                SELECT id
                FROM frequencia
                WHERE member_id = ? AND DATE(checkin_datetime) = ?
                ORDER BY checkin_datetime ASC, id ASC
                """,
                (member_id, dia)
            )
            ids = [row[0] for row in cursor.fetchall()]
            for checkin_id in ids[1:]:
                cursor.execute("DELETE FROM frequencia WHERE id = ?", (checkin_id,))
                removed += 1

        cursor.close()
        if removed:
            self.conn.commit()

    def ensure_indexes(self) -> None:
        statements = [
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
        self._execute_many(statements)

    def backfill_plan_payments(self) -> None:
        result = backfill_plan_payments(self.db)
        created = result.get("pagamentos_registrados", 0)
        processed = result.get("membros_processados", 0)
        if created:
            print(
                f"[migrations] Pagamentos retroativos criados: {created} (membros processados: {processed})"
            )


__all__ = ["DatabaseMigrator"]