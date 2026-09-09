"""add problem selected flag

Revision ID: a3d21f0b7c48
Revises: 5f4f131f9b88
Create Date: 2026-09-08 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d21f0b7c48'
down_revision: Union[str, Sequence[str], None] = '5f4f131f9b88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('problem', schema=None) as batch_op:
        # server_default so existing rows get a value; new rows take it from the model.
        batch_op.add_column(
            sa.Column('selected', sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('problem', schema=None) as batch_op:
        batch_op.drop_column('selected')
