#!/usr/bin/env python3
"""
测试后端MidJourney API调用流程
模拟后端代码的完整调用过程
"""

import httpx
import asyncio
import json


async def test_backend_api_call():
    """测试完整的后端API调用流程"""

    # 使用新的API密钥
    NEW_API_KEY = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"
    OLD_API_KEY = (
        "sk-fvaOT6nT5pHxOiy5Rq7vrzsDnk18dHmfdDsbPGW3g4qZKHX9"  # 旧密钥用于对比
    )

    API_URL = "https://api.linkapi.org"

    print("🔍 测试后端MidJourney API调用流程")
    print("=" * 60)

    # 测试参数
    request_data = {
        "prompt": "a beautiful sunset over mountains",
        "mode": "fast",
        "reference_images": [],
        "advanced_params": None,
    }

    async with httpx.AsyncClient() as client:

        # 测试1: 使用新API密钥
        print(f"\n🆕 测试1: 使用新API密钥")
        print(f"API密钥: {NEW_API_KEY[:20]}...")

        success = await test_api_call(client, API_URL, NEW_API_KEY, request_data)
        if success:
            print("✅ 新API密钥测试成功")
        else:
            print("❌ 新API密钥测试失败")

        # 测试2: 使用旧API密钥（用于对比）
        print(f"\n🔄 测试2: 使用旧API密钥（对比测试）")
        print(f"API密钥: {OLD_API_KEY[:20]}...")

        success = await test_api_call(client, API_URL, OLD_API_KEY, request_data)
        if success:
            print("✅ 旧API密钥测试成功")
        else:
            print("❌ 旧API密钥测试失败")

        # 测试3: 测试所有三种模式
        print(f"\n🚀 测试3: 测试所有模式（使用新密钥）")
        modes = ["fast", "relax", "turbo"]
        for mode in modes:
            request_data["mode"] = mode
            print(f"\n  测试{mode}模式...")
            success = await test_api_call(client, API_URL, NEW_API_KEY, request_data)
            if success:
                print(f"  ✅ {mode}模式测试成功")
            else:
                print(f"  ❌ {mode}模式测试失败")


async def test_api_call(client, api_url, api_key, request_data):
    """模拟后端的API调用逻辑"""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # 构建API请求负载 (完全按照后端代码逻辑)
        prompt = request_data.get("prompt", "")
        mode = request_data.get("mode", "fast")

        # 根据模式使用正确的API端点路径
        mode_path_map = {"fast": "mj-fast", "relax": "mj-relax", "turbo": "mj-turbo"}
        mode_path = mode_path_map.get(mode, "mj-fast")
        submit_url = f"{api_url}/{mode_path}/mj/submit/imagine"

        # 使用LinkAPI文档指定的标准参数格式
        payload = {"prompt": prompt, "base64Array": []}

        print(f"    📡 调用URL: {submit_url}")
        print(f"    📦 载荷: {json.dumps(payload, ensure_ascii=False)}")

        # 实际API调用
        response = await client.post(
            submit_url, json=payload, headers=headers, timeout=30.0
        )

        print(f"    📊 状态码: {response.status_code}")
        print(f"    📄 响应: {response.text}")

        if response.status_code != 200:
            print(f"    ❌ HTTP错误: {response.status_code}")
            return False

        result = response.json()
        if result.get("code") != 1:
            error_desc = result.get("description", "未知错误")
            print(f"    ❌ API错误: {error_desc}")

            # 分析错误类型
            if error_desc == "quota_not_enough":
                print(f"    💰 配额不足（这是好的，说明API调用格式正确）")
                return True  # 配额不足说明参数正确
            elif error_desc == "parameter error":
                print(f"    🔧 参数错误（需要修复）")
                return False
            else:
                print(f"    ⚠️  其他错误: {error_desc}")
                return False
        else:
            task_id = result.get("result")
            print(f"    ✅ 任务提交成功，ID: {task_id}")
            return True

    except Exception as e:
        print(f"    💥 异常: {str(e)}")
        return False


if __name__ == "__main__":
    asyncio.run(test_backend_api_call())
