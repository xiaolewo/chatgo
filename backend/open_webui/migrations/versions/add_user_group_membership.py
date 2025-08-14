"""Add user group membership table for multiple group support

Revision ID: add_user_group_membership
Revises: 922e7a387820
Create Date: 2024-12-19 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "add_user_group_membership"
down_revision = "922e7a387820"
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在（防止Peewee/Alembic冲突）
    from sqlalchemy import inspect

    inspector = inspect(op.get_bind())
    existing_tables = inspector.get_table_names()

    if "user_group_membership" not in existing_tables:
        # 创建用户-组关系表，直接包含外键约束
        op.create_table(
            "user_group_membership",
            sa.Column("id", sa.Text(), nullable=False, primary_key=True),
            sa.Column("user_id", sa.Text(), nullable=False, index=True),
            sa.Column("group_id", sa.Text(), nullable=False, index=True),
            sa.Column("joined_at", sa.BigInteger(), nullable=False),  # 加入时间
            sa.Column(
                "is_active", sa.Boolean(), nullable=False, default=True
            ),  # 是否活跃
            sa.Column("created_at", sa.BigInteger(), nullable=False),
            sa.Column("updated_at", sa.BigInteger(), nullable=False),
            # SQLite兼容的外键约束定义
            sa.ForeignKeyConstraint(
                ["group_id"],
                ["group.id"],
                name="fk_user_group_membership_group_id",
                ondelete="CASCADE",
            ),
        )

        # 添加联合唯一索引（SQLite兼容版本）
        op.create_index(
            "idx_user_group_unique_active",
            "user_group_membership",
            ["user_id", "group_id", "is_active"],
            unique=True,
        )
    else:
        print("user_group_membership表已存在，跳过创建")


def downgrade():
    op.drop_table("user_group_membership")
