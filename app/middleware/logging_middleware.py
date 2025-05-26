# -*- coding: utf-8 -*-
"""
日志中间件 - 记录HTTP请求和响应
"""
import time
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import api_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP请求日志中间件"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()

        # 提取请求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
        }

        # 记录请求体（如果是POST/PUT等）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 读取请求体
                body = await request.body()
                if body:
                    # 尝试解析JSON
                    try:
                        request_info["body"] = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_info["body"] = f"<binary data: {len(body)} bytes>"

                # 重新构造请求对象，因为body只能读取一次
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive
            except Exception as e:
                api_logger.warning(f"读取请求体失败: {e}")

        # 记录请求开始
        api_logger.info(f"HTTP请求开始: {request_info}")

        # 处理请求
        try:
            response = await call_next(request)

            # 计算处理时间
            process_time = time.time() - start_time

            # 记录响应信息
            response_info = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "process_time": f"{process_time:.3f}s"
            }

            # 如果是JSON响应，尝试记录响应体（仅记录前1000字符）
            if hasattr(response, 'body') and response.headers.get("content-type", "").startswith("application/json"):
                try:
                    body_preview = response.body[:1000].decode() if len(response.body) > 1000 else response.body.decode()
                    response_info["body_preview"] = body_preview
                except Exception:
                    response_info["body_preview"] = "<无法解析响应体>"

            # 根据状态码选择日志级别
            if response.status_code >= 500:
                api_logger.error(f"HTTP请求完成（服务器错误）: {response_info}")
            elif response.status_code >= 400:
                api_logger.warning(f"HTTP请求完成（客户端错误）: {response_info}")
            else:
                api_logger.info(f"HTTP请求完成（成功）: {response_info}")

            # 添加处理时间到响应头
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 计算错误处理时间
            error_time = time.time() - start_time

            # 记录异常
            api_logger.error(f"HTTP请求异常: method={request.method}, path={request.url.path}, error={str(e)}, time={error_time:.3f}s", exc_info=True)

            # 返回500错误
            return JSONResponse(
                status_code=500,
                content={"detail": "内部服务器错误"},
                headers={"X-Process-Time": str(error_time)}
            )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件 - 为每个请求生成唯一ID"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid

        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]

        # 将请求ID添加到请求状态中
        request.state.request_id = request_id

        # 处理请求
        response = await call_next(request)

        # 将请求ID添加到响应头
        response.headers["X-Request-ID"] = request_id

        return response