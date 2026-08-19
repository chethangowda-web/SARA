"""merge heads

Revision ID: ac4563396af6
Revises: ('4b5c6d7e8f9a', 'b3f8698f384f')
Create Date: 2026-08-16 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ac4563396af6'
down_revision: Union[str, Sequence[str], None] = ('4b5c6d7e8f9a', 'b3f8698f384f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
