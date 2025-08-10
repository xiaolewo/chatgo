#!/usr/bin/env python3
"""
简单的状态调试工具
用于检查可灵API状态同步问题
"""

import json
import sys
import httpx
import asyncio


async def check_kling_status(api_url, api_key, task_id):
    """检查可灵API的任务状态"""

    print(f"=== 调试可灵API状态同步 ===")
    print(f"API URL: {api_url}")
    print(f"任务ID: {task_id}")
    print(f"API Key: {'已配置' if api_key else '未配置'}")
    print()

    if not api_url or not api_key:
        print("❌ API配置不完整")
        return

    # 构建查询URL
    status_url = f"{api_url}/kling/v1/videos/{task_id}"
    print(f"查询URL: {status_url}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                status_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            print(f"响应状态码: HTTP {response.status_code}")

            if response.is_success:
                try:
                    result = response.json()
                    print(f"响应JSON:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))

                    # 分析响应内容
                    if result.get("code") == 0 and "data" in result:
                        task_data = result["data"]
                        task_status = task_data.get("task_status", "未知")
                        print(f"\n✅ 任务状态: {task_status}")

                        if task_data.get("task_result"):
                            task_result = task_data["task_result"]
                            if task_result.get("videos"):
                                video = task_result["videos"][0]
                                print(f"✅ 视频URL: {video.get('url', '无')}")
                                print(f"✅ 视频ID: {video.get('id', '无')}")
                                print(f"✅ 视频时长: {video.get('duration', '无')}")
                            else:
                                print("⚠️ 没有视频结果")
                        else:
                            print("⚠️ 没有task_result")
                    else:
                        print(
                            f"❌ API响应异常: code={result.get('code')}, message={result.get('message')}"
                        )

                except Exception as e:
                    print(f"❌ JSON解析失败: {e}")
                    print(f"原始响应: {response.text}")
            else:
                print(f"❌ 请求失败: {response.text}")

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback

        traceback.print_exc()


def main():
    if len(sys.argv) != 4:
        print("使用方法: python debug_status.py <api_url> <api_key> <task_id>")
        print("示例: python debug_status.py https://api.kling.com your_api_key 12345")
        sys.exit(1)

    api_url = sys.argv[1]
    api_key = sys.argv[2]
    task_id = sys.argv[3]

    asyncio.run(check_kling_status(api_url, api_key, task_id))


if __name__ == "__main__":
    main()
