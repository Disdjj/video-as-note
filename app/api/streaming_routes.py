# -*- coding: utf-8 -*-
"""
流式API路由 - 使用SSE实现实时流式响应
"""
import asyncio
import time
import json
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
from pydantic import ValidationError

from app.models import VideoRequest, LectureNote, ProcessingStatus
from app.services.ai_service import AIService
from app.services.transcript_service import TranscriptService
from app.utils.logger import api_logger, log_api_request

# 创建路由器
stream_router = APIRouter(prefix="/stream", tags=["streaming"])

# 全局服务实例
transcript_service = TranscriptService()
ai_service = AIService()

# 存储处理状态的简单内存存储（生产环境应使用Redis等）
streaming_status: Dict[str, ProcessingStatus] = {}


async def stream_processor(video_id: str, model_name: str, language: str):
    """流式处理视频字幕并生成讲义"""
    start_time = time.time()
    api_logger.info(f"开始流式处理视频 - video_id: {video_id}, model: {model_name}, language: {language}")

    try:
        # 更新状态：开始获取字幕
        api_logger.info(f"[{video_id}] 开始获取视频字幕")
        streaming_status[video_id] = ProcessingStatus(
            status="processing",
            message="正在获取视频字幕...",
            progress=20
        )

        # 获取字幕
        transcript_start = time.time()
        segments = transcript_service.get_transcript(video_id, language)
        transcript_text = transcript_service.combine_transcript_text(segments)
        transcript_time = time.time() - transcript_start

        api_logger.info(f"[{video_id}] 字幕获取完成，耗时: {transcript_time:.2f}秒，字幕长度: {len(transcript_text)}字符")

        # 更新状态：开始生成讲义
        api_logger.info(f"[{video_id}] 开始生成讲义，使用模型: {model_name}")
        streaming_status[video_id] = ProcessingStatus(
            status="processing",
            message="正在生成讲义...",
            progress=60
        )

        # 存储生成的内容
        generated_content = []

        # 定义回调函数来更新状态
        def content_callback(content: str):
            generated_content.append(content)
            current_length = sum(len(c) for c in generated_content)
            # 每生成一定量的内容更新一次状态
            if current_length % 500 == 0:
                api_logger.debug(f"[{video_id}] 已生成内容长度: {current_length}字符")

        # 使用AI服务的流式生成功能
        async for chunk in ai_service.stream_lecture_note(
            transcript_text=transcript_text,
            video_id=video_id,
            model_name=model_name,
            language=language,
            callback=content_callback
        ):
            # 如果是内容块，更新状态
            if chunk.get("type") == "content":
                continue  # 内容会通过SSE直接发送
            
            # 如果是完成信号，更新状态为完成
            elif chunk.get("type") == "completed":
                result = chunk.get("result")
                if result:
                    lecture_note = LectureNote(**result)
                    streaming_status[video_id] = ProcessingStatus(
                        status="completed",
                        message="讲义生成完成",
                        progress=100,
                        result=lecture_note
                    )
                    
                    total_time = time.time() - start_time
                    api_logger.info(f"[{video_id}] 视频处理完成，总耗时: {total_time:.2f}秒")
            
            # 如果是错误信号，更新状态为错误
            elif chunk.get("type") == "error":
                error_msg = chunk.get("message", "未知错误")
                streaming_status[video_id] = ProcessingStatus(
                    status="error",
                    message=error_msg,
                    progress=0
                )
                
                error_time = time.time() - start_time
                api_logger.error(f"[{video_id}] 视频处理失败，耗时: {error_time:.2f}秒，错误: {error_msg}")

    except Exception as e:
        error_time = time.time() - start_time
        api_logger.error(f"[{video_id}] 视频处理失败，耗时: {error_time:.2f}秒，错误: {str(e)}", exc_info=True)

        # 更新状态：错误
        streaming_status[video_id] = ProcessingStatus(
            status="error",
            message=f"处理失败: {str(e)}",
            progress=0
        )


async def event_generator(video_id: str, request: Request):
    """SSE事件生成器"""
    # 检查视频ID是否存在
    if video_id not in streaming_status:
        yield json.dumps({
            "type": "error",
            "message": "未找到该视频的处理记录"
        })
        return

    # 初始状态
    last_status = None
    last_progress = -1

    # 定义一个函数来检查客户端是否断开连接
    def is_disconnected():
        return request.is_disconnected

    try:
        # 持续发送更新，直到处理完成或出错
        while True:
            # 检查客户端是否断开连接
            if is_disconnected():
                api_logger.info(f"[{video_id}] 客户端断开连接，停止流式传输")
                break

            # 获取当前状态
            current_status = streaming_status.get(video_id)
            
            # 如果状态发生变化，发送更新
            if current_status and (last_status != current_status.status or 
                                  last_progress != current_status.progress):
                
                # 更新上次状态
                last_status = current_status.status
                last_progress = current_status.progress
                
                # 发送进度更新
                yield json.dumps({
                    "type": "progress",
                    "status": current_status.status,
                    "message": current_status.message,
                    "progress": current_status.progress
                })
                
                # 如果处理完成，发送结果并结束
                if current_status.status == "completed" and current_status.result:
                    yield json.dumps({
                        "type": "completed",
                        "result": current_status.result.dict()
                    })
                    break
                
                # 如果处理出错，发送错误信息并结束
                elif current_status.status == "error":
                    yield json.dumps({
                        "type": "error",
                        "message": current_status.message
                    })
                    break
            
            # 等待一段时间再检查
            await asyncio.sleep(0.5)
            
    except Exception as e:
        api_logger.error(f"[{video_id}] 生成SSE事件时出错: {str(e)}", exc_info=True)
        yield json.dumps({
            "type": "error",
            "message": f"流式传输错误: {str(e)}"
        })


async def stream_content_generator(video_id: str, model_name: str, language: str, transcript_text: str, request: Request):
    """内容流式生成器"""
    api_logger.info(f"[{video_id}] 开始流式生成内容")
    
    try:
        # 使用AI服务的流式生成功能
        async for chunk in ai_service.stream_lecture_note(
            transcript_text=transcript_text,
            video_id=video_id,
            model_name=model_name,
            language=language
        ):
            # 检查客户端是否断开连接
            if request.is_disconnected:
                api_logger.info(f"[{video_id}] 客户端断开连接，停止内容生成")
                break
                
            # 发送内容块
            yield json.dumps(chunk)
            
            # 如果是完成或错误信号，结束流
            if chunk.get("type") in ["completed", "error"]:
                break
                
    except Exception as e:
        api_logger.error(f"[{video_id}] 流式生成内容时出错: {str(e)}", exc_info=True)
        yield json.dumps({
            "type": "error",
            "message": f"内容生成错误: {str(e)}"
        })


@stream_router.post("/process", response_model=Dict[str, str])
async def stream_process_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """处理视频，流式生成讲义"""
    api_logger.info(f"收到流式视频处理请求: video_id={request.video_id}, model={request.model_name}, language={request.language}")

    try:
        # 提取视频ID
        api_logger.info(f"提取视频ID: {request.video_id}")
        video_id = transcript_service.extract_video_id(request.video_id)
        api_logger.info(f"提取到的视频ID: {video_id}")

        # 验证用户指定的模型是否可用
        api_logger.info(f"验证模型可用性: {request.model_name}")
        if not await ai_service.validate_model(request.model_name):
            api_logger.warning(f"模型不可用: {request.model_name}")
            raise HTTPException(
                status_code=400,
                detail=f"模型 {request.model_name} 不可用或配置不正确"
            )
        api_logger.info(f"模型验证通过: {request.model_name}")

        # 初始化处理状态
        api_logger.info(f"初始化处理状态: {video_id}")
        streaming_status[video_id] = ProcessingStatus(
            status="processing",
            message="开始处理...",
            progress=0
        )

        # 添加后台任务
        api_logger.info(f"添加后台处理任务: {video_id}")
        background_tasks.add_task(
            stream_processor,
            video_id,
            request.model_name,
            request.language
        )

        api_logger.info(f"流式视频处理请求已接受: {video_id}")
        return {"message": "处理已开始", "video_id": video_id}

    except ValueError as e:
        api_logger.error(f"视频处理请求参数错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"视频处理请求服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@stream_router.get("/{video_id}")
async def stream_events(video_id: str, request: Request):
    """流式事件API - 使用SSE实现实时更新"""
    api_logger.info(f"收到流式事件请求: {video_id}")
    
    try:
        # 提取视频ID
        real_video_id = transcript_service.extract_video_id(video_id)
        api_logger.info(f"提取到的视频ID: {real_video_id}")
        
        # 检查视频ID是否存在
        if real_video_id not in streaming_status:
            api_logger.warning(f"未找到视频处理记录: {real_video_id}")
            raise HTTPException(status_code=404, detail="未找到该视频的处理记录")
            
        # 返回SSE响应
        api_logger.info(f"开始流式传输: {real_video_id}")
        return EventSourceResponse(
            event_generator(real_video_id, request),
            media_type="text/event-stream"
        )
        
    except ValueError as e:
        api_logger.error(f"流式事件请求参数错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"流式事件请求服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@stream_router.post("/direct-generate")
async def stream_direct_generate(request: Request):
    """直接流式生成讲义（不经过后台任务）"""
    api_logger.info(f"收到直接流式生成请求")
    
    try:
        # 解析请求体
        body = await request.json()
        video_id = body.get("video_id")
        model_name = body.get("model_name")
        language = body.get("language", "简体中文")
        transcript_text = body.get("transcript_text")
        
        # 验证参数
        if not video_id or not model_name or not transcript_text:
            raise HTTPException(status_code=400, detail="缺少必要参数")
            
        # 验证模型
        if not await ai_service.validate_model(model_name):
            raise HTTPException(status_code=400, detail=f"模型 {model_name} 不可用或配置不正确")
            
        # 返回SSE响应
        api_logger.info(f"开始直接流式生成: {video_id}, 模型: {model_name}")
        return EventSourceResponse(
            stream_content_generator(video_id, model_name, language, transcript_text, request),
            media_type="text/event-stream"
        )
        
    except ValidationError as e:
        api_logger.error(f"直接流式生成请求参数验证错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"直接流式生成请求服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@stream_router.post("/validate-model")
async def stream_validate_model(request: Request):
    """流式验证模型是否可用"""
    api_logger.info(f"收到流式模型验证请求")
    
    try:
        # 解析请求体
        body = await request.json()
        model_name = body.get("model_name")
        
        if not model_name:
            raise HTTPException(status_code=400, detail="缺少model_name参数")
            
        async def validate_generator():
            """验证模型并生成事件流"""
            try:
                # 发送开始验证事件
                yield json.dumps({
                    "type": "progress",
                    "message": f"开始验证模型: {model_name}",
                    "progress": 10
                })
                
                # 验证模型
                start_time = time.time()
                is_valid = await ai_service.validate_model(model_name)
                validation_time = time.time() - start_time
                
                # 发送验证结果
                if is_valid:
                    yield json.dumps({
                        "type": "progress",
                        "message": f"获取模型信息中...",
                        "progress": 50
                    })
                    
                    # 获取模型信息
                    model_info = await ai_service.get_model_info(model_name)
                    
                    yield json.dumps({
                        "type": "completed",
                        "result": {
                            "model_name": model_name,
                            "is_valid": True,
                            "validation_time": f"{validation_time:.2f}秒",
                            "model_info": model_info
                        }
                    })
                else:
                    yield json.dumps({
                        "type": "error",
                        "message": f"模型 {model_name} 验证失败"
                    })
                    
            except Exception as e:
                api_logger.error(f"流式验证模型失败: {model_name}, 错误: {str(e)}", exc_info=True)
                yield json.dumps({
                    "type": "error",
                    "message": f"验证模型时发生错误: {str(e)}"
                })
                
        # 返回SSE响应
        api_logger.info(f"开始流式验证模型: {model_name}")
        return EventSourceResponse(
            validate_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        api_logger.error(f"流式验证模型请求服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@stream_router.get("/status/{video_id}")
async def get_streaming_status(video_id: str):
    """获取流式处理状态"""
    api_logger.info(f"查询流式处理状态: {video_id}")

    try:
        # 提取视频ID
        real_video_id = transcript_service.extract_video_id(video_id)
        
        if real_video_id not in streaming_status:
            api_logger.warning(f"未找到视频处理记录: {real_video_id}")
            raise HTTPException(status_code=404, detail="未找到该视频的处理记录")

        status = streaming_status[real_video_id]
        api_logger.info(f"返回流式处理状态: {real_video_id}, status={status.status}, progress={status.progress}")
        return status
        
    except ValueError as e:
        api_logger.error(f"获取流式状态参数错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"获取流式状态服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@stream_router.delete("/status/{video_id}")
async def clear_streaming_status(video_id: str):
    """清除流式处理状态"""
    api_logger.info(f"清除流式处理状态: {video_id}")

    try:
        # 提取视频ID
        real_video_id = transcript_service.extract_video_id(video_id)
        
        if real_video_id in streaming_status:
            del streaming_status[real_video_id]
            api_logger.info(f"流式处理状态已清除: {real_video_id}")
            return {"message": "状态已清除"}
        else:
            api_logger.warning(f"未找到要清除的流式处理记录: {real_video_id}")
            raise HTTPException(status_code=404, detail="未找到该视频的处理记录")
            
    except ValueError as e:
        api_logger.error(f"清除流式状态参数错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"清除流式状态服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")
