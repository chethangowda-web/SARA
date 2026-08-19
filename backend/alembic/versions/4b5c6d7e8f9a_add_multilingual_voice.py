"""add_multilingual_voice

Revision ID: 4b5c6d7e8f9a
Revises: 3aec9843a868
Create Date: 2026-08-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b5c6d7e8f9a'
down_revision: Union[str, None] = '3aec9843a868'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add preferred_language to users table
    op.add_column('users', sa.Column('preferred_language', sa.String(length=10), server_default='en', nullable=False))

    # 2. Add language columns to grievances table
    op.add_column('grievances', sa.Column('original_language', sa.String(length=10), server_default='en', nullable=False))
    op.add_column('grievances', sa.Column('original_title', sa.String(length=255), nullable=True))
    op.add_column('grievances', sa.Column('original_description', sa.Text(), nullable=True))
    op.add_column('grievances', sa.Column('normalized_title', sa.String(length=255), nullable=True))
    op.add_column('grievances', sa.Column('normalized_description', sa.Text(), nullable=True))

    # Migrate existing grievances data: original = current, normalized = current
    op.execute("UPDATE grievances SET original_title = title, original_description = description, normalized_title = title, normalized_description = description")

    # 3. Add language columns to grievance_comments table
    op.add_column('grievance_comments', sa.Column('original_language', sa.String(length=10), server_default='en', nullable=False))
    op.add_column('grievance_comments', sa.Column('normalized_comment', sa.Text(), nullable=True))

    # Migrate existing comments data: normalized = comment
    op.execute("UPDATE grievance_comments SET normalized_comment = comment")


def downgrade() -> None:
    # Remove columns
    op.drop_column('grievance_comments', 'normalized_comment')
    op.drop_column('grievance_comments', 'original_language')

    op.drop_column('grievances', 'normalized_description')
    op.drop_column('grievances', 'normalized_title')
    op.drop_column('grievances', 'original_description')
    op.drop_column('grievances', 'original_title')
    op.drop_column('grievances', 'original_language')

    op.drop_column('users', 'preferred_language')
