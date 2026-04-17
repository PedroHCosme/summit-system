"""Phase 4: moderate schema evolution

Revision ID: 5e3b8f4d2a11
Revises: b7156d140f0a
Create Date: 2026-04-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e3b8f4d2a11'
down_revision: Union[str, Sequence[str], None] = 'b7156d140f0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Referência canônica opcional de plano por FK (camada compatível com `plano` string).
    with op.batch_alter_table("membros") as batch_op:
        batch_op.add_column(sa.Column("plano_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_membros_plano_id_planos",
            "planos",
            ["plano_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_membros_plano_id", ["plano_id"], unique=False)

    # 2) Backfill plano_id a partir do nome legado `plano`.
    op.execute(
        """
        UPDATE membros
           SET plano_id = (
               SELECT p.id
                 FROM planos p
                WHERE lower(trim(p.nome)) = lower(trim(membros.plano))
                ORDER BY p.ativo DESC, p.id ASC
                LIMIT 1
           )
         WHERE plano_id IS NULL
           AND plano IS NOT NULL
           AND trim(plano) <> ''
        """
    )

    # 3) Índices / invariantes de check-in.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_frequencia_member_checkin_datetime
            ON frequencia (member_id, checkin_datetime)
        """
    )

    # Segurança para ambientes que já tenham dados duplicados:
    # mantém o primeiro check-in do dia e remove duplicados antes da constraint única.
    op.execute(
        """
        DELETE FROM frequencia
         WHERE id NOT IN (
               SELECT MIN(id)
                 FROM frequencia
                GROUP BY member_id, date(checkin_datetime)
         )
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_frequencia_member_day
            ON frequencia (member_id, date(checkin_datetime))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_frequencia_member_day")
    op.execute("DROP INDEX IF EXISTS ix_frequencia_member_checkin_datetime")

    with op.batch_alter_table("membros") as batch_op:
        batch_op.drop_index("ix_membros_plano_id")
        batch_op.drop_constraint("fk_membros_plano_id_planos", type_="foreignkey")
        batch_op.drop_column("plano_id")
