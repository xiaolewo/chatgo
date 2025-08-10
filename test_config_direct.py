#!/usr/bin/env python3
"""
直接测试配置是否正确加载
"""

import requests
import json


def test_config_retrieval():
    """测试配置获取"""

    print("🔍 测试MidJourney配置获取")
    print("=" * 50)

    # 尝试通过API获取配置
    openwebui_url = "http://localhost:8080"

    print(f"测试配置API: {openwebui_url}/api/v1/midjourney/config")

    try:
        response = requests.get(f"{openwebui_url}/api/v1/midjourney/config", timeout=10)
        print(f"状态码: {response.status_code}")

        if response.status_code == 403:
            print("❌ 需要认证token才能获取配置")
            print("这说明后端服务正常，但我们无法直接测试配置")
            print()
            print("请在浏览器中:")
            print("1. 登录OpenWebUI管理员账户")
            print("2. 进入 设置 → Admin Settings → MidJourney")
            print("3. 确认以下配置:")
            print("   ✓ 启用MidJourney: 已勾选")
            print("   ✓ API URL: https://api.linkapi.org")
            print("   ✓ API Key: sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
            print("   ✓ Fast模式积分: 10")
            print("   ✓ Relax模式积分: 5")
            print("   ✓ Turbo模式积分: 15")
            print("4. 点击保存配置")
            print("5. 重新测试图像生成")

        elif response.status_code == 404:
            print("❌ 配置API不存在，后端可能没有正确加载MidJourney模块")

        elif response.status_code == 200:
            config_data = response.json()
            print("✅ 配置获取成功:")
            print(json.dumps(config_data, indent=2, ensure_ascii=False))

            # 分析配置
            analyze_config(config_data)

        else:
            print(f"❓ 未知状态: {response.status_code}")
            print(f"响应: {response.text}")

    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")


def analyze_config(config):
    """分析配置"""

    print("\n📋 配置分析:")

    enabled = config.get("enabled", False)
    api_url = config.get("api_url", "")
    api_key = config.get("api_key", "")

    print(f"启用状态: {'✅ 已启用' if enabled else '❌ 未启用'}")
    print(f"API URL: {'✅ 已配置' if api_url else '❌ 未配置'} ({api_url})")
    print(f"API Key: {'✅ 已配置' if api_key else '❌ 未配置'} ({api_key[:20]}...)")

    if not enabled:
        print("\n❌ MidJourney服务未启用")
        print("解决方案: 在管理面板中启用MidJourney服务")

    if not api_url:
        print("\n❌ API URL未配置")
        print("解决方案: 设置API URL为 https://api.linkapi.org")

    if not api_key:
        print("\n❌ API Key未配置")
        print(
            "解决方案: 设置API Key为 sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55"
        )

    if enabled and api_url and api_key:
        print("\n✅ 配置看起来正确")
        print("如果仍有问题，可能是:")
        print("1. 后端服务没有重启")
        print("2. API Key无效")
        print("3. 网络连接问题")


def provide_manual_config_steps():
    """提供手动配置步骤"""

    print("\n" + "=" * 50)
    print("🔧 手动配置步骤")
    print()
    print("如果配置获取失败，请手动执行以下步骤:")
    print()
    print("1. 打开浏览器，访问OpenWebUI")
    print("2. 使用管理员账户登录")
    print("3. 点击右上角的用户头像 → Admin Panel")
    print("4. 在左侧菜单中找到 Settings")
    print("5. 寻找 MidJourney 或 Images 相关设置")
    print("6. 配置以下信息:")
    print("   - Enable MidJourney: ✓")
    print("   - API URL: https://api.linkapi.org")
    print("   - API Key: sk-9kOMUms2rhojGWiOE5239aB42bC947D5B501E4Dc2fB52c55")
    print("   - Fast Credits: 10")
    print("   - Relax Credits: 5")
    print("   - Turbo Credits: 15")
    print("7. 点击保存/更新按钮")
    print("8. 重新测试图像生成功能")
    print()
    print("⚠️  注意事项:")
    print("- 确保使用管理员账户")
    print("- 保存配置后可能需要刷新页面")
    print("- 如果找不到MidJourney设置，可能需要重启后端服务")


if __name__ == "__main__":
    test_config_retrieval()
    provide_manual_config_steps()
