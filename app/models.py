# -*- coding: utf-8 -*-
"""
数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """字幕片段"""
    text: str
    start: float
    duration: float


class VideoRequest(BaseModel):
    """视频处理请求"""
    video_id: str = Field(..., description="YouTube视频ID")
    model_name: str = Field(default="gpt-3.5-turbo", description="使用的AI模型")
    language: str = Field(default="zh", description="讲义语言")


class LectureNote(BaseModel):
    """生成的讲义"""
    title: str
    content: str
    video_id: str
    model_used: str
    created_at: str


class ProcessingStatus(BaseModel):
    """处理状态"""
    status: str  # "processing", "completed", "error"
    message: str
    progress: Optional[int] = None
    result: Optional[LectureNote] = None


class ModelConfig(BaseModel):
    """模型配置"""
    name: str
    display_name: str
    provider: str
    description: str