"""add_client_portal_auth

Revision ID: 764054baedb3
Revises: add_publer_multiworkspace
Create Date: 2025-11-02 20:00:01.673240+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '764054baedb3'
down_revision = 'add_publer_multiworkspace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add client portal authentication fields
    op.add_column('clients', sa.Column('password_hash', sa.String(), nullable=True))
    op.add_column('clients', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove client portal authentication fields
    op.drop_column('clients', 'last_login')
    op.drop_column('clients', 'password_hash')
