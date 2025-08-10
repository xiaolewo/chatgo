#!/usr/bin/env python3
"""
检查API账户状态和配额
"""

import asyncio
import httpx
import json
from datetime import datetime


async def check_api_status():
    """检查API状态"""

    API_URL = "https://api.linkapi.org"
    API_KEY = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"

    print("🔍 API状态检查")
    print("=" * 50)
    print(f"时间: {datetime.now()}")

    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        # 1. 检查账户信息
        print("\n💳 检查账户信息...")
        try:
            account_response = await client.get(
                f"{API_URL}/v1/dashboard/billing/subscription",
                headers=headers,
                timeout=10,
            )
            print(f"账户状态码: {account_response.status_code}")
            if account_response.status_code == 200:
                account_data = account_response.json()
                print(
                    f"账户信息: {json.dumps(account_data, indent=2, ensure_ascii=False)}"
                )
            else:
                print(f"账户查询失败: {account_response.text}")
        except Exception as e:
            print(f"账户查询异常: {str(e)}")

        # 2. 检查使用情况
        print("\n📊 检查使用情况...")
        try:
            usage_response = await client.get(
                f"{API_URL}/v1/dashboard/billing/usage", headers=headers, timeout=10
            )
            print(f"使用情况状态码: {usage_response.status_code}")
            if usage_response.status_code == 200:
                usage_data = usage_response.json()
                print(
                    f"使用情况: {json.dumps(usage_data, indent=2, ensure_ascii=False)}"
                )
            else:
                print(f"使用情况查询失败: {usage_response.text}")
        except Exception as e:
            print(f"使用情况查询异常: {str(e)}")

        # 3. 测试不同的API key
        print("\n🔑 测试不同API密钥...")
        old_key = "sk-fvaOT6nT5pHxOiy5Rq7vrzsDnk18dHmfdDsbPGW3g4qZKHX9"

        for key_name, key_value in [("新密钥", API_KEY), ("旧密钥", old_key)]:
            print(f"\n   测试{key_name}: {key_value[:20]}...")
            test_headers = {
                "Authorization": f"Bearer {key_value}",
                "Content-Type": "application/json",
            }

            try:
                models_response = await client.get(
                    f"{API_URL}/v1/models", headers=test_headers, timeout=10
                )
                print(f"   模型列表状态码: {models_response.status_code}")

                if models_response.status_code == 200:
                    models_data = models_response.json()
                    mj_models = [
                        m
                        for m in models_data.get("data", [])
                        if "mj" in m.get("id", "").lower()
                    ]
                    print(f"   ✅ {key_name}有效，找到{len(mj_models)}个MJ模型")
                elif models_response.status_code == 401:
                    print(f"   ❌ {key_name}无效或已过期")
                elif models_response.status_code == 429:
                    print(f"   ⚠️ {key_name}达到速率限制")
                else:
                    print(f"   ❓ {key_name}状态未知: {models_response.status_code}")

            except Exception as e:
                print(f"   ❌ {key_name}测试异常: {str(e)}")

        # 4. 测试快速提交（检查是否是配额问题）
        print(f"\n⚡ 测试快速提交...")
        try:
            submit_url = f"{API_URL}/mj-fast/mj/submit/imagine"
            simple_payload = {"prompt": "test", "base64Array": []}

            submit_response = await client.post(
                submit_url, json=simple_payload, headers=headers, timeout=10
            )

            print(f"快速提交状态码: {submit_response.status_code}")
            submit_result = submit_response.json()
            print(
                f"快速提交结果: {json.dumps(submit_result, indent=2, ensure_ascii=False)}"
            )

            if submit_result.get("code") == 1:
                print("✅ 任务提交成功，API工作正常")
            elif submit_result.get("description") == "quota_not_enough":
                print("❌ 配额不足，需要充值")
            elif submit_result.get("description") == "parameter error":
                print("❌ 参数错误")
            else:
                print(f"❓ 未知状态: {submit_result}")

        except Exception as e:
            print(f"快速提交异常: {str(e)}")


if __name__ == "__main__":
    asyncio.run(check_api_status())
