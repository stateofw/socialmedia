"""add publer multi-workspace support

Revision ID: add_publer_multiworkspace
Revises: add_prd_fields
Create Date: 2025-11-02 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_publer_multiworkspace'
down_revision = 'add_prd_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Publer multi-workspace fields to clients table
    op.add_column('clients', sa.Column('publer_workspace_id', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('publer_api_key', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove Publer multi-workspace fields
    op.drop_column('clients', 'publer_api_key')
    op.drop_column('clients', 'publer_workspace_id')
