"""merge heads

Revision ID: 733514a28521
Revises: ('b3f8698f384f', 'c28d7a1e5a0c')
Create Date: 2026-08-19 18:59:23.754647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '733514a28521'
down_revision: Union[str, None] = ('b3f8698f384f', 'c28d7a1e5a0c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
