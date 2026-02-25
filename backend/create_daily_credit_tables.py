#!/usr/bin/env python3
"""
每日积分发放功能数据库迁移脚本

这个脚本用于创建每日积分发放功能所需的数据库表。
如果您在现有系统中添加此功能，请运行此脚本来创建必要的表结构。

使用方法:
python create_daily_credit_tables.py
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from open_webui.internal.db import Base, engine, get_db
from sqlalchemy import text


def check_table_exists(table_name):
    """检查表是否存在"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """))
            return result.fetchone() is not None
    except Exception:
        return False


def create_daily_credit_tables():
    """创建每日积分发放相关的数据库表"""
    print("🔧 每日积分发放功能 - 数据库迁移")
    print("=" * 50)

    try:
        # 导入所有相关模型
        from open_webui.models.subscription import DailyCreditGrant
        from open_webui.models.credits import Credit, CreditLog, TradeTicket

        # 检查表是否已存在
        table_name = "subscription_daily_credit_grants"
        if check_table_exists(table_name):
            print(f"✅ 表 '{table_name}' 已存在，跳过创建")
            return True

        print(f"📝 创建表 '{table_name}'...")

        # 显示当前所有表
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"📋 当前数据库中的表: {existing_tables}")

        # 创建所有表（只会创建不存在的表）
        print("🔨 开始创建表...")
        Base.metadata.create_all(bind=engine)
        print("🔨 表创建命令执行完成")

        # 检查创建后的表
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            all_tables = [row[0] for row in result.fetchall()]
            print(f"📋 创建后数据库中的表: {all_tables}")

        # 验证表是否创建成功
        if check_table_exists(table_name):
            print(f"✅ 表 '{table_name}' 创建成功")

            # 显示表结构
            with engine.connect() as conn:
                result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                columns = result.fetchall()
                print(f"\n📋 表结构:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")

            return True
        else:
            print(f"❌ 表 '{table_name}' 创建失败")

            # 尝试手动创建表
            print("🔧 尝试手动创建表...")
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS subscription_daily_credit_grants (
                        id VARCHAR PRIMARY KEY,
                        user_id VARCHAR NOT NULL,
                        subscription_id VARCHAR,
                        plan_id VARCHAR,
                        grant_date BIGINT NOT NULL,
                        credits_granted BIGINT DEFAULT 0,
                        created_at BIGINT,
                        FOREIGN KEY(subscription_id) REFERENCES subscription_subscriptions (id),
                        FOREIGN KEY(plan_id) REFERENCES subscription_plans (id)
                    )
                """))
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_subscription_daily_credit_grants_user_id ON subscription_daily_credit_grants (user_id)"
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_subscription_daily_credit_grants_grant_date ON subscription_daily_credit_grants (grant_date)"
                    )
                )
                conn.commit()
                print("✅ 手动创建表成功")

            return check_table_exists(table_name)

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()
        return False


def verify_integration():
    """验证功能集成"""
    print(f"\n🔍 验证功能集成...")

    try:
        # 测试导入所有相关模块
        from open_webui.models.subscription import DailyCreditGrants
        from open_webui.utils.task_scheduler import TaskScheduler

        print("✅ 所有功能模块导入成功")

        # 测试基础功能
        today_timestamp = DailyCreditGrants.get_today_timestamp()
        print(f"✅ 今日时间戳获取成功: {today_timestamp}")

        return True

    except Exception as e:
        print(f"❌ 功能集成验证失败: {e}")
        return False


def main():
    """主函数"""
    success = create_daily_credit_tables()

    if success:
        verify_integration()
        print(f"\n🎉 每日积分发放功能数据库迁移完成！")
        print(f"\n📖 接下来您可以:")
        print(f"  1. 重启应用以激活任务调度器")
        print(f"  2. 创建包含积分的套餐")
        print(f"  3. 运行测试脚本: python test_daily_credits.py")
        print(f"  4. 查看功能文档: 每日积分发放功能说明.md")
    else:
        print(f"\n❌ 数据库迁移失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
