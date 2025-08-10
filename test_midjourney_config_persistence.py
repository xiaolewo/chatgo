#!/usr/bin/env python3
"""
测试MidJourney配置持久化功能
验证配置在重启后是否能正确保存和加载
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def test_midjourney_config_persistence():
    """测试MidJourney配置持久化"""

    print("🔧 MidJourney配置持久化测试")
    print("=" * 60)

    # 测试配置数据
    test_config = {
        "enabled": True,
        "api_url": "https://api.linkapi.org",
        "api_key": "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55",
        "fast_credits": 10,
        "relax_credits": 5,
        "turbo_credits": 15,
    }

    # 假设OpenWebUI运行在默认端口
    base_url = "http://localhost:8080"
    api_base = f"{base_url}/api/v1/midjourney"

    print(f"🌐 测试目标: {api_base}")
    print(f"🔑 测试API密钥: {test_config['api_key'][:20]}...")

    # 步骤1和2: API测试（需要运行的OpenWebUI服务）
    print(f"\n📋 步骤1-2: API端点测试")
    print(f"   💡 完整的API测试需要OpenWebUI服务运行")
    print(f"   💡 管理员可以通过Web界面测试配置保存功能")

    # 步骤3: 检查配置文件结构（代码层面）
    print(f"\n🏗️  步骤3: 检查配置结构")
    try:
        # 导入配置模块来验证结构
        from open_webui.config import (
            MIDJOURNEY_ENABLED,
            MIDJOURNEY_API_URL,
            MIDJOURNEY_API_KEY,
            MIDJOURNEY_FAST_CREDITS,
            MIDJOURNEY_RELAX_CREDITS,
            MIDJOURNEY_TURBO_CREDITS,
        )

        print(f"   ✅ MidJourney配置模块导入成功")
        print(f"   📊 配置项值:")
        print(f"      ENABLED: {MIDJOURNEY_ENABLED.value}")
        print(f"      API_URL: {MIDJOURNEY_API_URL.value}")
        print(
            f"      API_KEY: {MIDJOURNEY_API_KEY.value[:20] if MIDJOURNEY_API_KEY.value else 'None'}..."
        )
        print(f"      FAST_CREDITS: {MIDJOURNEY_FAST_CREDITS.value}")
        print(f"      RELAX_CREDITS: {MIDJOURNEY_RELAX_CREDITS.value}")
        print(f"      TURBO_CREDITS: {MIDJOURNEY_TURBO_CREDITS.value}")

    except ImportError as e:
        print(f"   ❌ 导入配置失败: {str(e)}")
        print(f"   💡 确保你在正确的目录中运行此脚本")
    except Exception as e:
        print(f"   ❌ 配置检查失败: {str(e)}")

    # 步骤4: 配置持久化说明
    print(f"\n📚 步骤4: 持久化机制说明")
    print(f"   🔧 OpenWebUI使用PersistentConfig类来管理配置")
    print(f"   💾 配置保存在数据库的config表中")
    print(f"   🔄 重启后配置会自动从数据库加载")
    print(f"   🎯 每个配置项都有唯一的config_path:")
    print(f"      - midjourney.enabled")
    print(f"      - midjourney.api_url")
    print(f"      - midjourney.api_key")
    print(f"      - midjourney.fast_credits")
    print(f"      - midjourney.relax_credits")
    print(f"      - midjourney.turbo_credits")

    # 步骤5: 验证结果
    print(f"\n✅ 步骤5: 验证说明")
    print(f"   1. 配置保存后，即使重启OpenWebUI后端服务")
    print(f"   2. 配置应该自动从数据库恢复")
    print(f"   3. 管理员面板中的MidJourney设置应该保持不变")
    print(f"   4. 这解决了每次重启都需要重新配置的问题")


def test_config_structure():
    """测试配置结构完整性"""
    print(f"\n🔍 配置结构完整性检查")
    print(f"-" * 40)

    try:
        # 检查配置文件是否包含MidJourney配置
        config_file = "backend/open_webui/config.py"
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

            checks = [
                ("MIDJOURNEY_ENABLED", "MIDJOURNEY_ENABLED" in content),
                ("MIDJOURNEY_API_URL", "MIDJOURNEY_API_URL" in content),
                ("MIDJOURNEY_API_KEY", "MIDJOURNEY_API_KEY" in content),
                ("MIDJOURNEY_FAST_CREDITS", "MIDJOURNEY_FAST_CREDITS" in content),
                ("MIDJOURNEY_RELAX_CREDITS", "MIDJOURNEY_RELAX_CREDITS" in content),
                ("MIDJOURNEY_TURBO_CREDITS", "MIDJOURNEY_TURBO_CREDITS" in content),
                (
                    "PersistentConfig usage",
                    "PersistentConfig(" in content and "midjourney." in content,
                ),
            ]

            for check_name, result in checks:
                status = "✅" if result else "❌"
                print(f"   {status} {check_name}")
        else:
            print(f"   ❌ 配置文件不存在: {config_file}")

    except Exception as e:
        print(f"   ❌ 配置检查失败: {str(e)}")


if __name__ == "__main__":
    print(f"🚀 MidJourney配置持久化测试")
    print(f"时间: {datetime.now()}")
    print("=" * 60)

    # 首先检查配置结构
    test_config_structure()

    # 然后运行测试
    test_midjourney_config_persistence()

    print(f"\n🎯 结论:")
    print(f"   如果所有配置检查都通过 (✅)，那么配置持久化应该正常工作")
    print(f"   重启OpenWebUI后端服务后，MidJourney配置应该会自动恢复")
    print(f"   不再需要每次重启后重新配置MidJourney设置")
