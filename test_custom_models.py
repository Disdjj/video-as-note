#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户自定义模型功能
"""
import requests
import json

def test_custom_model_functionality():
    """测试用户自定义模型功能"""
    base_url = "http://localhost:8000/api/v1"

    print("🧪 测试用户自定义模型功能")
    print("=" * 50)

    # 测试模型验证API
    print("\n1. 测试模型验证API")
    print("-" * 30)

    test_models = [
        "gpt-3.5-turbo",
        "gpt-4o",
        "claude-3-5-sonnet-20241022",
        "gemini-1.5-pro",
        "groq/llama-3.1-70b-versatile",
        "invalid-model-name"
    ]

    for model_name in test_models:
        try:
            response = requests.post(
                f"{base_url}/models/validate",
                json={"model_name": model_name},
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                status = "✅ 可用" if result["is_valid"] else "❌ 不可用"
                print(f"  {model_name}: {status}")
            else:
                print(f"  {model_name}: ❌ 验证失败 ({response.status_code})")

        except Exception as e:
            print(f"  {model_name}: ❌ 请求失败 - {e}")

    # 测试模型信息API
    print("\n2. 测试模型信息API")
    print("-" * 30)

    test_model = "gpt-3.5-turbo"
    try:
        response = requests.get(f"{base_url}/models/{test_model}/info", timeout=10)

        if response.status_code == 200:
            model_info = response.json()
            print(f"  模型: {model_info.get('model_name')}")
            print(f"  可用性: {'✅ 可用' if model_info.get('is_available') else '❌ 不可用'}")

            supported_params = model_info.get('supported_params', [])
            if supported_params:
                print(f"  支持的参数: {len(supported_params)} 个")
                print(f"  参数示例: {', '.join(supported_params[:5])}")
            else:
                print("  支持的参数: 无法获取")

        else:
            print(f"  获取模型信息失败: {response.status_code}")

    except Exception as e:
        print(f"  获取模型信息失败: {e}")

    # 测试健康检查
    print("\n3. 测试服务健康状态")
    print("-" * 30)

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"  状态: {health.get('status')}")
            print(f"  消息: {health.get('message')}")
        else:
            print(f"  健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"  健康检查失败: {e}")

    print("\n✨ 测试完成!")
    print("\n💡 使用说明:")
    print("  1. 在Web界面中输入任何LiteLLM支持的模型名称")
    print("  2. 点击验证按钮检查模型是否可用")
    print("  3. 验证成功后即可使用该模型生成讲义")
    print("  4. 支持的模型格式:")
    print("     - OpenAI: gpt-4o, gpt-4, gpt-3.5-turbo")
    print("     - Anthropic: claude-3-5-sonnet-20241022")
    print("     - Google: gemini-1.5-pro, gemini-1.5-flash")
    print("     - Groq: groq/llama-3.1-70b-versatile")
    print("     - 其他: 任何LiteLLM支持的模型")

if __name__ == "__main__":
    test_custom_model_functionality()