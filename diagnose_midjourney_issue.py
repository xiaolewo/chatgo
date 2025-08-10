#!/usr/bin/env python3
"""
诊断MidJourney API调用失败问题
检查配置、服务状态和API连接
"""

import requests
import json
from datetime import datetime


def diagnose_midjourney_issue():
    """诊断MidJourney问题"""

    print("🔍 MidJourney API调用失败诊断")
    print("=" * 60)
    print(f"时间: {datetime.now()}")

    # 测试配置
    API_URL = "https://api.linkapi.org"
    NEW_API_KEY = "sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"
    OLD_API_KEY = "sk-fvaOT6nT5pHxOiy5Rq7vrzsDnk18dHmfdDsbPGW3g4qZKHX9"

    # 步骤1: 测试新API密钥
    print(f"\n🔑 步骤1: 验证新API密钥")
    test_api_key(API_URL, NEW_API_KEY, "新API密钥")

    # 步骤2: 对比旧API密钥
    print(f"\n🔄 步骤2: 对比旧API密钥")
    test_api_key(API_URL, OLD_API_KEY, "旧API密钥")

    # 步骤3: 检查OpenWebUI后端状态
    print(f"\n🌐 步骤3: 检查OpenWebUI后端服务")
    check_openwebui_status()

    # 步骤4: 提供解决方案
    print(f"\n💡 步骤4: 解决方案")
    provide_solutions()


def test_api_key(api_url, api_key, key_name):
    """测试API密钥"""
    try:
        # 测试所有三种模式
        modes = [
            ("mj-fast", "Fast模式"),
            ("mj-relax", "Relax模式"),
            ("mj-turbo", "Turbo模式"),
        ]

        print(f"   🔐 {key_name} ({api_key[:20]}...)")

        for mode_path, mode_name in modes:
            url = f"{api_url}/{mode_path}/mj/submit/imagine"
            payload = {"prompt": "test prompt", "base64Array": []}
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            try:
                response = requests.post(url, json=payload, headers=headers, timeout=10)
                result = response.json()

                if result.get("code") == 1:
                    status = "✅ 成功"
                    detail = f"任务ID: {result.get('result')}"
                elif result.get("description") == "quota_not_enough":
                    status = "⚠️  配额不足"
                    detail = "API参数正确，但余额不足"
                elif result.get("description") == "parameter error":
                    status = "❌ 参数错误"
                    detail = "API参数格式有问题"
                else:
                    status = "❌ 其他错误"
                    detail = result.get("description", "未知错误")

                print(f"      {mode_name}: {status} - {detail}")

            except Exception as e:
                print(f"      {mode_name}: ❌ 连接失败 - {str(e)}")

    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")


def check_openwebui_status():
    """检查OpenWebUI服务状态"""
    openwebui_urls = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    for url in openwebui_urls:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ OpenWebUI运行中: {url}")

                # 检查MidJourney配置端点
                try:
                    config_response = requests.get(
                        f"{url}/api/v1/midjourney/config", timeout=5
                    )
                    if config_response.status_code == 403:
                        print(f"      🔒 MidJourney配置端点存在 (需要管理员权限)")
                    elif config_response.status_code == 200:
                        print(f"      ✅ MidJourney配置端点可访问")
                    else:
                        print(
                            f"      ❌ MidJourney配置端点异常: {config_response.status_code}"
                        )
                except:
                    print(f"      ❌ MidJourney端点无法访问")

                return url
        except:
            continue

    print(f"   ❌ 未找到运行中的OpenWebUI服务")
    return None


def provide_solutions():
    """提供解决方案"""
    print(f"   🎯 可能的原因和解决方案:")
    print(f"")
    print(f"   1️⃣ **后端服务未重启**")
    print(f"      - 问题: 配置代码已修改，但后端服务还在使用旧配置")
    print(f"      - 解决: 重启OpenWebUI后端服务")
    print(f"      - 命令: docker restart openwebui 或 systemctl restart openwebui")
    print(f"")
    print(f"   2️⃣ **管理员面板配置未更新**")
    print(f"      - 问题: 新API密钥还没有通过管理面板保存")
    print(f"      - 解决: 打开OpenWebUI管理后台 → 设置 → MidJourney")
    print(f"      - 配置: API URL: https://api.linkapi.org")
    print(f"      - 配置: API Key: sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
    print(f"      - 配置: 启用MidJourney服务")
    print(f"")
    print(f"   3️⃣ **配置持久化尚未生效**")
    print(f"      - 问题: 代码修改了但数据库配置还是旧的")
    print(f"      - 解决: 先重启服务，再通过管理面板重新保存配置")
    print(f"")
    print(f"   4️⃣ **前端缓存问题**")
    print(f"      - 问题: 浏览器缓存了旧的配置或代码")
    print(f"      - 解决: 强制刷新页面 (Ctrl+F5 或 Cmd+Shift+R)")
    print(f"")
    print(f"   📋 **推荐解决步骤**:")
    print(f"   1. 重启OpenWebUI后端服务")
    print(f"   2. 清除浏览器缓存并刷新页面")
    print(f"   3. 登录管理员账户 → 设置 → MidJourney配置")
    print(f"   4. 填入新的API密钥并保存")
    print(f"   5. 测试图像生成功能")


if __name__ == "__main__":
    diagnose_midjourney_issue()

    print(f"\n" + "=" * 60)
    print(f"🏁 诊断完成")
    print(f"请根据上述分析结果采取相应的解决措施")
