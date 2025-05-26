# -*- coding: utf-8 -*-
"""
字幕获取服务
"""
import re
import time
from typing import (
    List,
)

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
)

from app.models import TranscriptSegment
from app.utils.logger import transcript_logger


class TranscriptService:
    """YouTube字幕获取服务"""

    def __init__(self):
        transcript_logger.info("初始化字幕服务")
        self.api = YouTubeTranscriptApi()

    def extract_video_id(self, url_or_id: str) -> str:
        """从URL或直接ID中提取视频ID"""
        transcript_logger.info(f"提取视频ID: {url_or_id}")

        # 如果已经是视频ID格式，直接返回
        if re.match(r'^[a-zA-Z0-9_-]{11}$', url_or_id):
            transcript_logger.info(f"输入已是视频ID格式: {url_or_id}")
            return url_or_id

        # 从各种YouTube URL格式中提取视频ID
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        ]

        for i, pattern in enumerate(patterns):
            match = re.search(pattern, url_or_id)
            if match:
                video_id = match.group(1)
                transcript_logger.info(f"使用模式{i+1}成功提取视频ID: {video_id}")
                return video_id

        transcript_logger.error(f"无法从输入中提取有效的YouTube视频ID: {url_or_id}")
        raise ValueError(f"无法从 '{url_or_id}' 中提取有效的YouTube视频ID")

    def get_transcript(self, video_id: str, language: str = 'en') -> List[TranscriptSegment]:
        """获取视频字幕"""
        transcript_logger.info(f"开始获取字幕: video_id={video_id}, language={language}")
        start_time = time.time()

        try:
            # 尝试获取指定语言的字幕
            transcript_logger.info(f"调用YouTube API获取字幕: {video_id}")
            transcript_data = self.api.fetch(video_id)

            # 转换为我们的数据模型
            transcript_logger.info(f"开始转换字幕数据，原始段数: {len(transcript_data)}")
            segments = []
            for i, item in enumerate(transcript_data):
                segment = TranscriptSegment(
                    text=item.text,
                    start=item.start,
                    duration=item.duration
                )
                segments.append(segment)

                # 每100段记录一次进度
                if (i + 1) % 100 == 0:
                    transcript_logger.debug(f"已转换字幕段: {i + 1}/{len(transcript_data)}")

            fetch_time = time.time() - start_time
            total_duration = sum(segment.duration for segment in segments)
            transcript_logger.info(f"字幕获取成功: video_id={video_id}, 段数={len(segments)}, 总时长={total_duration:.2f}秒, 耗时={fetch_time:.2f}秒")

            return segments

        except TranscriptsDisabled:
            error_time = time.time() - start_time
            transcript_logger.error(f"字幕功能被禁用: video_id={video_id}, 耗时={error_time:.2f}秒")
            raise ValueError("该视频的字幕功能已被禁用")
        except NoTranscriptFound:
            error_time = time.time() - start_time
            transcript_logger.error(f"未找到字幕: video_id={video_id}, language={language}, 耗时={error_time:.2f}秒")
            raise ValueError("该视频没有可用的字幕")
        except Exception as e:
            error_time = time.time() - start_time
            transcript_logger.error(f"获取字幕失败: video_id={video_id}, 耗时={error_time:.2f}秒, 错误={str(e)}", exc_info=True)
            raise ValueError(f"获取字幕时发生错误: {str(e)}")

    def combine_transcript_text(self, segments: List[TranscriptSegment]) -> str:
        """将字幕片段合并为完整文本"""
        transcript_logger.info(f"合并字幕文本，段数: {len(segments)}")
        start_time = time.time()

        combined_text = " ".join([segment.text for segment in segments])

        combine_time = time.time() - start_time
        transcript_logger.info(f"字幕合并完成，总长度: {len(combined_text)}字符, 耗时: {combine_time:.3f}秒")

        return combined_text
