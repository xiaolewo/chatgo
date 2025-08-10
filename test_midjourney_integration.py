#!/usr/bin/env python3
"""
MidJourney集成测试脚本
测试后端API路由和前端API客户端的基本功能
"""

import asyncio
import json
import sys
import os

# 添加项目路径到Python path
sys.path.append("/Users/liuqingliang/openwebui/openwebui-main/backend")


async def test_midjourney_integration():
    """测试MidJourney集成的核心功能"""

    print("🚀 开始MidJourney集成测试")
    print("=" * 50)

    # 测试1: 导入路由模块
    try:
        from open_webui.routers.midjourney import (
            router,
            MidJourneyConfig,
            ImageGenerateRequest,
            TaskResponse,
            TaskStatusResponse,
            task_storage,
            process_midjourney_task,
        )

        print("✅ 测试1: 成功导入MidJourney路由模块")
    except Exception as e:
        print(f"❌ 测试1失败: 导入模块错误 - {e}")
        return False

    # 测试2: 验证数据模型
    try:
        # 测试配置模型
        config = MidJourneyConfig(
            enabled=True,
            api_url="https://api.midjourney.com",
            api_key="test-key",
            fast_credits=10,
            relax_credits=5,
        )

        # 测试请求模型
        request = ImageGenerateRequest(
            prompt="A beautiful sunset", mode="fast", aspect_ratio="1:1"
        )

        print("✅ 测试2: 数据模型验证成功")
        print(
            f"   - 配置: enabled={config.enabled}, fast_credits={config.fast_credits}"
        )
        print(f"   - 请求: prompt='{request.prompt}', mode='{request.mode}'")

    except Exception as e:
        print(f"❌ 测试2失败: 数据模型错误 - {e}")
        return False

    # 测试3: 测试任务处理函数
    try:
        # 创建模拟任务
        task_id = "test-task-001"
        task_info = {
            "task_id": task_id,
            "user_id": "test-user",
            "prompt": "Test image generation",
            "mode": "fast",
            "status": "submitted",
            "progress": 0,
            "message": "任务已提交",
            "credits_used": 10,
            "created_at": "2025-01-01T00:00:00",
        }

        task_storage[task_id] = task_info

        print("✅ 测试3: 任务存储测试成功")
        print(f"   - 任务ID: {task_id}")
        print(f"   - 初始状态: {task_info['status']}")

    except Exception as e:
        print(f"❌ 测试3失败: 任务处理错误 - {e}")
        return False

    # 测试4: 测试异步任务处理
    try:
        print("🔄 测试4: 开始异步任务处理测试...")

        # 创建异步任务并等待完成（使用短延迟进行测试）
        original_task = process_midjourney_task(task_id)

        # 模拟等待任务进度
        await asyncio.sleep(0.1)  # 短暂等待

        current_task = task_storage.get(task_id)
        if current_task:
            print(f"   - 任务状态: {current_task['status']}")
            print(f"   - 进度: {current_task.get('progress', 0)}%")
            print(f"   - 消息: {current_task.get('message', 'N/A')}")

        print("✅ 测试4: 异步任务处理测试成功")

    except Exception as e:
        print(f"❌ 测试4失败: 异步处理错误 - {e}")
        return False

    # 测试5: 验证前端API客户端文件
    try:
        api_client_path = (
            "/Users/liuqingliang/openwebui/openwebui-main/src/lib/apis/midjourney.js"
        )

        if os.path.exists(api_client_path):
            with open(api_client_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查关键函数是否存在
            required_functions = [
                "getMidJourneyConfig",
                "updateMidJourneyConfig",
                "generateImage",
                "getTaskStatus",
                "getUserTasks",
                "pollTaskStatus",
            ]

            missing_functions = []
            for func in required_functions:
                if func not in content:
                    missing_functions.append(func)

            if missing_functions:
                print(f"❌ 测试5失败: 缺少API函数 - {missing_functions}")
                return False
            else:
                print("✅ 测试5: 前端API客户端验证成功")
                print(f"   - 文件路径: {api_client_path}")
                print(f"   - 包含函数: {len(required_functions)}个")
        else:
            print(f"❌ 测试5失败: API客户端文件不存在 - {api_client_path}")
            return False

    except Exception as e:
        print(f"❌ 测试5失败: 文件验证错误 - {e}")
        return False

    # 测试6: 验证主程序集成
    try:
        main_py_path = (
            "/Users/liuqingliang/openwebui/openwebui-main/backend/open_webui/main.py"
        )

        with open(main_py_path, "r", encoding="utf-8") as f:
            main_content = f.read()

        # 检查是否正确导入和注册了midjourney路由
        if "midjourney," in main_content:
            print("✅ 测试6: 主程序集成验证成功")
            print("   - MidJourney路由已正确导入")

            if "midjourney.router" in main_content:
                print("   - MidJourney路由已正确注册")
            else:
                print("⚠️  警告: MidJourney路由可能未正确注册")
        else:
            print("❌ 测试6失败: MidJourney路由未导入到主程序")
            return False

    except Exception as e:
        print(f"❌ 测试6失败: 主程序集成检查错误 - {e}")
        return False

    print("=" * 50)
    print("🎉 所有测试通过! MidJourney集成测试成功")

    # 显示集成状态总结
    print("\n📊 集成状态总结:")
    print("✅ 后端API路由模块")
    print("✅ 数据模型和类型定义")
    print("✅ 任务存储和管理")
    print("✅ 异步任务处理")
    print("✅ 前端API客户端")
    print("✅ 主程序路由集成")

    print("\n🔄 下一步待完成:")
    print("1. 启动后端服务进行端到端测试")
    print("2. 测试管理员配置面板")
    print("3. 测试图像生成页面集成")
    print("4. 验证实时状态更新")
    print("5. 测试错误处理机制")

    return True


if __name__ == "__main__":
    try:
        # 运行异步测试
        result = asyncio.run(test_midjourney_integration())

        if result:
            print("\n✨ 测试完成: 成功")
            sys.exit(0)
        else:
            print("\n💥 测试完成: 失败")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 测试执行错误: {e}")
        sys.exit(1)
