# 用户自定义模型使用示例

本文档展示如何使用用户自定义模型功能。

## Web界面使用

### 1. 输入模型名称
在"AI模型名称"输入框中输入任何LiteLLM支持的模型名称，例如：
- `gpt-4o`
- `claude-3-5-sonnet-20241022`
- `gemini-1.5-pro`
- `groq/llama-3.1-70b-versatile`

### 2. 验证模型
点击蓝色的验证按钮（✓），系统会检查：
- 模型是否被LiteLLM支持
- 相应的API密钥是否已配置
- 模型是否可以正常调用

### 3. 查看验证结果
- ✅ 绿色文字：模型验证成功，可以使用
- ❌ 红色文字：模型不可用或配置不正确

## API使用示例

### 验证模型
```bash
curl -X POST http://localhost:8000/api/v1/models/validate \
  -H "Content-Type: application/json" \
  -d '{"model_name": "gpt-4o"}'
```

响应示例：
```json
{
  "model_name": "gpt-4o",
  "is_valid": true,
  "model_info": {
    "model_name": "gpt-4o",
    "is_available": true,
    "supported_params": ["temperature", "max_tokens", "top_p", ...],
    "environment_validation": {...}
  }
}
```

### 获取模型信息
```bash
curl http://localhost:8000/api/v1/models/gpt-4o/info
```

### 使用自定义模型处理视频
```bash
curl -X POST http://localhost:8000/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "model_name": "claude-3-5-sonnet-20241022",
    "language": "zh"
  }'
```

## Python SDK使用

```python
import requests

# 验证模型
def validate_model(model_name):
    response = requests.post(
        "http://localhost:8000/api/v1/models/validate",
        json={"model_name": model_name}
    )
    return response.json()

# 使用自定义模型
def process_video_with_custom_model(video_id, model_name):
    response = requests.post(
        "http://localhost:8000/api/v1/process",
        json={
            "video_id": video_id,
            "model_name": model_name,
            "language": "zh"
        }
    )
    return response.json()

# 示例使用
model_name = "gpt-4o"
validation = validate_model(model_name)

if validation["is_valid"]:
    result = process_video_with_custom_model("dQw4w9WgXcQ", model_name)
    print(f"处理开始，视频ID: {result['video_id']}")
else:
    print("模型验证失败")
```

## 常用模型名称

### OpenAI
- `gpt-4o` - 最新的GPT-4o模型
- `gpt-4o-mini` - 轻量级GPT-4o
- `gpt-4-turbo` - GPT-4 Turbo
- `gpt-4` - 标准GPT-4
- `gpt-3.5-turbo` - GPT-3.5 Turbo

### Anthropic
- `claude-3-5-sonnet-20241022` - 最新Claude 3.5 Sonnet
- `claude-3-5-haiku-20241022` - 快速Claude 3.5
- `claude-3-opus-20240229` - 最强Claude模型
- `claude-3-sonnet-20240229` - 平衡性能Claude

### Google
- `gemini-1.5-pro` - Gemini 1.5 Pro
- `gemini-1.5-flash` - 快速Gemini模型
- `gemini-pro` - 标准Gemini Pro

### Groq (高性能推理)
- `groq/llama-3.1-70b-versatile` - Llama 3.1 70B
- `groq/llama-3.1-8b-instant` - 快速Llama 3.1
- `groq/mixtral-8x7b-32768` - Mixtral模型

### DeepSeek
- `deepseek/deepseek-chat` - DeepSeek对话模型
- `deepseek/deepseek-coder` - DeepSeek代码模型

### 其他提供商
- `mistral/mistral-large-latest` - Mistral大模型
- `cohere/command-r-plus` - Cohere Command R+
- `together_ai/meta-llama/Llama-3-70b-chat-hf` - Together AI上的Llama

## 环境变量配置

确保为你要使用的模型配置相应的API密钥：

```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key

# Google
GOOGLE_API_KEY=your_google_key
GEMINI_API_KEY=your_google_key

# Groq
GROQ_API_KEY=your_groq_key

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_key

# 其他提供商...
```

## 故障排除

### 模型验证失败
1. **检查模型名称**: 确保使用正确的LiteLLM模型名称格式
2. **检查API密钥**: 确保相应提供商的API密钥已正确配置
3. **检查网络**: 确保可以访问模型提供商的API端点
4. **检查配额**: 确保API密钥有足够的使用配额

### 常见错误
- `模型不可用或配置不正确`: 通常是API密钥未配置或无效
- `验证请求失败`: 网络连接问题或服务器错误
- `模型名称格式错误`: 使用了不正确的模型名称格式

### 获取帮助
- 查看LiteLLM官方文档：https://docs.litellm.ai/
- 检查模型提供商的API文档
- 使用模型信息API获取详细的错误信息