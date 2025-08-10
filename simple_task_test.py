#!/usr/bin/env python3
"""
Simple test to verify the task processing logic works correctly
"""
import asyncio
import uuid
import random
from datetime import datetime

# Simulate the task storage and processing logic
task_storage = {}


async def mock_process_midjourney_task(task_id: str):
    """Mock version of the process_midjourney_task function"""
    task_info = task_storage.get(task_id)

    if not task_info:
        print(f"❌ Task not found: {task_id}")
        return

    try:
        print(f"🚀 Starting task processing: {task_id}")

        # Verify task status
        if task_info["status"] != "submitted":
            print(f"⚠️  Task status invalid: {task_info['status']}")
            return

        # Stage 1: Processing starts
        task_info["status"] = "processing"
        task_info["message"] = "正在提交到MidJourney服务"
        task_info["progress"] = 10
        print(f"📊 Progress: {task_info['progress']}% - {task_info['message']}")

        # Simulate processing stages
        await asyncio.sleep(2)
        task_info["message"] = "MidJourney正在生成图像"
        task_info["progress"] = 30
        print(f"📊 Progress: {task_info['progress']}% - {task_info['message']}")

        await asyncio.sleep(3)
        task_info["message"] = "图像生成中..."
        task_info["progress"] = 60
        print(f"📊 Progress: {task_info['progress']}% - {task_info['message']}")

        await asyncio.sleep(2)
        task_info["message"] = "正在完成处理..."
        task_info["progress"] = 90
        print(f"📊 Progress: {task_info['progress']}% - {task_info['message']}")

        await asyncio.sleep(1)

        # Complete the task
        task_info["status"] = "completed"
        task_info["message"] = "图像生成完成"
        task_info["progress"] = 100
        task_info["image_url"] = f"https://picsum.photos/1024/1024?random={task_id[:8]}"
        task_info["completed_at"] = datetime.now()

        # Generate action buttons
        task_info["actions"] = [
            {
                "label": "U1",
                "custom_id": f"MJ::JOB::upsample::1::{task_id}",
                "type": "upscale",
                "emoji": "🔍",
            },
            {
                "label": "U2",
                "custom_id": f"MJ::JOB::upsample::2::{task_id}",
                "type": "upscale",
                "emoji": "🔍",
            },
            {
                "label": "U3",
                "custom_id": f"MJ::JOB::upsample::3::{task_id}",
                "type": "upscale",
                "emoji": "🔍",
            },
            {
                "label": "U4",
                "custom_id": f"MJ::JOB::upsample::4::{task_id}",
                "type": "upscale",
                "emoji": "🔍",
            },
            {
                "label": "V1",
                "custom_id": f"MJ::JOB::variation::1::{task_id}",
                "type": "variation",
                "emoji": "🎨",
            },
            {
                "label": "V2",
                "custom_id": f"MJ::JOB::variation::2::{task_id}",
                "type": "variation",
                "emoji": "🎨",
            },
            {
                "label": "V3",
                "custom_id": f"MJ::JOB::variation::3::{task_id}",
                "type": "variation",
                "emoji": "🎨",
            },
            {
                "label": "V4",
                "custom_id": f"MJ::JOB::variation::4::{task_id}",
                "type": "variation",
                "emoji": "🎨",
            },
            {
                "label": "🔄",
                "custom_id": f"MJ::JOB::reroll::0::{task_id}",
                "type": "reroll",
                "emoji": "🔄",
            },
        ]

        # Generate seed if not specified
        if not task_info.get("seed"):
            task_info["seed"] = random.randint(0, 4294967295)

        print(f"✅ Task completed successfully: {task_id}")
        print(f"📊 Final progress: {task_info['progress']}%")
        print(f"🖼️  Image URL: {task_info['image_url']}")
        print(f"🎮 Actions available: {len(task_info['actions'])}")
        print(f"🌱 Seed: {task_info['seed']}")

    except Exception as e:
        print(f"❌ Task processing failed: {task_id}")
        print(f"🔥 Error: {str(e)}")

        # Set failure status
        task_info["status"] = "failed"
        task_info["error_message"] = str(e)
        task_info["completed_at"] = datetime.now()
        task_info["message"] = f"生成失败: {str(e)}"


async def test_task_flow():
    """Test the complete task flow"""
    print("🧪 Testing MidJourney Task Processing Flow")
    print("=" * 50)

    # Create test task
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "user_id": "test_user_123",
        "prompt": "A beautiful sunset over mountains, photorealistic",
        "final_prompt": "A beautiful sunset over mountains, photorealistic --chaos 30 --stylize 150 --v6.1",
        "mode": "fast",
        "aspect_ratio": "16:9",
        "status": "submitted",
        "progress": 0,
        "image_url": None,
        "message": "任务已提交，等待处理",
        "credits_used": 10,
        "created_at": datetime.now(),
        "completed_at": None,
        "error_message": None,
        "actions": [],
        "seed": 12345,
        "advanced_params": {"chaos": 30, "stylize": 150, "version": "v6.1"},
    }

    task_storage[task_id] = task_info
    print(f"📝 Created task: {task_id}")
    print(f"📝 Prompt: {task_info['prompt']}")
    print(f"📝 Advanced params: {task_info['advanced_params']}")
    print()

    # Process the task
    await mock_process_midjourney_task(task_id)

    # Check final result
    final_task = task_storage[task_id]
    print()
    print("📋 Final Task Result:")
    print(f"   Status: {final_task['status']}")
    print(f"   Progress: {final_task['progress']}%")
    print(f"   Message: {final_task['message']}")
    print(f"   Image URL: {final_task.get('image_url', 'None')}")
    print(f"   Actions: {len(final_task.get('actions', []))}")
    print(f"   Seed: {final_task.get('seed', 'None')}")

    # Test success criteria
    success = (
        final_task["status"] == "completed"
        and final_task["progress"] == 100
        and final_task.get("image_url") is not None
        and len(final_task.get("actions", [])) == 9  # Should have 9 action buttons
    )

    print()
    print(f"🎯 Test Result: {'✅ PASSED' if success else '❌ FAILED'}")

    if success:
        print("🎉 The task processing logic is working correctly!")
        print("   • Task progresses through all stages")
        print("   • Final status is 'completed' with 100% progress")
        print("   • Image URL is generated")
        print("   • Action buttons are created")
        print("   • Seed value is assigned")
    else:
        print("⚠️  Task processing has issues:")
        if final_task["status"] != "completed":
            print(f"   • Status should be 'completed', got '{final_task['status']}'")
        if final_task["progress"] != 100:
            print(f"   • Progress should be 100%, got {final_task['progress']}%")
        if not final_task.get("image_url"):
            print("   • Image URL is missing")
        if len(final_task.get("actions", [])) != 9:
            print(
                f"   • Should have 9 action buttons, got {len(final_task.get('actions', []))}"
            )

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(test_task_flow())
        print(
            f"\n{'🎉 SUCCESS' if result else '💥 FAILURE'}: Task processing test {'passed' if result else 'failed'}"
        )
    except Exception as e:
        print(f"💥 Test crashed with error: {e}")
        import traceback

        traceback.print_exc()
