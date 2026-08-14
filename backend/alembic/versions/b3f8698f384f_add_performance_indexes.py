"""add_performance_indexes

Revision ID: b3f8698f384f
Revises: 3aec9843a868
Create Date: 2026-08-14 21:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f8698f384f'
down_revision: Union[str, None] = '3aec9843a868'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create indexes for frequently queried fields
    op.create_index('ix_grievances_citizen_id', 'grievances', ['citizen_id'], unique=False)
    op.create_index('ix_grievances_current_state', 'grievances', ['current_state'], unique=False)
    op.create_index('ix_grievances_department_id', 'grievances', ['department_id'], unique=False)
    op.create_index('ix_assignments_officer_id', 'assignments', ['officer_id'], unique=False)
    op.create_index('ix_assignments_grievance_id', 'assignments', ['grievance_id'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_grievance_events_grievance_id', 'grievance_events', ['grievance_id'], unique=False)
    op.create_index('ix_evidence_grievance_id', 'evidence', ['grievance_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_evidence_grievance_id', table_name='evidence')
    op.drop_index('ix_grievance_events_grievance_id', table_name='grievance_events')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_assignments_grievance_id', table_name='assignments')
    op.drop_index('ix_assignments_officer_id', table_name='assignments')
    op.drop_index('ix_grievances_department_id', table_name='grievances')
    op.drop_index('ix_grievances_current_state', table_name='grievances')
    op.drop_index('ix_grievances_citizen_id', table_name='grievances')
