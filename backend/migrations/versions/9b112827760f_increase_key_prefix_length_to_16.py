"""Increase key_prefix length to 16

Revision ID: 9b112827760f
Revises: b2c3d4e5f6a7
Create Date: 2025-11-07 11:15:00.236018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b112827760f'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'api_keys',
        'key_prefix',
        existing_type=sa.String(length=8),
        type_=sa.String(length=16),
        schema='sandbox'
    )


def downgrade() -> None:
    op.alter_column(
        'api_keys',
        'key_prefix',
        existing_type=sa.String(length=16),
        type_=sa.String(length=8),
        schema='sandbox'
    )
