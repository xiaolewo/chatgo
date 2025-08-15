"""Unify all migration heads - Final merge

Revision ID: 03f980d4a3cc
Revises: 3c526075dc91, add_ppt_config_table, add_user_group_membership
Create Date: 2025-08-14 13:35:03.532051

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "03f980d4a3cc"
down_revision: Union[str, None] = (
    "3c526075dc91",
    "add_ppt_config_table",
    "add_user_group_membership",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    统一所有HEAD的合并迁移
    所有表结构和字段都已在前面的迁移中创建
    这个合并迁移不需要执行任何操作
    """
    pass


def downgrade() -> None:
    """
    回滚合并操作
    """
    pass
