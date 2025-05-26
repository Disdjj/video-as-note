@echo off
chcp 65001 >nul

echo 🎥 YouTube视频字幕转讲义工具
echo ================================

REM 检查是否存在.env文件
if not exist .env (
    echo ⚠️  未找到.env文件，正在创建...
    copy .env.example .env >nul
    echo ✅ 已创建.env文件，请编辑该文件添加你的API密钥
    echo 📝 需要配置的API密钥：
    echo    - OPENAI_API_KEY ^(OpenAI GPT模型^)
    echo    - ANTHROPIC_API_KEY ^(Claude模型^)
    echo    - GOOGLE_API_KEY ^(Gemini模型^)
    echo.
    echo ⚡ 至少需要配置一个API密钥才能正常使用
    echo.
)

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% == 0 (
    docker-compose --version >nul 2>&1
    if %errorlevel% == 0 (
        echo 🐳 检测到Docker，使用Docker启动...
        echo 📦 构建并启动容器...
        docker-compose up --build -d

        echo.
        echo ✅ 服务已启动！
        echo 🌐 访问地址: http://localhost:8000
        echo.
        echo 📋 常用命令：
        echo    查看日志: docker-compose logs -f
        echo    停止服务: docker-compose down
        echo    重启服务: docker-compose restart
        goto :end
    )
)

REM 检查uv是否安装
uv --version >nul 2>&1
if %errorlevel% == 0 (
    echo 🐍 使用uv启动本地开发服务器...
    echo 📦 安装依赖...
    uv sync

    echo 🚀 启动服务器...
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    goto :end
)

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo 🐍 使用Python启动...
    echo 📦 安装依赖...
    pip install -r requirements.txt 2>nul || echo 请手动安装依赖

    echo 🚀 启动服务器...
    python run.py
    goto :end
)

echo ❌ 未找到Docker、uv或Python，请先安装其中一个
echo.
echo 安装选项：
echo 1. Docker: https://docs.docker.com/get-docker/
echo 2. uv: pip install uv
echo 3. Python: https://python.org

:end
pause