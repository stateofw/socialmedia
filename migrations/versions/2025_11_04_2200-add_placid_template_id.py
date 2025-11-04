"""add placid template id to clients

Revision ID: add_placid_template_id
Revises: b377d3f5d4af
Create Date: 2025-11-04 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_placid_template_id'
down_revision = 'b377d3f5d4af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Placid template ID field to clients table
    op.add_column('clients', sa.Column('placid_template_id', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove Placid template ID field
    op.drop_column('clients', 'placid_template_id')
