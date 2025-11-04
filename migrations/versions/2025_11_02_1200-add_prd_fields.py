"""add PRD fields to client model

Revision ID: add_prd_fields
Revises: add_retry_rejection_fields
Create Date: 2025-11-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_prd_fields'
down_revision = 'add_retry_rejection_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new fields to clients table
    op.add_column('clients', sa.Column('tone_preference', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('promotions_offers', sa.Text(), nullable=True))
    op.add_column('clients', sa.Column('off_limits_topics', sa.JSON(), nullable=True))
    op.add_column('clients', sa.Column('reuse_media', sa.Boolean(), nullable=True, server_default='true'))
    op.add_column('clients', sa.Column('media_folder_url', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('primary_contact_name', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('primary_contact_email', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('primary_contact_phone', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('backup_contact_name', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('backup_contact_email', sa.String(), nullable=True))

    # Set default for tone_preference on existing rows
    op.execute("UPDATE clients SET tone_preference = 'professional' WHERE tone_preference IS NULL")


def downgrade() -> None:
    # Remove added columns
    op.drop_column('clients', 'backup_contact_email')
    op.drop_column('clients', 'backup_contact_name')
    op.drop_column('clients', 'primary_contact_phone')
    op.drop_column('clients', 'primary_contact_email')
    op.drop_column('clients', 'primary_contact_name')
    op.drop_column('clients', 'media_folder_url')
    op.drop_column('clients', 'reuse_media')
    op.drop_column('clients', 'off_limits_topics')
    op.drop_column('clients', 'promotions_offers')
    op.drop_column('clients', 'tone_preference')
