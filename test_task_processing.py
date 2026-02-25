#!/usr/bin/env python3
"""
Test script for MidJourney task processing logic
"""

import asyncio
import sys
import uuid
from datetime import datetime

# Add the backend directory to Python path
sys.path.append("./backend")

# Import the MidJourney modules
from open_webui.routers.midjourney import process_midjourney_task, task_storage


async def test_task_processing():
    """Test the simplified task processing logic"""
    print("🧪 Testing MidJourney task processing...")

    # Create a test task
    task_id = str(uuid.uuid4())
    task_info = {
        "task_id": task_id,
        "user_id": "test_user",
        "prompt": "A beautiful landscape with mountains and lakes",
        "final_prompt": "A beautiful landscape with mountains and lakes --chaos 50 --stylize 100",
        "mode": "fast",
        "aspect_ratio": "1:1",
        "status": "submitted",
        "progress": 0,
        "image_url": None,
        "message": "任务已提交，等待处理",
        "credits_used": 10,
        "created_at": datetime.now(),
        "completed_at": None,
        "error_message": None,
        "actions": [],
        "seed": None,
        "advanced_params": {"chaos": 50, "stylize": 100},
    }

    # Store the task
    task_storage[task_id] = task_info
    print(f"✅ Test task created: {task_id}")
    print(
        f"📊 Initial status: {task_info['status']}, progress: {task_info['progress']}%"
    )

    # Process the task
    print("🚀 Starting task processing...")
    await process_midjourney_task(task_id)

    # Check final status
    final_task = task_storage[task_id]
    print(
        f"📊 Final status: {final_task['status']}, progress: {final_task['progress']}%"
    )
    print(f"💬 Final message: {final_task['message']}")
    print(
        f"🖼️  Image URL: {'✅ Generated' if final_task.get('image_url') else '❌ Missing'}"
    )
    print(f"🎮 Actions available: {len(final_task.get('actions', []))}")
    print(f"🌱 Seed: {final_task.get('seed', 'Not set')}")

    # Verify completion
    success = (
        final_task["status"] == "completed"
        and final_task["progress"] == 100
        and final_task.get("image_url") is not None
        and len(final_task.get("actions", [])) > 0
    )

    return success


async def test_action_processing():
    """Test action processing logic"""
    print("\n🎮 Testing MidJourney action processing...")

    # Import action processing function
    from open_webui.routers.midjourney import process_action_task

    # Create a test action task
    action_task_id = str(uuid.uuid4())
    action_task_info = {
        "task_id": action_task_id,
        "user_id": "test_user",
        "parent_task_id": "parent_123",
        "action_type": "upscale",
        "button_index": 0,
        "custom_id": "MJ::JOB::upsample::1::test",
        "prompt": "Test action prompt",
        "status": "submitted",
        "progress": 0,
        "image_url": None,
        "message": "正在执行upscale操作",
        "credits_used": 5,
        "created_at": datetime.now(),
        "completed_at": None,
        "actions": [],
    }

    task_storage[action_task_id] = action_task_info
    print(f"✅ Test action task created: {action_task_id}")

    # Process the action task
    await process_action_task(action_task_id)

    # Check results
    final_action_task = task_storage[action_task_id]
    print(f"📊 Action final status: {final_action_task['status']}")
    print(f"💬 Action final message: {final_action_task['message']}")
    print(
        f"🖼️  Action image URL: {'✅ Generated' if final_action_task.get('image_url') else '❌ Missing'}"
    )

    return final_action_task["status"] == "completed"


async def main():
    """Run all tests"""
    print("🏃 Running MidJourney integration tests...\n")

    try:
        # Test basic task processing
        test1_passed = await test_task_processing()

        # Test action processing
        test2_passed = await test_action_processing()

        print(f"\n📋 Test Results:")
        print(f"✅ Basic task processing: {'PASSED' if test1_passed else 'FAILED'}")
        print(f"✅ Action processing: {'PASSED' if test2_passed else 'FAILED'}")

        overall_success = test1_passed and test2_passed
        print(
            f"\n🎯 Overall test result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
        )

        if overall_success:
            print("\n🚀 The simplified task processing logic is working correctly!")
            print("   ✅ Tasks complete successfully")
            print("   ✅ Progress updates properly")
            print("   ✅ Images are generated")
            print("   ✅ Action buttons are created")

        return overall_success

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
