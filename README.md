# YouTube视频字幕转讲义工具

一个基于AI的智能工具，可以将YouTube视频字幕转换为结构化的学习讲义。支持多种AI模型（GPT、Claude、Gemini），使用LiteLLM实现统一的API接口。

## 功能特性

- 🎥 **YouTube字幕提取**: 自动获取YouTube视频的字幕内容
- 🤖 **用户自定义模型**: 支持用户输入任何LiteLLM支持的模型名称
- 🌟 **LiteLLM集成**: 通过LiteLLM支持1000+个AI模型，100+个提供商
- 📚 **智能讲义生成**: 将字幕转换为结构化的学习材料，包含概念解释、图表等
- 🌐 **现代化Web界面**: 响应式设计，支持实时进度显示，模型验证功能
- 🐳 **Docker支持**: 一键部署，支持容器化运行
- 🔄 **异步处理**: 后台处理，支持长时间任务
- ✅ **模型验证**: 实时验证用户输入的模型是否可用

## 技术栈

### 后端
- **FastAPI**: 现代化的Python Web框架
- **LiteLLM**: 统一的LLM API接口，支持100+模型
- **LangChain**: AI应用开发框架
- **YouTube Transcript API**: YouTube字幕获取
- **Pydantic**: 数据验证和序列化

### 前端
- **HTML5 + CSS3 + JavaScript**: 原生Web技术
- **Tailwind CSS**: 实用优先的CSS框架
- **Font Awesome**: 图标库

### 部署
- **Docker**: 容器化部署
- **Docker Compose**: 多容器编排
- **uv**: 现代Python包管理器

## 快速开始

### 方法1: Docker部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd video-as-note
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，添加你的API密钥
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
打开浏览器访问: http://localhost:8000

### 方法2: 本地开发

1. **安装依赖**
```bash
# 安装uv包管理器
pip install uv

# 安装项目依赖
uv sync
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件
```

3. **启动开发服务器**
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 环境变量配置

在`.env`文件中配置以下变量：

```bash
# API密钥（至少配置一个）
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LiteLLM配置
LITELLM_MODEL=gpt-3.5-turbo
LITELLM_TEMPERATURE=0.7
LITELLM_MAX_TOKENS=4000

# 应用配置
DEBUG=false
```

## 支持的AI模型

通过LiteLLM集成，本项目支持1000+个AI模型，包括：

### 主要提供商
| 提供商 | 模型示例 | 说明 |
|--------|----------|------|
| OpenAI | gpt-4o, gpt-4, gpt-3.5-turbo | 最流行的AI模型 |
| Anthropic | claude-3.5-sonnet, claude-3-opus | 强大的推理能力 |
| Google | gemini-1.5-pro, gemini-flash | 支持长上下文 |
| Groq | llama-3.1-70b, mixtral-8x7b | 高性能推理 |
| DeepSeek | deepseek-chat, deepseek-coder | 专业代码模型 |

### 其他支持的提供商
- Mistral AI, Cohere, Together AI, Fireworks AI
- Replicate, Hugging Face, Ollama, VLLM
- 还有90+个其他提供商...

> 💡 提示：你可以使用任何LiteLLM支持的模型名称，系统会自动验证其可用性
>
> 📖 详细使用说明：[用户自定义模型使用示例](USAGE_EXAMPLES.md)

## API文档

启动服务后，可以访问以下地址查看API文档：

- ReDoc: http://localhost:8000/redoc

### 主要API端点

- `POST /api/v1/models/validate` - 验证用户指定的模型是否可用
- `GET /api/v1/models/{model_name}/info` - 获取指定模型的详细信息
- `POST /api/v1/process` - 开始处理视频
- `GET /api/v1/status/{video_id}` - 获取处理状态
- `GET /api/v1/result/{video_id}` - 获取生成的讲义
- `GET /api/v1/transcript/{video_id}` - 获取视频字幕

## 使用说明

1. **输入视频信息**: 在首页输入YouTube视频URL或视频ID
2. **输入AI模型**:
   - 手动输入任何LiteLLM支持的模型名称
   - 点击验证按钮检查模型是否可用
   - 支持的模型格式示例：
     - OpenAI: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
     - Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
     - Google: `gemini-1.5-pro`, `gemini-1.5-flash`
     - Groq: `groq/llama-3.1-70b-versatile`, `groq/mixtral-8x7b-32768`
     - DeepSeek: `deepseek/deepseek-chat`, `deepseek/deepseek-coder`
3. **选择字幕语言**: 选择视频字幕的语言（中文、英文等）
4. **开始处理**: 点击"开始生成讲义"按钮
5. **等待完成**: 系统会显示实时进度，处理通常需要1-3分钟
6. **查看结果**: 处理完成后可以查看、复制或下载生成的讲义

## 讲义格式

生成的讲义包含以下部分：

1. **课程概览**: 核心主题、知识点、课程定位
2. **详细内容**: 逻辑化组织的知识点，深度解释，Mermaid图表
3. **重点总结**: 核心概念、易混淆概念、扩展资源
4. **知识增强**: 前置知识、常见误区、实际应用

## 项目结构

```
video-as-note/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── config.py          # 配置文件
│   ├── models.py          # 数据模型
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   └── routes.py
│   └── services/          # 业务服务
│       ├── __init__.py
│       ├── transcript_service.py  # 字幕服务
│       └── llm_service.py         # LLM服务
├── static/                # 静态文件
│   ├── index.html         # 前端页面
│   └── app.js            # 前端JavaScript
├── pyproject.toml         # 项目配置
├── uv.lock               # 依赖锁定文件
├── Dockerfile            # Docker镜像构建
├── docker-compose.yml    # Docker编排
├── .env.example           # 环境变量示例
└── README.md             # 项目说明
```

## 开发指南

### 添加新的AI模型

1. 在`app/services/llm_service.py`的`get_available_models()`方法中添加新模型配置
2. 确保LiteLLM支持该模型
3. 更新环境变量配置（如需要）

### 自定义讲义模板

修改`app/services/llm_service.py`中的`get_lecture_prompt()`方法来自定义生成的讲义格式。

### 扩展字幕语言支持

在前端`static/index.html`的语言选择下拉框中添加新的语言选项。

## 故障排除

### 常见问题

1. **API密钥错误**: 确保在`.env`文件中正确配置了API密钥
2. **视频无字幕**: 某些视频可能没有字幕或字幕被禁用
3. **模型不可用**: 检查API密钥是否有效，是否有足够的配额
4. **处理超时**: 对于很长的视频，可能需要更多时间处理

### 日志查看

```bash
# Docker部署
docker-compose logs -f video-as-note

# 本地开发
# 日志会直接输出到控制台
```

## 贡献指南

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 致谢

- [LiteLLM](https://github.com/BerriAI/litellm) - 统一的LLM API接口
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api) - YouTube字幕获取
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化Web框架
- [LangChain](https://langchain.com/) - AI应用开发框架