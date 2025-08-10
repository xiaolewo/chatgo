#!/usr/bin/env python3
"""
调试MidJourney轮询过程
专门测试任务状态查询是否正常工作
"""

import asyncio
import httpx
import json
from datetime import datetime


async def test_polling_process():
    """测试完整的轮询过程"""

    API_URL = "https://api.linkapi.org"
    API_KEY = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"

    print("🔍 MidJourney轮询过程调试")
    print("=" * 60)
    print(f"时间: {datetime.now()}")

    async with httpx.AsyncClient() as client:

        # 步骤1: 提交任务
        print("\n📋 步骤1: 提交图像生成任务")
        submit_url = f"{API_URL}/mj-fast/mj/submit/imagine"
        payload = {"prompt": "a cat sitting on a windowsill", "base64Array": []}
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            submit_response = await client.post(
                submit_url, json=payload, headers=headers, timeout=30
            )
            print(f"提交状态码: {submit_response.status_code}")

            if submit_response.status_code == 200:
                submit_result = submit_response.json()
                print(
                    f"提交结果: {json.dumps(submit_result, indent=2, ensure_ascii=False)}"
                )

                if submit_result.get("code") == 1:
                    task_id = submit_result.get("result")
                    print(f"✅ 任务提交成功，任务ID: {task_id}")

                    # 步骤2: 立即查询任务状态
                    print(f"\n📋 步骤2: 立即查询任务状态")
                    await test_task_query(client, API_URL, API_KEY, task_id)

                    # 步骤3: 等待一段时间后再查询
                    print(f"\n📋 步骤3: 等待5秒后查询状态")
                    await asyncio.sleep(5)
                    await test_task_query(client, API_URL, API_KEY, task_id)

                    # 步骤4: 模拟轮询过程
                    print(f"\n📋 步骤4: 模拟轮询过程（最多5次）")
                    await simulate_polling(
                        client, API_URL, API_KEY, task_id, max_polls=5
                    )

                else:
                    print(f"❌ 任务提交失败: {submit_result}")
            else:
                print(
                    f"❌ HTTP错误: {submit_response.status_code} - {submit_response.text}"
                )

        except Exception as e:
            print(f"❌ 提交异常: {str(e)}")


async def test_task_query(client, api_url, api_key, task_id):
    """测试单次任务查询"""

    # 使用修复后的统一查询路径
    query_url = f"{api_url}/mj/task/{task_id}/fetch"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"   查询URL: {query_url}")

    try:
        query_response = await client.get(query_url, headers=headers, timeout=10)
        print(f"   查询状态码: {query_response.status_code}")

        if query_response.status_code == 200:
            query_result = query_response.json()
            print(
                f"   查询结果: {json.dumps(query_result, indent=4, ensure_ascii=False)}"
            )

            status = query_result.get("status", "unknown")
            progress = query_result.get("progress", "unknown")
            image_url = query_result.get("imageUrl")
            fail_reason = query_result.get("failReason")

            print(f"   ✅ 状态: {status}")
            print(f"   ✅ 进度: {progress}")
            if image_url:
                print(f"   ✅ 图片URL: {image_url}")
            if fail_reason:
                print(f"   ❌ 失败原因: {fail_reason}")

        else:
            print(
                f"   ❌ 查询失败: {query_response.status_code} - {query_response.text}"
            )

    except Exception as e:
        print(f"   ❌ 查询异常: {str(e)}")


async def simulate_polling(client, api_url, api_key, task_id, max_polls=5):
    """模拟轮询过程"""

    poll_count = 0

    while poll_count < max_polls:
        poll_count += 1
        print(f"\n   🔄 第{poll_count}次轮询:")

        await test_task_query(client, api_url, api_key, task_id)

        # 等待3秒再进行下一次轮询
        if poll_count < max_polls:
            print(f"   ⏳ 等待3秒...")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(test_polling_process())
