#!/usr/bin/env python3
"""
测试可灵API回调机制的工具
"""

import httpx
import asyncio
import json


async def test_callback():
    """测试回调接口"""
    callback_url = "http://localhost:8080/api/v1/kling/callback"

    # 模拟可灵API完成后的回调数据
    test_callback_data = {
        "task_id": "781909151135473721",  # 使用你之前的task_id
        "task_status": "succeed",
        "updated_at": 1754450999000,  # 新的时间戳
        "task_status_msg": "视频生成完成",
        "task_result": {
            "videos": [
                {
                    "id": "test_video_id",
                    "url": "https://example.com/test_video.mp4",
                    "duration": 5,
                }
            ]
        },
    }

    print("=== 测试可灵API回调机制 ===")
    print(f"回调URL: {callback_url}")
    print(f"测试数据: {json.dumps(test_callback_data, indent=2)}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                callback_url,
                json=test_callback_data,
                headers={"Content-Type": "application/json"},
            )

            print(f"\n响应状态: HTTP {response.status_code}")
            print(f"响应内容: {response.text}")

            if response.is_success:
                result = response.json()
                if result.get("code") == 0:
                    print("✅ 回调测试成功！")
                    print("现在前端应该显示视频生成完成")
                else:
                    print(f"❌ 回调处理失败: {result.get('message')}")
            else:
                print(f"❌ 回调请求失败")

    except Exception as e:
        print(f"❌ 测试回调失败: {e}")
        print("可能原因:")
        print("1. 后端服务未启动")
        print("2. 端口8080被占用")
        print("3. 网络连接问题")


def main():
    print("测试可灵API回调机制...\n")
    asyncio.run(test_callback())

    print("\n=== 使用说明 ===")
    print("1. 确保后端服务运行在 http://localhost:8080")
    print("2. 运行此脚本模拟可灵API的回调通知")
    print("3. 检查前端页面是否正确显示视频完成状态")
    print("4. 检查后端日志是否有回调处理记录")


if __name__ == "__main__":
    main()
