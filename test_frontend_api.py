#!/usr/bin/env python3
"""
模拟前端API调用，测试完整流程
"""

import asyncio
import httpx
import json
import time
from datetime import datetime


async def test_frontend_api():
    """测试前端API调用流程"""

    # OpenWebUI API配置
    OPENWEBUI_URL = "http://localhost:8080"

    print("🔍 前端API调用测试")
    print("=" * 60)
    print(f"时间: {datetime.now()}")

    async with httpx.AsyncClient() as client:

        # 步骤1: 测试MidJourney配置端点
        print("\n📋 步骤1: 测试配置端点")
        try:
            config_response = await client.get(
                f"{OPENWEBUI_URL}/api/v1/midjourney/config", timeout=10
            )
            print(f"配置端点状态码: {config_response.status_code}")

            if config_response.status_code == 403:
                print("   ⚠️  需要认证，这是正常的")
            elif config_response.status_code == 404:
                print("   ❌ 路由不存在！")
                return
            else:
                print(f"   状态: {config_response.status_code}")

        except Exception as e:
            print(f"   ❌ 配置端点测试失败: {str(e)}")
            return

        # 步骤2: 测试任务生成端点
        print("\n📋 步骤2: 测试任务生成端点")
        test_payload = {"prompt": "a simple test image", "mode": "fast"}

        try:
            generate_response = await client.post(
                f"{OPENWEBUI_URL}/api/v1/midjourney/generate",
                json=test_payload,
                timeout=10,
            )
            print(f"生成端点状态码: {generate_response.status_code}")

            if generate_response.status_code == 403:
                print("   ⚠️  需要认证，这是正常的")
                # 我们无法继续测试，因为没有认证token
                print("   💡 无法继续测试，因为需要登录token")
                print("   建议通过浏览器开发者工具查看实际的API调用")
                return
            elif generate_response.status_code == 404:
                print("   ❌ 生成路由不存在！")
                return
            else:
                print(f"   状态: {generate_response.status_code}")
                if generate_response.status_code == 200:
                    result = generate_response.json()
                    print(
                        f"   结果: {json.dumps(result, indent=2, ensure_ascii=False)}"
                    )

                    # 如果成功，测试任务状态查询
                    if result.get("task_id"):
                        await test_task_status(client, OPENWEBUI_URL, result["task_id"])

        except Exception as e:
            print(f"   ❌ 生成端点测试失败: {str(e)}")


async def test_task_status(client, base_url, task_id):
    """测试任务状态查询"""

    print(f"\n📋 步骤3: 测试任务状态查询")
    print(f"任务ID: {task_id}")

    try:
        status_response = await client.get(
            f"{base_url}/api/v1/midjourney/task/{task_id}", timeout=10
        )
        print(f"状态查询状态码: {status_response.status_code}")

        if status_response.status_code == 200:
            status_result = status_response.json()
            print(
                f"状态结果: {json.dumps(status_result, indent=2, ensure_ascii=False)}"
            )
        elif status_response.status_code == 403:
            print("   ⚠️  需要认证")
        elif status_response.status_code == 404:
            print("   ❌ 状态查询路由不存在！")
        else:
            print(f"   错误: {status_response.status_code} - {status_response.text}")

    except Exception as e:
        print(f"   ❌ 状态查询失败: {str(e)}")


def check_debug_steps():
    """提供调试步骤"""

    print("\n" + "=" * 60)
    print("🔧 调试建议:")
    print()
    print("1. 检查后端服务是否重启:")
    print("   docker logs openwebui --tail 50")
    print("   或查看systemctl status/日志")
    print()
    print("2. 在浏览器中打开开发者工具:")
    print("   - 按F12打开开发者工具")
    print("   - 切换到Network标签")
    print("   - 尝试生成图像")
    print("   - 查看失败的API请求详情")
    print()
    print("3. 查看具体的API调用URL和响应:")
    print("   - 找到失败的请求")
    print("   - 检查请求URL是否正确")
    print("   - 检查响应内容和状态码")
    print()
    print("4. 检查后端配置:")
    print("   - 确认MidJourney路由已正确加载")
    print("   - 检查后端日志中的错误信息")
    print()
    print("5. 验证前端配置:")
    print("   - 确认MIDJOURNEY_API_BASE_URL指向正确的端点")
    print("   - 检查认证token是否有效")


if __name__ == "__main__":
    asyncio.run(test_frontend_api())
    check_debug_steps()
