"""add content generation preference to clients

Revision ID: add_content_generation_preference
Revises: add_placid_template_id
Create Date: 2025-11-04 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_content_generation_preference'
down_revision = 'add_placid_template_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add content generation preference field to clients table
    op.add_column('clients', sa.Column('content_generation_preference', sa.String(), nullable=True))

    # Set default value for existing clients
    op.execute("UPDATE clients SET content_generation_preference = 'own_media' WHERE content_generation_preference IS NULL")


def downgrade() -> None:
    # Remove content generation preference field
    op.drop_column('clients', 'content_generation_preference')
