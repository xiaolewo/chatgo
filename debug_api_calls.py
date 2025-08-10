#!/usr/bin/env python3
"""
调试API调用，专门检查具体的错误
"""

import requests
import json
from datetime import datetime


def debug_api_calls():
    """调试API调用"""

    print("🔍 API调用调试")
    print("=" * 50)
    print(f"时间: {datetime.now()}")

    # OpenWebUI基础URL
    base_url = "http://localhost:8080"

    print(f"\n使用基础URL: {base_url}")

    # 1. 测试健康检查
    print(f"\n1️⃣ 测试基础连接...")
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        print(f"健康检查: {health_response.status_code}")

        if health_response.status_code != 200:
            print("❌ 基础服务不可用")
            return

    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return

    # 2. 测试MidJourney路由可用性
    print(f"\n2️⃣ 测试MidJourney路由...")

    routes_to_test = [
        ("/api/v1/midjourney/config", "GET"),
        ("/api/v1/midjourney/generate", "POST"),
    ]

    for route, method in routes_to_test:
        url = f"{base_url}{route}"
        print(f"\n测试: {method} {url}")

        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            elif method == "POST":
                response = requests.post(url, json={"test": "data"}, timeout=5)

            print(f"状态码: {response.status_code}")

            if response.status_code == 403:
                print("✅ 路由存在，需要认证")
            elif response.status_code == 404:
                print("❌ 路由不存在")
            elif response.status_code == 405:
                print("❌ 方法不允许（可能是路由注册问题）")
            elif response.status_code == 422:
                print("⚠️  参数验证失败（路由存在）")
            elif response.status_code == 500:
                print("❌ 服务器内部错误")
                try:
                    error_detail = response.json()
                    print(
                        f"错误详情: {json.dumps(error_detail, indent=2, ensure_ascii=False)}"
                    )
                except:
                    print(f"错误内容: {response.text}")
            else:
                print(f"其他状态: {response.status_code}")
                try:
                    content = response.json()
                    print(
                        f"响应内容: {json.dumps(content, indent=2, ensure_ascii=False)}"
                    )
                except:
                    print(f"响应文本: {response.text}")

        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")

    # 3. 检查是否是后端重启问题
    print(f"\n3️⃣ 检查后端状态...")

    # 尝试访问其他已知端点
    other_endpoints = ["/api/v1/models", "/api/v1/chats", "/api/config"]

    print("测试其他端点以确认后端服务状态:")
    for endpoint in other_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            status_text = "正常" if response.status_code in [200, 401, 403] else "异常"
            print(f"   {endpoint}: {response.status_code} ({status_text})")
        except:
            print(f"   {endpoint}: 连接失败")

    # 4. 给出具体指导
    print(f"\n4️⃣ 下一步调试指导")
    print()
    print("A. 如果MidJourney路由返回404或405:")
    print("   1. 确认后端服务已重启:")
    print("      docker restart openwebui")
    print("      # 或其他重启命令")
    print()
    print("   2. 检查后端日志:")
    print("      docker logs openwebui --tail 100")
    print("      # 查找MidJourney相关的加载信息")
    print()
    print("B. 如果路由返回403（需要认证）:")
    print("   1. 在浏览器中打开开发者工具")
    print("   2. 尝试生成图像")
    print("   3. 在Network标签中查看具体的失败请求")
    print("   4. 记录错误的HTTP状态码和响应内容")
    print()
    print("C. 如果路由返回500:")
    print("   1. 检查上面显示的错误详情")
    print("   2. 查看后端日志获取完整错误信息")
    print("   3. 可能是配置或导入问题")
    print()
    print("⚠️  重要提醒:")
    print("   如果任何MidJourney路由返回404，说明后端修改没有生效")
    print("   这通常意味着需要完全重启后端服务")


if __name__ == "__main__":
    debug_api_calls()
