# -*- coding: utf-8 -*-
"""
API路由
"""
import asyncio
import time
from typing import List, Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse

from app.models import VideoRequest, LectureNote, ProcessingStatus, ModelConfig
# 使用新的 AIService 取代旧的 LLMService
from app.services.transcript_service import TranscriptService
from app.services.ai_service import AIService
from app.utils.logger import api_logger, log_api_request

router = APIRouter()

# 全局服务实例
transcript_service = TranscriptService()
ai_service = AIService()

# 存储处理状态的简单内存存储（生产环境应使用数据库）
processing_status: Dict[str, ProcessingStatus] = {}


async def process_video_async(video_id: str, model_name: str, language: str):
    """异步处理视频"""
    start_time = time.time()
    api_logger.info(f"开始异步处理视频 - video_id: {video_id}, model: {model_name}, language: {language}")

    try:
        # 更新状态：开始获取字幕
        api_logger.info(f"[{video_id}] 开始获取视频字幕")
        processing_status[video_id] = ProcessingStatus(
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
        processing_status[video_id] = ProcessingStatus(
            status="processing",
            message="正在生成讲义...",
            progress=60
        )

        # 生成讲义
        llm_start = time.time()
        lecture_note = await ai_service.generate_lecture_note(
            transcript_text=transcript_text,
            video_id=video_id,
            model_name=model_name,
            language=language
        )
        llm_time = time.time() - llm_start

        api_logger.info(f"[{video_id}] 讲义生成完成，耗时: {llm_time:.2f}秒，讲义长度: {len(lecture_note.content)}字符")

        # 更新状态：完成
        processing_status[video_id] = ProcessingStatus(
            status="completed",
            message="讲义生成完成",
            progress=100,
            result=lecture_note
        )

        total_time = time.time() - start_time
        api_logger.info(f"[{video_id}] 视频处理完成，总耗时: {total_time:.2f}秒")

    except Exception as e:
        error_time = time.time() - start_time
        api_logger.error(f"[{video_id}] 视频处理失败，耗时: {error_time:.2f}秒，错误: {str(e)}", exc_info=True)

        # 更新状态：错误
        processing_status[video_id] = ProcessingStatus(
            status="error",
            message=f"处理失败: {str(e)}",
            progress=0
        )


@router.post("/models/validate")
async def validate_model(request: Dict[str, str]):
    """验证用户指定的模型是否可用"""
    api_logger.info(f"收到模型验证请求: {request}")

    model_name = request.get("model_name")
    if not model_name:
        api_logger.warning("模型验证请求缺少model_name参数")
        raise HTTPException(status_code=400, detail="缺少model_name参数")

    try:
        api_logger.info(f"开始验证模型: {model_name}")
        start_time = time.time()

        is_valid = await ai_service.validate_model(model_name)
        model_info = await ai_service.get_model_info(model_name)

        validation_time = time.time() - start_time
        api_logger.info(f"模型验证完成: {model_name}, 有效性: {is_valid}, 耗时: {validation_time:.2f}秒")

        return {
            "model_name": model_name,
            "is_valid": is_valid,
            "model_info": model_info
        }
    except Exception as e:
        api_logger.error(f"验证模型失败: {model_name}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证模型失败: {str(e)}")


@router.get("/models/{model_name}/info")
async def get_model_info(model_name: str):
    """获取指定模型的详细信息"""
    api_logger.info(f"获取模型信息请求: {model_name}")

    try:
        start_time = time.time()
        model_info = await ai_service.get_model_info(model_name)
        info_time = time.time() - start_time

        api_logger.info(f"获取模型信息成功: {model_name}, 耗时: {info_time:.2f}秒")
        return model_info
    except Exception as e:
        api_logger.error(f"获取模型信息失败: {model_name}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")


@router.post("/process", response_model=Dict[str, str])
async def process_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """处理视频，生成讲义"""
    api_logger.info(f"收到视频处理请求: video_id={request.video_id}, model={request.model_name}, language={request.language}")

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
        processing_status[video_id] = ProcessingStatus(
            status="processing",
            message="开始处理...",
            progress=0
        )

        # 添加后台任务
        api_logger.info(f"添加后台处理任务: {video_id}")
        background_tasks.add_task(
            process_video_async,
            video_id,
            request.model_name,
            request.language
        )

        api_logger.info(f"视频处理请求已接受: {video_id}")
        return {"message": "处理已开始", "video_id": video_id}

    except ValueError as e:
        api_logger.error(f"视频处理请求参数错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"视频处理请求服务器错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/status/{video_id}", response_model=ProcessingStatus)
async def get_processing_status(video_id: str):
    """获取处理状态"""
    api_logger.info(f"查询处理状态: {video_id}")

    if video_id not in processing_status:
        api_logger.warning(f"未找到视频处理记录: {video_id}")
        raise HTTPException(status_code=404, detail="未找到该视频的处理记录")

    status = processing_status[video_id]
    api_logger.info(f"返回处理状态: {video_id}, status={status.status}, progress={status.progress}")
    return status


@router.get("/result/{video_id}", response_model=LectureNote)
async def get_lecture_note(video_id: str):
    """获取生成的讲义"""
    api_logger.info(f"获取讲义结果: {video_id}")

    if video_id not in processing_status:
        api_logger.warning(f"未找到视频处理记录: {video_id}")
        raise HTTPException(status_code=404, detail="未找到该视频的处理记录")

    status = processing_status[video_id]
    if status.status != "completed" or not status.result:
        api_logger.warning(f"讲义尚未生成完成: {video_id}, status={status.status}")
        raise HTTPException(status_code=400, detail="讲义尚未生成完成")

    api_logger.info(f"成功返回讲义: {video_id}, 内容长度: {len(status.result.content)}字符")
    return status.result


@router.get("/transcript/{video_id}")
async def get_video_transcript(video_id: str, language: str = "zh"):
    """获取视频字幕（用于预览）"""
    api_logger.info(f"获取视频字幕: video_id={video_id}, language={language}")

    try:
        start_time = time.time()
        video_id = transcript_service.extract_video_id(video_id)
        api_logger.info(f"提取到的视频ID: {video_id}")

        segments = transcript_service.get_transcript(video_id, language)
        transcript_text = transcript_service.combine_transcript_text(segments)

        transcript_time = time.time() - start_time
        api_logger.info(f"字幕获取成功: {video_id}, 段数: {len(segments)}, 总长度: {len(transcript_text)}字符, 耗时: {transcript_time:.2f}秒")

        return {
            "video_id": video_id,
            "language": language,
            "segments": [segment.dict() for segment in segments],
            "full_text": transcript_text
        }

    except ValueError as e:
        api_logger.error(f"获取字幕参数错误: {video_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        api_logger.error(f"获取字幕服务器错误: {video_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.delete("/status/{video_id}")
async def clear_processing_status(video_id: str):
    """清除处理状态"""
    api_logger.info(f"清除处理状态: {video_id}")

    if video_id in processing_status:
        del processing_status[video_id]
        api_logger.info(f"处理状态已清除: {video_id}")
        return {"message": "状态已清除"}
    else:
        api_logger.warning(f"未找到要清除的处理记录: {video_id}")
        raise HTTPException(status_code=404, detail="未找到该视频的处理记录")
