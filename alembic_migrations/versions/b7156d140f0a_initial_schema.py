"""Initial schema

Revision ID: b7156d140f0a
Revises: 
Create Date: 2026-03-14 19:57:58.870743

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7156d140f0a'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # A migração inicial não fará alterações destrutivas (drop_index / alter_column)
    # pois a criação das tabelas continua sendo gerida pelo Base.metadata.create_all
    # ou pelo DatabaseManager na inicialização.
    pass


def downgrade() -> None:
    pass
