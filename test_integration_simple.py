#!/usr/bin/env python3
"""
简化的MidJourney集成验证测试
检查文件存在性、代码结构和基本逻辑
"""

import os
import re
import json


def test_file_structure():
    """测试文件结构和存在性"""
    print("🔍 测试1: 文件结构验证")

    files_to_check = [
        {
            "path": "backend/open_webui/routers/midjourney.py",
            "description": "后端MidJourney路由",
            "required_content": ["router =", "MidJourneyConfig", "generate_image"],
        },
        {
            "path": "src/lib/apis/midjourney.js",
            "description": "前端API客户端",
            "required_content": [
                "export const",
                "getMidJourneyConfig",
                "generateImage",
            ],
        },
        {
            "path": "src/lib/components/admin/Settings/MidJourney.svelte",
            "description": "MidJourney管理配置组件",
            "required_content": ["Switch", "config", "saveHandler"],
        },
        {
            "path": "src/routes/(app)/image-generation/+page.svelte",
            "description": "图像生成页面",
            "required_content": ["generateImage", "selectedMode", "midjourney"],
        },
    ]

    success_count = 0

    for file_info in files_to_check:
        file_path = file_info["path"]
        description = file_info["description"]
        required_content = file_info["required_content"]

        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                missing_content = []
                for required in required_content:
                    if required not in content:
                        missing_content.append(required)

                if missing_content:
                    print(f"⚠️  {description}: 文件存在但缺少内容 - {missing_content}")
                else:
                    print(f"✅ {description}: 验证通过")
                    success_count += 1

            except Exception as e:
                print(f"❌ {description}: 读取错误 - {e}")
        else:
            print(f"❌ {description}: 文件不存在 - {file_path}")

    print(f"\n📊 文件结构测试结果: {success_count}/{len(files_to_check)} 通过")
    return success_count == len(files_to_check)


def test_backend_router():
    """测试后端路由代码"""
    print("\n🔍 测试2: 后端路由代码验证")

    router_path = "backend/open_webui/routers/midjourney.py"

    if not os.path.exists(router_path):
        print("❌ 后端路由文件不存在")
        return False

    try:
        with open(router_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查关键路由端点
        endpoints = [
            ('@router.get("/config"', "获取配置"),
            ('@router.post("/config"', "更新配置"),
            ('@router.post("/generate"', "生成图像"),
            ('@router.get("/task/{task_id}"', "查询任务状态"),
            ('@router.get("/tasks"', "获取任务列表"),
            ('@router.delete("/task/{task_id}"', "取消任务"),
        ]

        missing_endpoints = []
        for endpoint, desc in endpoints:
            if endpoint not in content:
                missing_endpoints.append(f"{desc}({endpoint})")

        if missing_endpoints:
            print(f"❌ 缺少路由端点: {missing_endpoints}")
            return False

        # 检查关键数据模型
        models = [
            "MidJourneyConfig",
            "ImageGenerateRequest",
            "TaskResponse",
            "TaskStatusResponse",
        ]
        missing_models = []
        for model in models:
            if f"class {model}" not in content:
                missing_models.append(model)

        if missing_models:
            print(f"❌ 缺少数据模型: {missing_models}")
            return False

        # 检查异步任务处理函数
        if "async def process_midjourney_task" not in content:
            print("❌ 缺少异步任务处理函数")
            return False

        print("✅ 后端路由代码验证通过")
        print("   - 6个API端点完整")
        print("   - 4个数据模型完整")
        print("   - 异步任务处理功能完整")

        return True

    except Exception as e:
        print(f"❌ 后端路由验证错误: {e}")
        return False


def test_frontend_api():
    """测试前端API客户端"""
    print("\n🔍 测试3: 前端API客户端验证")

    api_path = "src/lib/apis/midjourney.js"

    if not os.path.exists(api_path):
        print("❌ 前端API文件不存在")
        return False

    try:
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查导出的API函数
        api_functions = [
            "getMidJourneyConfig",
            "updateMidJourneyConfig",
            "generateImage",
            "getTaskStatus",
            "getUserTasks",
            "cancelTask",
            "pollTaskStatus",
            "generateImageWithPolling",
        ]

        missing_functions = []
        for func in api_functions:
            if f"export const {func}" not in content:
                missing_functions.append(func)

        if missing_functions:
            print(f"❌ 缺少API函数: {missing_functions}")
            return False

        # 检查常量定义
        constants = ["TASK_STATUS", "GENERATION_MODE", "ASPECT_RATIOS"]
        missing_constants = []
        for const in constants:
            if f"export const {const}" not in content:
                missing_constants.append(const)

        if missing_constants:
            print(f"❌ 缺少常量定义: {missing_constants}")
            return False

        print("✅ 前端API客户端验证通过")
        print(f"   - {len(api_functions)}个API函数完整")
        print(f"   - {len(constants)}个常量定义完整")

        return True

    except Exception as e:
        print(f"❌ 前端API验证错误: {e}")
        return False


def test_main_integration():
    """测试主程序集成"""
    print("\n🔍 测试4: 主程序集成验证")

    main_path = "backend/open_webui/main.py"

    if not os.path.exists(main_path):
        print("❌ 主程序文件不存在")
        return False

    try:
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 检查导入
        if "midjourney," not in content:
            print("❌ MidJourney模块未导入")
            return False

        # 检查路由注册
        if "app.include_router(midjourney.router" not in content:
            print("❌ MidJourney路由未注册")
            return False

        # 检查路由前缀
        if '"/api/v1/midjourney"' not in content:
            print("❌ MidJourney路由前缀不正确")
            return False

        print("✅ 主程序集成验证通过")
        print("   - 模块正确导入")
        print("   - 路由正确注册")
        print("   - API前缀配置正确")

        return True

    except Exception as e:
        print(f"❌ 主程序集成验证错误: {e}")
        return False


def test_admin_settings():
    """测试管理员设置组件"""
    print("\n🔍 测试5: 管理员设置组件验证")

    # 检查MidJourney设置组件
    midjourney_path = "src/lib/components/admin/Settings/MidJourney.svelte"
    settings_path = "src/lib/components/admin/Settings.svelte"

    tests_passed = 0

    # 测试MidJourney组件
    if os.path.exists(midjourney_path):
        try:
            with open(midjourney_path, "r", encoding="utf-8") as f:
                content = f.read()

            required_elements = [
                "Switch bind:state={config.enabled}",
                "api_url",
                "api_key",
                "fast_credits",
                "relax_credits",
                "saveHandler",
            ]

            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)

            if missing_elements:
                print(f"⚠️  MidJourney组件: 缺少元素 - {missing_elements}")
            else:
                print("✅ MidJourney设置组件: 验证通过")
                tests_passed += 1

        except Exception as e:
            print(f"❌ MidJourney组件验证错误: {e}")
    else:
        print("❌ MidJourney设置组件文件不存在")

    # 测试Settings主组件集成
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查MidJourney标签页
            if (
                "selectedTab === 'midjourney'" in content
                and "import MidJourney" in content
            ):
                print("✅ Settings主组件: MidJourney集成验证通过")
                tests_passed += 1
            else:
                print("❌ Settings主组件: MidJourney集成不完整")

        except Exception as e:
            print(f"❌ Settings主组件验证错误: {e}")
    else:
        print("❌ Settings主组件文件不存在")

    return tests_passed == 2


def main():
    """主测试函数"""
    print("🚀 MidJourney集成简化验证测试")
    print("=" * 60)

    # 切换到项目根目录
    os.chdir("/Users/liuqingliang/openwebui/openwebui-main")

    test_results = []

    # 运行各项测试
    test_results.append(test_file_structure())
    test_results.append(test_backend_router())
    test_results.append(test_frontend_api())
    test_results.append(test_main_integration())
    test_results.append(test_admin_settings())

    # 统计结果
    passed = sum(test_results)
    total = len(test_results)

    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print(f"✅ 通过: {passed}/{total} 项测试")

    if passed == total:
        print("🎉 所有测试通过! MidJourney集成基础结构验证成功")

        print("\n📋 已完成的集成组件:")
        print("✅ 后端API路由模块 (6个端点)")
        print("✅ 前端API客户端 (8个函数)")
        print("✅ 数据模型和类型定义")
        print("✅ 主程序路由集成")
        print("✅ 管理员配置界面")

        print("\n🔄 下一步计划:")
        print("1. 启动开发服务器进行端到端测试")
        print("2. 测试管理员配置保存/加载")
        print("3. 测试图像生成流程和任务状态")
        print("4. 优化前端组件的实时状态更新")
        print("5. 完善错误处理和用户反馈")

        return True
    else:
        print(f"⚠️  {total - passed} 项测试未通过，需要修复")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        exit(130)
    except Exception as e:
        print(f"\n💥 测试执行错误: {e}")
        exit(1)
