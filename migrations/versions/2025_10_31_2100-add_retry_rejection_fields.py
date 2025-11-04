"""Add retry_count and rejection_reason fields to content table

Revision ID: add_retry_rejection_fields
Revises:
Create Date: 2025-10-31 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_retry_rejection_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new fields for retry tracking and rejection feedback."""

    # Add retry_count column
    op.add_column('contents',
        sa.Column('retry_count', sa.Integer(), nullable=True, server_default='0')
    )

    # Add rejection_reason column
    op.add_column('contents',
        sa.Column('rejection_reason', sa.Text(), nullable=True)
    )

    # Update existing enum to include REJECTED and RETRYING statuses
    # Note: For PostgreSQL, you may need to use ALTER TYPE
    # For SQLite, this is handled by SQLAlchemy automatically

    # Set default value for existing rows
    op.execute("UPDATE contents SET retry_count = 0 WHERE retry_count IS NULL")


def downgrade() -> None:
    """Remove retry_count and rejection_reason fields."""

    op.drop_column('contents', 'rejection_reason')
    op.drop_column('contents', 'retry_count')
