"""add_assignment_history_and_multilingual

Revision ID: 784f67f24176
Revises: ac4563396af6
Create Date: 2026-08-16 12:10:37.314138

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '784f67f24176'
down_revision: Union[str, None] = 'ac4563396af6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('assignments', sa.Column('reason', sa.Text(), nullable=True))
    op.add_column('assignments', sa.Column('workload_snapshot', sa.JSON(), nullable=True))
    op.add_column('grievances', sa.Column('assigned_officer_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(None, 'grievances', 'users', ['assigned_officer_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint(None, 'grievances', type_='foreignkey')
    op.drop_column('grievances', 'assigned_officer_id')
    op.drop_column('assignments', 'workload_snapshot')
    op.drop_column('assignments', 'reason')
