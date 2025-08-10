#!/usr/bin/env python3
"""
MidJourney API调试脚本
用于验证配置和测试API调用
"""

import asyncio
import httpx
import json


async def test_midjourney_api():
    """测试MidJourney API调用"""

    # 配置信息 (请确保这些与你的实际配置匹配)
    API_URL = "https://api.linkapi.org"
    API_KEY = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"

    print("🔍 MidJourney API调试测试")
    print("=" * 50)

    # 测试1: 基础连接测试
    print("1️⃣ 测试基础连接...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/v1/models",
                headers={"Authorization": f"Bearer {API_KEY}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                print("✅ 基础连接成功")
                models = response.json()
                mj_models = [
                    m for m in models.get("data", []) if "mj_" in m.get("id", "")
                ]
                print(f"   找到 {len(mj_models)} 个MidJourney模型")
            else:
                print(f"❌ 基础连接失败: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        return False

    # 测试2: 图像生成API调用
    print("\n2️⃣ 测试图像生成API...")
    try:
        submit_url = f"{API_URL}/mj-fast/mj/submit/imagine"
        payload = {"prompt": "a beautiful sunset over mountains", "base64Array": []}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                submit_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )

            print(f"   状态码: {response.status_code}")
            print(f"   响应内容: {response.text}")

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 1:
                    task_id = result.get("result")
                    print(f"✅ 任务提交成功，任务ID: {task_id}")

                    # 测试3: 任务状态查询
                    print("\n3️⃣ 测试任务状态查询...")
                    await asyncio.sleep(2)  # 等待2秒

                    fetch_url = f"{API_URL}/mj/task/{task_id}/fetch"
                    status_response = await client.get(
                        fetch_url,
                        headers={"Authorization": f"Bearer {API_KEY}"},
                        timeout=10.0,
                    )

                    print(f"   状态查询响应: {status_response.status_code}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"   任务状态: {status_data.get('status', 'unknown')}")
                        print(f"   进度: {status_data.get('progress', 'unknown')}")
                        print("✅ 状态查询成功")
                    else:
                        print(f"❌ 状态查询失败: {status_response.text}")

                else:
                    print(f"❌ API返回错误: {result.get('description', '未知错误')}")
                    return False
            else:
                print(f"❌ API调用失败: {response.status_code} - {response.text}")
                return False

    except Exception as e:
        print(f"❌ API调用异常: {e}")
        return False

    print("\n🎉 所有测试完成！")
    return True


async def check_configuration():
    """检查配置文件"""
    print("\n📋 配置检查")
    print("=" * 30)

    print("请确保在OpenWebUI管理后台设置以下配置：")
    print("• MidJourney服务：启用")
    print("• API URL：https://api.linkapi.org")
    print("• API Key：sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
    print("• Fast模式积分：10")
    print("• Relax模式积分：5")
    print("• Turbo模式积分：15")


if __name__ == "__main__":

    async def main():
        await check_configuration()
        success = await test_midjourney_api()

        if success:
            print("\n✅ 所有测试通过！MidJourney API配置正确。")
            print("如果仍有问题，请检查：")
            print("1. 后端日志中的详细错误信息")
            print("2. 前端浏览器控制台的错误信息")
            print("3. 网络连接是否正常")
        else:
            print("\n❌ 测试失败，请检查配置和网络连接。")

    asyncio.run(main())
