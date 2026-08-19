"""add_secure_auth_and_staff_authorization

Revision ID: c28d7a1e5a0c
Revises: 3aec9843a868
Create Date: 2026-08-19 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c28d7a1e5a0c'
down_revision: Union[str, None] = '3aec9843a868'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add fields to users table
    op.add_column('users', sa.Column('phone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('google_subject', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('auth_provider', sa.String(length=50), server_default='credentials', nullable=False))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Create staff_authorizations table
    op.create_table(
        'staff_authorizations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('CITIZEN', 'OFFICER', 'SUPERVISOR', 'ADMIN', name='user_roles_enum'), nullable=False),
        sa.Column('department_id', sa.Uuid(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_staff_authorizations_email'), 'staff_authorizations', ['email'], unique=True)

    # 3. Seed staff authorizations
    op.execute(
        """
        INSERT INTO staff_authorizations (id, email, role, is_active, created_at)
        VALUES 
            (gen_random_uuid(), 'priyankah.4767@gmail.com', 'OFFICER', true, now()),
            (gen_random_uuid(), 'charanavs04@gmail.com', 'OFFICER', true, now()),
            (gen_random_uuid(), 'prajwals2006ps@gmail.com', 'SUPERVISOR', true, now()),
            (gen_random_uuid(), 'dmsudeepreddy17@gmail.com', 'SUPERVISOR', true, now()),
            (gen_random_uuid(), 'bhoomija24@gmail.com', 'SUPERVISOR', true, now()),
            (gen_random_uuid(), 'iamchethen2813@gmail.com', 'ADMIN', true, now())
        ON CONFLICT (email) DO NOTHING;
        """
    )


def downgrade() -> None:
    # 1. Drop staff_authorizations table
    op.drop_index(op.f('ix_staff_authorizations_email'), table_name='staff_authorizations')
    op.drop_table('staff_authorizations')

    # 2. Drop fields from users table
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'google_subject')
    op.drop_column('users', 'password_reset_expires_at')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'verification_token_expires_at')
    op.drop_column('users', 'verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'phone')
