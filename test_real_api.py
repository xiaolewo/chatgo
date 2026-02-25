#!/usr/bin/env python3
"""
测试真实的MidJourney API调用
"""

import asyncio
import httpx
import json

# 真实API配置
API_URL = "https://api.linkapi.org"
API_KEY = "sk-fvaOT6nT5pHxOiy5Rq7vrzsDnk18dHmfdDsbPGW3g4qZKHX9"


async def test_api_connection():
    """测试API连接和基础调用"""
    print("🧪 测试MidJourney API连接")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY[:20]}...")

    async with httpx.AsyncClient() as client:
        try:
            # 测试基础图像生成API
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }

            # 构建最简单的请求
            payload = {"prompt": "a cute cat", "base64Array": []}

            submit_url = f"{API_URL}/fast/mj/submit/imagine"
            print(f"\n📡 调用URL: {submit_url}")
            print(f"📤 请求payload: {json.dumps(payload, indent=2)}")

            # 发送请求
            response = await client.post(
                submit_url, json=payload, headers=headers, timeout=30.0
            )

            print(f"\n📊 响应状态码: {response.status_code}")
            print(f"📥 响应头: {dict(response.headers)}")

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}"
                )

                if result.get("code") == 1:
                    task_id = result.get("result")
                    print(f"🎉 任务提交成功！任务ID: {task_id}")
                    return task_id
                else:
                    print(f"❌ 任务提交失败: {result.get('description', '未知错误')}")
                    return None
            else:
                error_text = response.text
                print(f"❌ API调用失败: {response.status_code}")
                print(f"💥 错误内容: {error_text}")
                return None

        except Exception as e:
            print(f"💥 请求异常: {str(e)}")
            return None


async def test_task_status(task_id):
    """测试任务状态查询"""
    if not task_id:
        return

    print(f"\n🔍 查询任务状态: {task_id}")

    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }

            fetch_url = f"{API_URL}/fast/mj/task/{task_id}/fetch"
            print(f"📡 查询URL: {fetch_url}")

            response = await client.get(fetch_url, headers=headers, timeout=30.0)

            print(f"📊 查询状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ 任务状态: {json.dumps(result, indent=2, ensure_ascii=False)}"
                )

                status = result.get("status")
                progress = result.get("progress", "0%")
                print(f"📈 当前状态: {status} - 进度: {progress}")

                if status == "SUCCESS":
                    print(f"🖼️  图像URL: {result.get('imageUrl', 'N/A')}")
                    buttons = result.get("buttons", [])
                    print(f"🎮 可用按钮: {len(buttons)}个")
                elif status == "FAILURE":
                    print(f"💥 失败原因: {result.get('failReason', 'N/A')}")

            else:
                print(f"❌ 查询失败: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"💥 查询异常: {str(e)}")


async def test_advanced_parameters():
    """测试带高级参数的API调用"""
    print(f"\n🎨 测试高级参数功能")

    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            }

            # 测试带高级参数的请求
            payload = {
                "prompt": "a beautiful landscape --chaos 30 --stylize 100 --v 6.1",
                "base64Array": [],
            }

            submit_url = f"{API_URL}/fast/mj/submit/imagine"
            print(f"📤 高级参数请求: {json.dumps(payload, indent=2)}")

            response = await client.post(
                submit_url, json=payload, headers=headers, timeout=30.0
            )

            print(f"📊 高级参数响应: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ 高级参数结果: {json.dumps(result, indent=2, ensure_ascii=False)}"
                )
                return result.get("result") if result.get("code") == 1 else None
            else:
                print(f"❌ 高级参数失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"💥 高级参数异常: {str(e)}")
            return None


async def main():
    """主测试函数"""
    print("🚀 开始MidJourney API集成测试\n")

    # 1. 测试基础API连接
    task_id = await test_api_connection()

    # 2. 如果基础调用成功，查询任务状态
    if task_id:
        await asyncio.sleep(2)  # 等待2秒
        await test_task_status(task_id)

    # 3. 测试高级参数
    advanced_task_id = await test_advanced_parameters()

    print(f"\n📋 测试总结:")
    print(f"✅ 基础API调用: {'成功' if task_id else '失败'}")
    print(f"✅ 高级参数调用: {'成功' if advanced_task_id else '失败'}")

    if task_id or advanced_task_id:
        print(f"\n🎉 API连接正常！可以集成到OpenWebUI中")
        return True
    else:
        print(f"\n💥 API调用失败，需要检查参数或权限")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
