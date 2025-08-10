#!/usr/bin/env python3
"""
测试可灵视频生成API调用修复
验证 KlingGenerateRequest 模型的 callback_url 属性问题
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from open_webui.routers.kling import KlingGenerateRequest, CameraControl


def test_kling_request_model():
    """测试可灵请求模型"""

    print("=== 可灵请求模型测试 ===\n")

    # 1. 测试基本请求（不包含callback_url）
    print("1. 测试基本请求（不包含callback_url）...")
    try:
        basic_request = KlingGenerateRequest(prompt="测试提示词")
        print("✅ 基本请求创建成功")
        print(f"   prompt: {basic_request.prompt}")
        print(f"   callback_url: {basic_request.callback_url}")
        print(f"   model_name: {basic_request.model_name}")
        print(f"   mode: {basic_request.mode}")
        print(f"   duration: {basic_request.duration}")
        print(f"   aspect_ratio: {basic_request.aspect_ratio}")
    except Exception as e:
        print(f"❌ 基本请求创建失败: {e}")
        return False

    print()

    # 2. 测试包含callback_url的请求
    print("2. 测试包含callback_url的请求...")
    try:
        callback_request = KlingGenerateRequest(
            prompt="测试提示词",
            callback_url="https://example.com/callback",
            mode="pro",
            duration="10",
        )
        print("✅ 回调请求创建成功")
        print(f"   prompt: {callback_request.prompt}")
        print(f"   callback_url: {callback_request.callback_url}")
        print(f"   mode: {callback_request.mode}")
        print(f"   duration: {callback_request.duration}")
    except Exception as e:
        print(f"❌ 回调请求创建失败: {e}")
        return False

    print()

    # 3. 测试包含摄像机控制的请求
    print("3. 测试包含摄像机控制的请求...")
    try:
        camera_control = CameraControl(type="horizontal", config={"horizontal": 5.0})

        camera_request = KlingGenerateRequest(
            prompt="测试摄像机控制",
            camera_control=camera_control,
            external_task_id="test-123",
        )
        print("✅ 摄像机控制请求创建成功")
        print(f"   prompt: {camera_request.prompt}")
        print(f"   camera_control: {camera_request.camera_control}")
        print(f"   external_task_id: {camera_request.external_task_id}")
    except Exception as e:
        print(f"❌ 摄像机控制请求创建失败: {e}")
        return False

    print()

    # 4. 测试字段访问
    print("4. 测试所有字段访问...")
    try:
        full_request = KlingGenerateRequest(
            model_name="kling-v2-master",
            prompt="完整测试",
            negative_prompt="不要的内容",
            cfg_scale=0.8,
            mode="pro",
            aspect_ratio="9:16",
            duration="10",
            callback_url="https://callback.example.com",
            external_task_id="full-test-456",
        )

        # 访问所有字段，确保没有属性错误
        fields_to_test = [
            "model_name",
            "prompt",
            "negative_prompt",
            "cfg_scale",
            "mode",
            "camera_control",
            "aspect_ratio",
            "duration",
            "callback_url",
            "external_task_id",
        ]

        for field in fields_to_test:
            value = getattr(full_request, field)
            print(f"   {field}: {value}")

        print("✅ 所有字段访问成功")

    except AttributeError as e:
        print(f"❌ 字段访问失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 完整请求测试失败: {e}")
        return False

    print()

    # 5. 测试字典转换（用于任务存储）
    print("5. 测试字典转换...")
    try:
        test_request = KlingGenerateRequest(
            prompt="字典测试", callback_url="https://test.com/callback"
        )

        # 模拟任务创建时的字典转换
        task_form_data = {
            "prompt": test_request.prompt,
            "negative_prompt": test_request.negative_prompt,
            "model_name": test_request.model_name,
            "mode": test_request.mode,
            "aspect_ratio": test_request.aspect_ratio,
            "duration": test_request.duration,
            "cfg_scale": test_request.cfg_scale,
            "camera_control": (
                test_request.camera_control.dict()
                if test_request.camera_control
                else None
            ),
            "callback_url": test_request.callback_url,
            "external_task_id": test_request.external_task_id,
            "credits_used": 5,
        }

        print("✅ 字典转换成功")
        print("   转换后的数据:")
        for key, value in task_form_data.items():
            print(f"     {key}: {value}")

    except Exception as e:
        print(f"❌ 字典转换失败: {e}")
        return False

    print("\n🎉 所有测试通过！可灵请求模型修复成功！")
    return True


if __name__ == "__main__":
    success = test_kling_request_model()
    if success:
        print("\n✅ 修复验证通过，可灵视频生成应该可以正常工作了")
    else:
        print("\n❌ 修复验证失败，需要进一步检查")
        sys.exit(1)
