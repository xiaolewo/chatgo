#!/usr/bin/env python3
"""
测试即梦任务视频URL提取修复
手动查询数据库中已成功但缺少视频URL的任务，并尝试重新获取
"""
import os
import sys
import json
import httpx
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from open_webui.models.jimeng_tasks import JimengTasks
from open_webui.config import JIMENG_API_URL, JIMENG_API_KEY


# 任务状态常量
class TaskStatus:
    NOT_START = "NOT_START"
    SUBMITTED = "SUBMITTED"
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    FAILURE = "FAILURE"
    SUCCESS = "SUCCESS"


async def test_video_extraction():
    """测试视频URL提取功能"""

    print("=== 即梦任务视频URL提取修复测试 ===\n")

    # 1. 获取所有SUCCESS但video_url为空的任务
    print("1. 查询成功但缺少视频URL的任务...")

    # 这里我们直接查询已知的任务ID
    task_id = "cgt-20250806174309-4qgz9"
    task = JimengTasks.get_task_by_id(task_id)

    if not task:
        print(f"任务 {task_id} 不存在")
        return

    print(f"找到任务: {task_id}")
    print(f"状态: {task.status}")
    print(f"当前video_url: {task.video_url}")
    print(f"创建时间: {task.created_at}")
    print()

    # 2. 检查API配置
    api_url = JIMENG_API_URL.value
    api_key = JIMENG_API_KEY.value

    print("2. 检查API配置...")
    print(f"API URL: {api_url[:50] if api_url else 'None'}...")
    print(f"API Key: {'已配置' if api_key else 'None'}")

    if not api_url or not api_key:
        print("❌ API配置不完整，无法查询")
        return

    # 3. 查询即梦API获取任务状态
    print(f"\n3. 查询即梦API获取任务 {task_id} 的最新状态...")

    try:
        status_url = f"{api_url}/jimeng/fetch/{task_id}"
        print(f"请求URL: {status_url}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                status_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            print(f"HTTP状态码: {response.status_code}")

            if response.is_success:
                api_result = response.json()
                print("✅ API查询成功")
                print(f"API响应原始数据:")
                print(json.dumps(api_result, ensure_ascii=False, indent=2))

                if api_result.get("code") == "success" and "data" in api_result:
                    task_data = api_result["data"]
                    new_status = task_data.get("status")

                    print(f"\n4. 分析任务数据...")
                    print(f"任务状态: {new_status}")
                    print(f"task_data结构: {list(task_data.keys())}")
                    print(f"task_data详细内容:")
                    print(json.dumps(task_data, ensure_ascii=False, indent=2))

                    # 5. 尝试提取视频URL
                    print(f"\n5. 尝试提取视频URL...")

                    video_url = None
                    video_id = None
                    extraction_method = None

                    # 尝试不同的数据结构路径
                    if task_data.get("data") and task_data["data"].get("data"):
                        # 原来的路径：task_data.data.data.video
                        video_info = task_data["data"]["data"]
                        if video_info.get("video"):
                            video_url = video_info["video"]
                            video_id = task_data.get("task_id")
                            extraction_method = "data.data.video"

                    # 尝试直接从task_data.data获取
                    elif task_data.get("data") and task_data["data"].get("video"):
                        video_url = task_data["data"]["video"]
                        video_id = task_data.get("task_id")
                        extraction_method = "data.video"

                    # 尝试直接从task_data获取
                    elif task_data.get("video"):
                        video_url = task_data["video"]
                        video_id = task_data.get("task_id")
                        extraction_method = "video"

                    # 尝试从video_url字段获取
                    elif task_data.get("video_url"):
                        video_url = task_data["video_url"]
                        video_id = task_data.get("task_id")
                        extraction_method = "video_url"

                    if video_url:
                        print(f"✅ 成功提取视频URL!")
                        print(f"提取方法: {extraction_method}")
                        print(f"视频URL: {video_url}")
                        print(f"视频ID: {video_id}")

                        # 6. 更新数据库
                        print(f"\n6. 更新数据库...")
                        update_data = {
                            "video_url": video_url,
                            "video_id": video_id,
                            "finish_time": task_data.get("finish_time"),
                        }

                        updated_task = JimengTasks.update_task_by_id(
                            task_id, update_data
                        )
                        if updated_task:
                            print("✅ 数据库更新成功!")
                            print(f"新的video_url: {updated_task.video_url}")
                        else:
                            print("❌ 数据库更新失败")
                    else:
                        print("❌ 无法从任何路径提取视频URL")
                        print("可能的原因:")
                        print("- API响应数据结构与预期不符")
                        print("- 视频还未生成完成")
                        print("- API接口有变化")

                        # 显示所有可能的字段
                        def find_video_fields(obj, path=""):
                            """递归查找可能包含视频URL的字段"""
                            video_fields = []
                            if isinstance(obj, dict):
                                for key, value in obj.items():
                                    current_path = f"{path}.{key}" if path else key
                                    if isinstance(value, str) and any(
                                        ext in value.lower()
                                        for ext in [
                                            ".mp4",
                                            ".avi",
                                            ".mov",
                                            "video",
                                            "http",
                                        ]
                                    ):
                                        video_fields.append((current_path, value))
                                    elif isinstance(value, (dict, list)):
                                        video_fields.extend(
                                            find_video_fields(value, current_path)
                                        )
                            elif isinstance(obj, list):
                                for i, item in enumerate(obj):
                                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                                    video_fields.extend(
                                        find_video_fields(item, current_path)
                                    )
                            return video_fields

                        video_fields = find_video_fields(task_data)
                        if video_fields:
                            print(f"\n发现可能的视频相关字段:")
                            for field_path, value in video_fields:
                                print(f"  {field_path}: {value}")
                        else:
                            print("未发现任何可能的视频相关字段")

                else:
                    print("❌ API响应格式异常")
                    print(f"响应code: {api_result.get('code')}")
                    print(f"包含data字段: {'data' in api_result}")
            else:
                print(f"❌ API查询失败: HTTP {response.status_code}")
                print(f"响应内容: {response.text}")

    except Exception as e:
        print(f"❌ 查询失败: {e}")
        import traceback

        print(f"错误详情: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(test_video_extraction())
