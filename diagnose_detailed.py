#!/usr/bin/env python3
"""
详细诊断MidJourney问题
生成调试信息帮助用户查找问题
"""

import requests
import json
from datetime import datetime


def diagnose_detailed():
    """详细诊断"""

    print("🔍 MidJourney详细诊断")
    print("=" * 60)
    print(f"时间: {datetime.now()}")

    # 检查1: 后端服务状态
    print("\n1️⃣ 检查后端服务状态")
    openwebui_endpoints = ["http://localhost:8080", "http://127.0.0.1:8080"]

    working_endpoint = None
    for endpoint in openwebui_endpoints:
        try:
            response = requests.get(f"{endpoint}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - 服务运行中")
                working_endpoint = endpoint
                break
            else:
                print(f"   ❌ {endpoint} - HTTP {response.status_code}")
        except:
            print(f"   ❌ {endpoint} - 无法连接")

    if not working_endpoint:
        print("\n❌ 后端服务未运行，请先启动OpenWebUI服务")
        return

    # 检查2: MidJourney路由
    print(f"\n2️⃣ 检查MidJourney路由 ({working_endpoint})")
    midjourney_routes = [
        "/api/v1/midjourney/config",
        "/api/v1/midjourney/generate",
    ]

    for route in midjourney_routes:
        try:
            response = requests.get(f"{working_endpoint}{route}", timeout=5)
            if response.status_code == 403:
                print(f"   ✅ {route} - 存在（需要认证）")
            elif response.status_code == 404:
                print(f"   ❌ {route} - 不存在（路由问题）")
            else:
                print(f"   ℹ️  {route} - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {route} - 错误: {str(e)}")

    # 检查3: 生成调试指南
    print(f"\n3️⃣ 前端调试指南")
    print("请按以下步骤在浏览器中调试：")
    print()
    print("A. 打开浏览器开发者工具：")
    print("   - 按F12或右键→检查元素")
    print("   - 切换到 Network（网络）标签")
    print("   - 清空现有请求")
    print()
    print("B. 尝试生成图像：")
    print("   - 在OpenWebUI中输入提示词")
    print("   - 点击生成按钮")
    print("   - 观察Network标签中出现的请求")
    print()
    print("C. 查找失败的API请求：")
    print("   - 寻找红色（失败）的请求")
    print("   - 通常是类似这样的URL：")
    print(f"     • {working_endpoint}/api/v1/midjourney/generate")
    print(f"     • {working_endpoint}/api/v1/midjourney/task/[任务ID]")
    print()
    print("D. 检查失败请求的详细信息：")
    print("   - 点击失败的请求")
    print("   - 查看Headers标签：")
    print("     → 确认Authorization头是否存在")
    print("     → 确认Content-Type是application/json")
    print("   - 查看Response标签：")
    print("     → 记录HTTP状态码")
    print("     → 记录错误消息内容")
    print()

    # 检查4: 常见问题解决方案
    print("4️⃣ 常见问题及解决方案")
    print()
    print("如果看到403 Forbidden：")
    print("   → 检查是否已登录OpenWebUI")
    print("   → 检查是否有管理员权限")
    print("   → 刷新页面重新登录")
    print()
    print("如果看到404 Not Found：")
    print("   → 后端服务可能没有正确重启")
    print("   → MidJourney路由可能没有加载")
    print("   → 执行: docker restart openwebui")
    print()
    print("如果看到500 Internal Server Error：")
    print("   → 查看后端日志: docker logs openwebui --tail 100")
    print("   → 检查MidJourney配置是否正确")
    print("   → 检查API密钥是否有效")
    print()
    print("如果任务一直是'等待处理'状态：")
    print("   → 这是正常的，MidJourney任务需要时间")
    print("   → 等待1-2分钟后再检查")
    print("   → 检查API配额是否充足")
    print()

    # 检查5: 重启检查清单
    print("5️⃣ 重启检查清单")
    print()
    print("请确认以下步骤已完成：")
    print("□ 后端代码已修改（查询路径和状态映射）")
    print("□ 后端服务已重启")
    print("□ 浏览器缓存已清除")
    print("□ 管理员面板中MidJourney配置已保存")
    print("□ API密钥已更新为: sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
    print()

    print("=" * 60)
    print("📞 如果问题仍然存在：")
    print("1. 请提供浏览器Network标签中失败请求的详细信息")
    print("2. 请提供后端日志中的相关错误信息")
    print("3. 确认上述检查清单中的所有项目都已完成")


if __name__ == "__main__":
    diagnose_detailed()
