"""Tipo do Check-in gravado no check-in (ADR 0001)

Revision ID: c4a1e9d7b2f3
Revises: 5e3b8f4d2a11
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4a1e9d7b2f3'
down_revision: Union[str, Sequence[str], None] = '5e3b8f4d2a11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ADD COLUMN direto: batch_alter_table recriaria a tabela e perderia uq_frequencia_member_day.
    # Banco novo ja nasce com a coluna (init_db/create_all).
    colunas = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("frequencia")}
    if "plano" not in colunas:
        op.add_column("frequencia", sa.Column("plano", sa.String(100), nullable=True))

    # Backfill: pagamento per-checkin do mesmo membro no mesmo dia; na falta, plano atual do membro.
    op.execute(
        """
        UPDATE frequencia
           SET plano = COALESCE(
               (SELECT p.tipo_transacao
                  FROM pagamentos p
                 WHERE p.member_id = frequencia.member_id
                   AND date(p.data_pagamento) = date(frequencia.checkin_datetime)
                   AND p.tipo_transacao IN ('Gympass', 'Totalpass', 'Diária', 'Diaria', 'Diária Boulder')
                 LIMIT 1),
               (SELECT m.plano FROM membros m WHERE m.id = frequencia.member_id)
           )
         WHERE plano IS NULL
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE frequencia DROP COLUMN plano")
