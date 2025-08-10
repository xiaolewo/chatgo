#!/usr/bin/env python3
"""
测试修复后的状态处理
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

# 模拟状态响应
test_responses = [
    {"status": "NOT_START", "progress": "0%"},
    {"status": "SUBMITTED", "progress": "5%"},
    {"status": "IN_PROGRESS", "progress": "25%"},
    {"status": "IN_PROGRESS", "progress": "50%"},
    {"status": "IN_PROGRESS", "progress": "75%"},
    {
        "status": "SUCCESS",
        "progress": "100%",
        "imageUrl": "https://example.com/image.png",
        "buttons": [],
    },
]


def test_status_mapping():
    """测试状态映射逻辑"""

    print("🧪 测试状态映射逻辑")
    print("=" * 40)

    # 模拟任务信息
    task_info = {"status": "processing", "progress": 0, "message": "初始状态"}

    for i, status_response in enumerate(test_responses):
        print(f"\n步骤 {i+1}: MidJourney状态 = {status_response['status']}")

        # 应用我们的映射逻辑
        mj_status = status_response.get("status")

        if mj_status == "SUCCESS":
            task_info["status"] = "completed"
            task_info["message"] = "图像生成完成"
            task_info["progress"] = 100
            task_info["image_url"] = status_response.get("imageUrl")
            print(f"   → 映射为: {task_info['status']} (完成)")

        elif mj_status in ["NOT_START", "SUBMITTED"]:
            task_info["message"] = "任务已提交，等待处理"
            task_info["progress"] = max(task_info.get("progress", 0), 5)
            print(f"   → 映射为: {task_info['status']} (等待)")

        elif mj_status == "IN_PROGRESS":
            # 保持processing状态，更新进度
            progress_str = status_response.get("progress", "0%")
            try:
                progress_num = int(progress_str.replace("%", ""))
                task_info["progress"] = 20 + int(progress_num * 0.75)
            except:
                pass
            task_info["message"] = f"MidJourney正在生成图像 ({progress_str})"
            print(f"   → 映射为: {task_info['status']} (处理中)")

        elif mj_status == "FAILURE":
            task_info["status"] = "failed"
            task_info["message"] = "生成失败"
            print(f"   → 映射为: {task_info['status']} (失败)")

        elif mj_status == "CANCEL":
            task_info["status"] = "cancelled"
            task_info["message"] = "任务已取消"
            print(f"   → 映射为: {task_info['status']} (取消)")

        print(f"   状态: {task_info['status']}")
        print(f"   进度: {task_info['progress']}%")
        print(f"   消息: {task_info['message']}")

        # 如果任务完成，退出循环
        if task_info["status"] in ["completed", "failed", "cancelled"]:
            break

    print(f"\n✅ 测试完成，最终状态: {task_info['status']}")


if __name__ == "__main__":
    test_status_mapping()
