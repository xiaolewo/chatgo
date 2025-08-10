#!/usr/bin/env python3
"""
测试OpenWebUI后端的MidJourney端点
验证任务提交和状态查询是否正常工作
"""

import json
import time
from datetime import datetime


def test_openwebui_backend():
    """测试OpenWebUI后端端点"""

    print("🧪 OpenWebUI后端MidJourney端点测试")
    print("=" * 60)
    print(f"时间: {datetime.now()}")

    # 尝试不同的端口
    base_urls = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    for base_url in base_urls:
        print(f"\n🌐 测试端点: {base_url}")
        test_single_endpoint(base_url)


def test_single_endpoint(base_url):
    """测试单个端点"""
    try:
        import requests

        # 1. 测试健康检查
        try:
            health_response = requests.get(f"{base_url}/health", timeout=5)
            if health_response.status_code == 200:
                print(f"   ✅ 健康检查通过")
            else:
                print(f"   ❌ 健康检查失败: {health_response.status_code}")
                return
        except:
            print(f"   ❌ 无法连接到服务")
            return

        # 2. 测试MidJourney配置端点（不需要认证的信息）
        try:
            config_url = f"{base_url}/api/v1/midjourney/config"
            config_response = requests.get(config_url, timeout=5)
            print(f"   📋 配置端点状态: {config_response.status_code}")
            if config_response.status_code == 403:
                print(f"      🔒 需要管理员权限 (端点存在)")
            elif config_response.status_code == 404:
                print(f"      ❌ MidJourney路由未找到")
            else:
                print(f"      ℹ️  其他状态")
        except Exception as e:
            print(f"   ❌ 配置端点测试失败: {str(e)}")

        # 3. 测试任务提交端点（同样会因为认证失败，但能测试路由）
        try:
            generate_url = f"{base_url}/api/v1/midjourney/generate"
            test_payload = {"prompt": "test image", "mode": "fast"}
            generate_response = requests.post(
                generate_url, json=test_payload, timeout=5
            )
            print(f"   🚀 生成端点状态: {generate_response.status_code}")
            if generate_response.status_code == 401:
                print(f"      🔐 需要认证 (端点存在)")
            elif generate_response.status_code == 404:
                print(f"      ❌ MidJourney生成路由未找到")
            else:
                print(f"      ℹ️  状态: {generate_response.status_code}")
        except Exception as e:
            print(f"   ❌ 生成端点测试失败: {str(e)}")

    except ImportError:
        print(f"   ⚠️  requests库未安装，跳过HTTP测试")
        print(f"   💡 手动验证方法:")
        print(f"   curl {base_url}/health")
        print(f"   curl {base_url}/api/v1/midjourney/config")


def check_configuration_instructions():
    """显示配置检查说明"""
    print(f"\n🔧 手动验证步骤:")
    print(f"1. 确认OpenWebUI服务正在运行:")
    print(f"   - 检查进程: ps aux | grep openwebui")
    print(f"   - 检查端口: netstat -tlnp | grep :8080")
    print(f"")
    print(f"2. 登录管理员账户并检查MidJourney配置:")
    print(f"   - 打开 http://localhost:8080 (或你的OpenWebUI地址)")
    print(f"   - 登录管理员账户")
    print(f"   - 进入 设置 → MidJourney配置")
    print(f"   - 确认配置:")
    print(f"     ✓ 启用MidJourney: 已勾选")
    print(f"     ✓ API URL: https://api.linkapi.org")
    print(f"     ✓ API Key: sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
    print(f"     ✓ Fast模式积分: 10")
    print(f"     ✓ Relax模式积分: 5")
    print(f"     ✓ Turbo模式积分: 15")
    print(f"   - 点击保存配置")
    print(f"")
    print(f"3. 检查后端日志:")
    print(f"   - 查看OpenWebUI后端日志输出")
    print(f"   - 寻找 'MidJourney' 相关的日志消息")
    print(f"   - 检查是否有错误或警告")
    print(f"")
    print(f"4. 测试前端功能:")
    print(f"   - 打开图像生成页面")
    print(f"   - 尝试生成一张图片")
    print(f"   - 打开浏览器开发者工具查看Network标签")
    print(f"   - 观察API调用是否成功")


if __name__ == "__main__":
    test_openwebui_backend()
    check_configuration_instructions()

    print(f"\n" + "=" * 60)
    print(f"🎯 重要提醒:")
    print(f"如果端点测试显示路由不存在(404)，说明:")
    print(f"1. 后端服务可能没有正确重启")
    print(f"2. MidJourney路由没有正确注册")
    print(f"3. 需要检查import和路由配置")
    print(f"")
    print(f"如果端点存在但需要认证(401/403)，说明:")
    print(f"1. 路由配置正确")
    print(f"2. 需要通过Web界面测试完整功能")
