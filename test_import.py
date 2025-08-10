#!/usr/bin/env python3
"""
测试导入是否有问题
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


def test_imports():
    print("🧪 测试导入...")

    try:
        print("1. 测试config导入...")
        from open_webui.config import MIDJOURNEY_ENABLED

        print(f"   ✅ MIDJOURNEY_ENABLED = {MIDJOURNEY_ENABLED.value}")
    except Exception as e:
        print(f"   ❌ config导入失败: {e}")
        return False

    try:
        print("2. 测试midjourney路由导入...")
        from open_webui.routers import midjourney

        print(f"   ✅ midjourney路由导入成功")
    except Exception as e:
        print(f"   ❌ midjourney路由导入失败: {e}")
        return False

    try:
        print("3. 测试main导入...")
        from open_webui import main

        print(f"   ✅ main导入成功")
    except Exception as e:
        print(f"   ❌ main导入失败: {e}")
        return False

    return True


if __name__ == "__main__":
    if test_imports():
        print("\n✅ 所有导入测试通过")
    else:
        print("\n❌ 导入测试失败")
