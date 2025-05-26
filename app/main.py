# -*- coding: utf-8 -*-
"""
FastAPI主应用
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import router
from app.middleware import (
    LoggingMiddleware,
    RequestIDMiddleware,
)
from app.utils.logger import app_logger

# 创建FastAPI应用
app = FastAPI(
    title="VideoAsNote",
    description="视频字幕转讲义工具",
    version="0.1.0",
    debug=False
)

# 记录应用启动
app_logger.info(f"启动FastAPI应用 v0.1.0")

# 添加日志中间件（按顺序添加，先添加的后执行）
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_logger.info("中间件配置完成")

# 注册API路由
app.include_router(router, prefix="/api/v1", tags=["main"])
app_logger.info("API路由注册完成")

# 静态文件服务
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app_logger.info("静态文件服务已启用")


# 前端页面路由
@app.get("/")
async def read_index():
    """返回前端页面"""
    app_logger.info("访问首页")
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    else:
        return {"message": "欢迎使用YouTube视频字幕转讲义工具", "api_docs": "/docs"}


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    app_logger.debug("健康检查请求")
    return {"status": "healthy", "message": "服务运行正常"}


if __name__ == "__main__":
    import uvicorn

    app_logger.info("启动开发服务器")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
