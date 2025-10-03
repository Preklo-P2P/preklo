"""Add only terms agreement fields to user table

Revision ID: d781b2503468
Revises: 0962623b6303
Create Date: 2025-10-03 13:11:19.111863

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd781b2503468'
down_revision: Union[str, None] = 'dd1b67c2ded2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add terms agreement fields to users table
    op.add_column('users', sa.Column('terms_agreed', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('terms_agreed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove terms agreement fields from users table
    op.drop_column('users', 'terms_agreed_at')
    op.drop_column('users', 'terms_agreed')
