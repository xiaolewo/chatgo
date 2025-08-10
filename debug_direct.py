#!/usr/bin/env python3
"""
直接调用后端代码进行调试
绕过HTTP层面，直接测试业务逻辑
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加backend路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


async def test_backend_logic():
    """直接测试后端逻辑"""

    print("🔍 直接测试后端逻辑")
    print("=" * 50)
    print(f"时间: {datetime.now()}")

    try:
        # 导入后端模块
        from open_webui.routers.midjourney import fetch_midjourney_task

        # 测试参数
        api_url = "https://api.linkapi.org"
        api_key = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"

        # 步骤1: 先提交一个任务获取task_id
        print("\n1️⃣ 提交测试任务...")
        import httpx

        async with httpx.AsyncClient() as client:
            submit_url = f"{api_url}/mj-fast/mj/submit/imagine"
            payload = {"prompt": "test task for debugging", "base64Array": []}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            submit_response = await client.post(
                submit_url, json=payload, headers=headers, timeout=30
            )

            if submit_response.status_code == 200:
                submit_result = submit_response.json()
                if submit_result.get("code") == 1:
                    task_id = submit_result.get("result")
                    print(f"✅ 任务提交成功，ID: {task_id}")

                    # 步骤2: 使用修复后的函数查询状态
                    print(f"\n2️⃣ 测试修复后的查询函数...")

                    try:
                        # 直接调用修复后的函数
                        status_result = await fetch_midjourney_task(
                            api_url=api_url,
                            api_key=api_key,
                            task_id=task_id,
                            mode="fast",
                        )

                        print(f"✅ 查询函数调用成功")
                        print(f"状态: {status_result.get('status')}")
                        print(f"进度: {status_result.get('progress')}")
                        print(f"描述: {status_result.get('description', 'N/A')}")

                        if status_result.get("status") == "FAILURE":
                            print(f"❌ 失败原因: {status_result.get('failReason')}")

                        # 步骤3: 测试状态映射逻辑
                        print(f"\n3️⃣ 测试状态映射...")
                        test_status_mapping(status_result)

                    except Exception as e:
                        print(f"❌ 查询函数调用失败: {str(e)}")
                        import traceback

                        traceback.print_exc()

                else:
                    print(f"❌ 任务提交失败: {submit_result}")
            else:
                print(
                    f"❌ HTTP错误: {submit_response.status_code} - {submit_response.text}"
                )

    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保在OpenWebUI项目根目录中运行此脚本")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()


def test_status_mapping(status_response):
    """测试状态映射逻辑"""

    print("   测试状态映射逻辑...")

    # 模拟task_info
    task_info = {"status": "processing", "progress": 20, "message": "处理中"}

    # 应用状态映射逻辑
    mj_status = status_response.get("status")

    print(f"   MidJourney状态: {mj_status}")

    if mj_status == "SUCCESS":
        task_info["status"] = "completed"
        task_info["message"] = "图像生成完成"
        task_info["progress"] = 100
        print(f"   → 映射为: completed")

    elif mj_status in ["NOT_START", "SUBMITTED"]:
        task_info["message"] = "任务已提交，等待处理"
        task_info["progress"] = max(task_info.get("progress", 0), 5)
        print(f"   → 映射为: processing (等待)")

    elif mj_status == "IN_PROGRESS":
        progress_str = status_response.get("progress", "0%")
        try:
            progress_num = int(progress_str.replace("%", ""))
            task_info["progress"] = 20 + int(progress_num * 0.75)
        except:
            pass
        task_info["message"] = f"MidJourney正在生成图像 ({progress_str})"
        print(f"   → 映射为: processing (进行中)")

    elif mj_status == "FAILURE":
        task_info["status"] = "failed"
        task_info["message"] = "生成失败"
        print(f"   → 映射为: failed")

    else:
        print(f"   → 未处理的状态: {mj_status}")

    print(f"   最终状态: {task_info['status']}")
    print(f"   进度: {task_info['progress']}%")
    print(f"   消息: {task_info['message']}")


def check_imports():
    """检查导入是否正常"""
    print("\n🔍 检查导入...")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

        # 测试基本导入
        import open_webui

        print("✅ open_webui 导入成功")

        import open_webui.routers

        print("✅ routers 导入成功")

        import open_webui.routers.midjourney

        print("✅ midjourney 路由导入成功")

        from open_webui.routers.midjourney import fetch_midjourney_task

        print("✅ fetch_midjourney_task 函数导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {str(e)}")
        return False


if __name__ == "__main__":
    print("检查导入状态...")
    if check_imports():
        print("导入成功，开始测试...")
        asyncio.run(test_backend_logic())
    else:
        print("导入失败，请检查环境配置")
