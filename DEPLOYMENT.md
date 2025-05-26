# 部署指南

## 快速部署

### 1. 使用启动脚本（推荐）

**Windows用户：**
```bash
# 双击运行或在命令行执行
start.bat
```

**Linux/Mac用户：**
```bash
chmod +x start.sh
./start.sh
```

### 2. 手动部署

#### 方法1: Docker部署

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑.env文件，添加API密钥

# 2. 启动服务
docker-compose up --build -d

# 3. 访问应用
# http://localhost:8000
```

#### 方法2: 本地开发

```bash
# 1. 安装uv包管理器
pip install uv

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件

# 4. 启动服务
uv run python run.py
```

## 环境变量配置

在`.env`文件中配置以下变量（至少配置一个API密钥）：

```bash
# OpenAI API密钥
OPENAI_API_KEY=sk-your-openai-api-key

# Anthropic API密钥
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Google API密钥
GOOGLE_API_KEY=your-google-api-key

# 可选配置
LITELLM_MODEL=gpt-3.5-turbo
LITELLM_TEMPERATURE=0.7
LITELLM_MAX_TOKENS=4000
DEBUG=false
```

## 获取API密钥

### OpenAI API密钥
1. 访问 [OpenAI Platform](https://platform.openai.com/)
2. 注册/登录账户
3. 进入 API Keys 页面
4. 创建新的API密钥

### Anthropic API密钥
1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 注册/登录账户
3. 进入 API Keys 页面
4. 创建新的API密钥

### Google API密钥
1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 注册/登录账户
3. 创建新的API密钥
4. 启用Gemini API

## 验证部署

### 1. 健康检查
```bash
curl http://localhost:8000/health
# 应该返回: {"status":"healthy","message":"服务运行正常"}
```

### 2. 测试API
```bash
curl http://localhost:8000/api/v1/models
# 应该返回可用模型列表
```

### 3. 访问Web界面
打开浏览器访问: http://localhost:8000

### 4. 测试字幕获取
```bash
uv run python test_example.py
# 应该成功获取YouTube视频字幕
```

## 常见问题

### 1. 端口被占用
```bash
# 查看端口占用
netstat -an | findstr :8000  # Windows
lsof -i :8000               # Linux/Mac

# 修改端口（在run.py中）
port=8001  # 改为其他端口
```

### 2. API密钥错误
- 确保API密钥格式正确
- 检查API密钥是否有效
- 确认账户有足够的配额

### 3. 依赖安装失败
```bash
# 清理缓存重新安装
uv cache clean
uv sync --reinstall
```

### 4. Docker构建失败
```bash
# 清理Docker缓存
docker system prune -a
docker-compose build --no-cache
```

## 生产环境部署

### 1. 使用反向代理
```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 环境变量安全
- 使用环境变量而不是.env文件
- 限制API密钥权限
- 定期轮换API密钥

### 3. 监控和日志
```bash
# 查看Docker日志
docker-compose logs -f video-as-note

# 设置日志轮转
# 在docker-compose.yml中添加logging配置
```

### 4. 扩展性考虑
- 使用Redis缓存处理结果
- 添加数据库存储历史记录
- 实现负载均衡

## 故障排除

### 查看日志
```bash
# Docker部署
docker-compose logs -f

# 本地开发
# 日志直接输出到控制台
```

### 重启服务
```bash
# Docker部署
docker-compose restart

# 本地开发
# Ctrl+C 停止，然后重新运行
```

### 完全重置
```bash
# Docker部署
docker-compose down
docker-compose up --build -d

# 本地开发
uv cache clean
uv sync
```