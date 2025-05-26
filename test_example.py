#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试示例脚本
"""
import asyncio
from app.services.transcript_service import TranscriptService

async def test_transcript_service():
    """测试字幕服务"""
    service = TranscriptService()

    # 使用示例视频ID（这是一个公开的教育视频）
    video_id = "dPiKBDgsicQ"  # 来自main.py的示例

    try:
        print(f"正在获取视频 {video_id} 的字幕...")
        segments = service.get_transcript(video_id, "en")
        print(f"成功获取 {len(segments)} 个字幕片段")

        # 显示前几个片段
        for i, segment in enumerate(segments[:3]):
            print(f"片段 {i+1}: {segment.text}")

        # 合并字幕文本
        full_text = service.combine_transcript_text(segments)
        print(f"\n完整字幕长度: {len(full_text)} 字符")
        print(f"前200字符: {full_text[:200]}...")

    except Exception as e:
        print(f"获取字幕失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_transcript_service())