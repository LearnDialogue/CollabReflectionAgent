"""Add evaluation_data JSONB column to sessions table

Revision ID: 003
Revises: 002
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('evaluation_data', postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('sessions', 'evaluation_data')
