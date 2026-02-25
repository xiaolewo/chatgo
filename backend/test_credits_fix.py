#!/usr/bin/env python3
"""
测试积分扣除功能修复
验证Credits.update_credit_by_user_id方法是否正常工作
"""

import sys
from pathlib import Path
from decimal import Decimal

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from open_webui.models.credits import Credits


def test_credit_update():
    """测试积分扣除功能"""

    print("=== 积分扣除功能测试 ===\n")

    # 测试用户ID
    test_user_id = "test_user_123"

    print("1. 初始化测试用户积分...")
    try:
        # 初始化用户积分
        credit_model = Credits.init_credit_by_user_id(test_user_id)
        print(f"✅ 用户 {test_user_id} 初始积分: {credit_model.credit}")
    except Exception as e:
        print(f"❌ 初始化积分失败: {e}")
        return False

    print()

    print("2. 测试update_credit_by_user_id方法...")
    try:
        # 获取当前积分
        current_credit = Credits.get_credit_by_user_id(test_user_id)
        old_credits = current_credit.credit

        # 模拟视频生成扣除5个积分
        credits_cost = 5
        new_credit = old_credits - credits_cost

        print(f"当前积分: {old_credits}")
        print(f"扣除积分: {credits_cost}")
        print(f"目标积分: {new_credit}")

        # 调用update_credit_by_user_id方法
        updated_credit = Credits.update_credit_by_user_id(test_user_id, new_credit)

        if updated_credit:
            print(f"✅ 积分扣除成功")
            print(f"   扣除前: {old_credits}")
            print(f"   扣除后: {updated_credit.credit}")
            print(f"   实际扣除: {old_credits - updated_credit.credit}")
        else:
            print("❌ 积分扣除失败: update_credit_by_user_id返回None")
            return False

    except Exception as e:
        print(f"❌ 积分扣除异常: {e}")
        import traceback

        print(f"错误详情: {traceback.format_exc()}")
        return False

    print()

    print("3. 测试Decimal类型兼容性...")
    try:
        # 测试Decimal和int的混合运算
        current_credit = Credits.get_credit_by_user_id(test_user_id)
        old_credits = current_credit.credit  # Decimal类型
        credits_cost = 10  # int类型

        # 这个运算应该正常工作
        new_credit_amount = old_credits - credits_cost  # Decimal - int = Decimal

        print(f"Decimal - int 运算测试:")
        print(f"   {old_credits} - {credits_cost} = {new_credit_amount}")
        print(f"   结果类型: {type(new_credit_amount)}")

        # 再次扣除积分
        updated_credit = Credits.update_credit_by_user_id(
            test_user_id, new_credit_amount
        )

        if updated_credit:
            print(f"✅ Decimal类型兼容性测试通过")
        else:
            print("❌ Decimal类型兼容性测试失败")
            return False

    except Exception as e:
        print(f"❌ Decimal兼容性测试异常: {e}")
        return False

    print()

    print("4. 检查积分记录日志...")
    try:
        from open_webui.models.credits import CreditLogs

        # 获取用户的积分日志
        logs = CreditLogs.get_credit_log_by_page(user_id=test_user_id, limit=5)

        print(f"用户 {test_user_id} 最近5条积分记录:")
        for i, log in enumerate(logs, 1):
            print(
                f"   {i}. 积分: {log.credit}, 时间: {log.created_at}, 详情: {log.detail}"
            )

        if logs:
            print("✅ 积分记录日志正常")
        else:
            print("⚠️  没有找到积分记录日志")

    except Exception as e:
        print(f"❌ 检查积分日志异常: {e}")
        return False

    print("\n🎉 所有测试通过！积分扣除功能修复成功！")
    return True


if __name__ == "__main__":
    success = test_credit_update()
    if success:
        print("\n✅ 积分扣除功能验证通过，即梦和可灵视频生成应该可以正常扣除v豆了")
    else:
        print("\n❌ 积分扣除功能验证失败，需要进一步检查")
        sys.exit(1)
