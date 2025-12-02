"""Create sandbox-specific tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create test_accounts table
    op.create_table(
        'test_accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sandbox_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=32), nullable=False),
        sa.Column('wallet_address', sa.String(length=66), nullable=False),
        sa.Column('usdc_balance', sa.Numeric(precision=20, scale=8), default=0.0),
        sa.Column('apt_balance', sa.Numeric(precision=20, scale=8), default=0.0),
        sa.Column('original_usdc_balance', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('original_apt_balance', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('currency_type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        schema='sandbox'
    )
    op.create_index('ix_test_accounts_sandbox_user_id', 'test_accounts', ['sandbox_user_id'], schema='sandbox')
    op.create_index('ix_test_accounts_username', 'test_accounts', ['username'], unique=False, schema='sandbox')
    op.create_index('ix_test_accounts_wallet_address', 'test_accounts', ['wallet_address'], unique=False, schema='sandbox')
    
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sandbox_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('key_hash', sa.String(length=255), nullable=False),
        sa.Column('key_prefix', sa.String(length=8), nullable=False),  # First 8 chars for display
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        schema='sandbox'
    )
    op.create_index('ix_api_keys_sandbox_user_id', 'api_keys', ['sandbox_user_id'], schema='sandbox')
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True, schema='sandbox')
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'], schema='sandbox')
    
    # Create webhook_subscriptions table
    op.create_table(
        'webhook_subscriptions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sandbox_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(length=512), nullable=False),
        sa.Column('events', JSON, nullable=False),  # List of event types
        sa.Column('secret', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        schema='sandbox'
    )
    op.create_index('ix_webhook_subscriptions_sandbox_user_id', 'webhook_subscriptions', ['sandbox_user_id'], schema='sandbox')
    op.create_index('ix_webhook_subscriptions_is_active', 'webhook_subscriptions', ['is_active'], schema='sandbox')
    
    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('subscription_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', JSON, nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),  # pending, delivered, failed
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempts', sa.Integer(), default=0, nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='sandbox'
    )
    op.create_index('ix_webhook_deliveries_subscription_id', 'webhook_deliveries', ['subscription_id'], schema='sandbox')
    op.create_index('ix_webhook_deliveries_status', 'webhook_deliveries', ['status'], schema='sandbox')
    op.create_index('ix_webhook_deliveries_created_at', 'webhook_deliveries', ['created_at'], schema='sandbox')
    op.create_foreign_key(
        'fk_webhook_deliveries_subscription',
        'webhook_deliveries', 'webhook_subscriptions',
        ['subscription_id'], ['id'],
        source_schema='sandbox', referent_schema='sandbox'
    )
    
    # Create analytics table
    op.create_table(
        'analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('sandbox_user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),  # signup, api_call, transaction, etc.
        sa.Column('endpoint', sa.String(length=255), nullable=True),  # API endpoint called
        sa.Column('event_metadata', JSON, nullable=True),  # Additional event data
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        schema='sandbox'
    )
    op.create_index('ix_analytics_sandbox_user_id', 'analytics', ['sandbox_user_id'], schema='sandbox')
    op.create_index('ix_analytics_event_type', 'analytics', ['event_type'], schema='sandbox')
    op.create_index('ix_analytics_created_at', 'analytics', ['created_at'], schema='sandbox')


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('analytics', schema='sandbox')
    op.drop_table('webhook_deliveries', schema='sandbox')
    op.drop_table('webhook_subscriptions', schema='sandbox')
    op.drop_table('api_keys', schema='sandbox')
    op.drop_table('test_accounts', schema='sandbox')

