#!/usr/bin/env python3
"""
每日积分发放功能测试脚本

演示如何使用每日积分发放系统：
1. 创建套餐
2. 为用户订阅套餐
3. 手动触发积分发放
4. 查看发放历史
"""

import os
import sys
import time
import uuid
from decimal import Decimal

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入数据库初始化相关
from open_webui.internal.db import Base, engine
from sqlalchemy import text


def init_database():
    """初始化数据库，创建所有必要的表"""
    print("=== 初始化数据库 ===")
    try:
        # 导入所有模型以确保它们被注册到 Base.metadata
        from open_webui.models.credits import Credit, CreditLog, TradeTicket
        from open_webui.models.subscription import (
            Plan,
            Subscription,
            RedeemCode,
            Payment,
            DailyCreditGrant,
        )

        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")

        # 验证关键表是否存在
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='subscription_daily_credit_grants'
            """))
            table_exists = result.fetchone() is not None

            if table_exists:
                print("✅ subscription_daily_credit_grants 表已创建")
            else:
                print("❌ subscription_daily_credit_grants 表创建失败")
                return False

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

    return True


from open_webui.models.subscription import (
    Plans,
    Subscriptions,
    DailyCreditGrants,
    PlanModel,
    SubscriptionModel,
)
from open_webui.models.credits import Credits
from open_webui.models.users import Users


def setup_test_data():
    """设置测试数据"""
    print("=== 设置测试数据 ===")

    # 1. 创建测试用户 (假设用户已存在)
    test_user_id = "test_user_001"
    print(f"使用测试用户ID: {test_user_id}")

    # 2. 创建测试套餐
    test_plan = PlanModel(
        id="premium_plan",
        name="高级套餐",
        description="包含每日1000积分的高级套餐",
        price=29.99,
        duration=30,  # 30天
        credits=1000,  # 每日1000积分
        features=["unlimited_chat", "priority_support"],
        is_active=True,
    )

    try:
        existing_plan = Plans.get_plan_by_id("premium_plan")
        if existing_plan:
            print("测试套餐已存在，跳过创建")
        else:
            plan = Plans.create_plan(test_plan)
            print(f"创建测试套餐: {plan.name} (ID: {plan.id})")
    except Exception as e:
        print(f"创建套餐失败: {e}")

    # 3. 为用户订阅套餐
    try:
        # 检查用户是否已有订阅
        existing_subscription = Subscriptions.get_user_active_subscription(test_user_id)
        if existing_subscription:
            print("用户已有活跃订阅，跳过创建")
            subscription_id = existing_subscription.id
        else:
            subscription_data = {
                "user_id": test_user_id,
                "plan_id": "premium_plan",
                "duration_days": 30,
            }
            result = Subscriptions.subscribe_user(subscription_data)
            subscription_id = result["subscription"]["id"]
            print(f"为用户创建订阅: {subscription_id}")
    except Exception as e:
        print(f"创建订阅失败: {e}")
        return None, None

    return test_user_id, subscription_id


def test_daily_credit_grant(user_id, subscription_id):
    """测试每日积分发放"""
    print("\n=== 测试每日积分发放 ===")

    # 1. 检查用户当前积分
    user_credit = Credits.get_credit_by_user_id(user_id)
    if user_credit:
        print(f"用户当前积分: {user_credit.credit}")
    else:
        print("用户没有积分记录，将初始化")
        Credits.init_credit_by_user_id(user_id)
        user_credit = Credits.get_credit_by_user_id(user_id)
        print(f"用户初始化积分: {user_credit.credit}")

    # 2. 检查今日是否已发放积分
    has_granted = DailyCreditGrants.has_granted_today(user_id, subscription_id)
    print(f"今日是否已发放积分: {has_granted}")

    # 3. 获取套餐信息
    subscription = Subscriptions.get_subscription_by_id(subscription_id)
    plan = Plans.get_plan_by_id(subscription.plan_id)
    print(f"套餐每日积分: {plan.credits}")

    # 4. 尝试发放积分
    if not has_granted:
        print("开始发放每日积分...")
        grant = DailyCreditGrants.grant_daily_credits(
            user_id=user_id,
            subscription_id=subscription_id,
            plan_id=plan.id,
            credits_amount=plan.credits,
        )

        if grant:
            print(f"积分发放成功: {grant.credits_granted} 积分")

            # 检查用户积分是否增加
            updated_credit = Credits.get_credit_by_user_id(user_id)
            print(f"用户更新后积分: {updated_credit.credit}")
        else:
            print("积分发放失败（可能今日已发放）")
    else:
        print("今日已发放过积分，跳过")


def test_bulk_grant():
    """测试批量发放功能"""
    print("\n=== 测试批量发放功能 ===")

    result = DailyCreditGrants.process_daily_grants_for_all_users()
    print(f"批量发放结果: {result}")


def test_grant_history(user_id):
    """测试积分发放历史查询"""
    print("\n=== 测试积分发放历史 ===")

    history = DailyCreditGrants.get_user_grant_history(user_id, page=1, limit=5)
    print(f"发放历史记录数: {history['total']}")

    for grant in history["grants"]:
        grant_date = time.strftime("%Y-%m-%d", time.localtime(grant["grant_date"]))
        print(
            f"- {grant_date}: {grant['credits_granted']} 积分 (套餐: {grant['plan_id']})"
        )


def main():
    """主函数"""
    print("🚀 每日积分发放功能测试")
    print("=" * 50)

    # 首先初始化数据库
    if not init_database():
        print("❌ 数据库初始化失败，退出测试")
        return

    try:
        # 1. 设置测试数据
        user_id, subscription_id = setup_test_data()
        if not user_id or not subscription_id:
            print("❌ 测试数据设置失败")
            return

        # 2. 测试单用户积分发放
        test_daily_credit_grant(user_id, subscription_id)

        # 3. 测试批量发放
        test_bulk_grant()

        # 4. 测试发放历史
        test_grant_history(user_id)

        print("\n✅ 测试完成！")

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
