"""Create sandbox schema

Revision ID: a1b2c3d4e5f6
Revises: d781b2503468
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'd781b2503468'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sandbox schema
    op.execute('CREATE SCHEMA IF NOT EXISTS sandbox')


def downgrade() -> None:
    # Drop sandbox schema (this will also drop all tables in the schema)
    op.execute('DROP SCHEMA IF EXISTS sandbox CASCADE')

