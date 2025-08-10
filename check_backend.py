#!/usr/bin/env python3
"""
简单检查后端服务状态的脚本
"""

import httpx
import asyncio
import json


async def check_backend():
    """检查后端服务状态"""
    backend_url = "http://localhost:8080"

    print("=== 检查后端服务状态 ===\n")

    # 1. 检查后端服务是否运行
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{backend_url}/health")
            if response.is_success:
                print("✅ 后端服务正在运行")
            else:
                print(f"❌ 后端服务异常: HTTP {response.status_code}")
                return
    except Exception as e:
        print(f"❌ 无法连接到后端服务 (http://localhost:8080)")
        print(f"   错误: {e}")
        print("\n💡 解决方案:")
        print("   1. 检查后端服务是否启动")
        print("   2. 确认端口8080没有被占用")
        print("   3. 检查防火墙设置")
        return

    # 2. 检查可灵配置
    print("\n=== 检查可灵API配置 ===")
    try:
        # 注意：这里需要一个有效的用户token，实际使用时需要替换
        # 由于没有token，我们只能检查接口是否可访问
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{backend_url}/api/v1/kling/config")
            print(f"可灵配置接口状态: HTTP {response.status_code}")

            if response.status_code == 401:
                print("⚠️ 需要认证token才能访问配置")
            elif response.status_code == 404:
                print("❌ 可灵API路由不存在")
            elif response.is_success:
                print("✅ 可灵配置接口可访问")

    except Exception as e:
        print(f"❌ 检查可灵配置失败: {e}")


def main():
    print("开始检查后端服务状态...\n")
    asyncio.run(check_backend())

    print("\n=== 诊断建议 ===")
    print("如果后端服务未运行，请:")
    print("1. 确保安装了所有依赖")
    print("2. 启动后端服务")
    print("3. 检查可灵API配置是否正确设置")
    print("   - KLING_API_URL: 可灵API的基础URL")
    print("   - KLING_API_KEY: 可灵API的认证密钥")


if __name__ == "__main__":
    main()
