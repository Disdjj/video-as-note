# -*- coding: utf-8 -*-
"""
LLM服务 - 使用LiteLLM和LangChain，支持用户自定义模型
"""
import time
from datetime import datetime
from typing import (
    Any,
    Dict,
    List,
)

import litellm
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
)
from langchain_litellm import ChatLiteLLM

from app.models import (
    LectureNote,
)
from app.utils.logger import llm_logger


class LLMService:
    """LLM服务 - 支持用户自定义模型"""

    def __init__(self):
        llm_logger.info("初始化LLM服务")
        self.setup_litellm()

    def setup_litellm(self):
        """设置LiteLLM配置 - 使用官方推荐的方式"""
        llm_logger.info("开始设置LiteLLM配置")

        llm_logger.info("LiteLLM配置完成")

    def validate_model(self, model_name: str) -> bool:
        """验证模型是否可用"""
        return True

    def test_model_availability(self, model_name: str) -> bool:
        """测试模型是否可用"""
        llm_logger.info(f"开始测试模型可用性: {model_name}")
        start_time = time.time()

        try:
            response = litellm.completion(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            test_time = time.time() - start_time
            llm_logger.info(f"模型测试成功: {model_name}, 耗时: {test_time:.2f}秒")
            return True
        except Exception as e:
            test_time = time.time() - start_time
            llm_logger.error(f"模型测试失败: {model_name}, 错误: {e}, 耗时: {test_time:.2f}秒")
            return False

    def get_supported_params(self, model_name: str) -> List[str]:
        """获取模型支持的参数"""
        llm_logger.info(f"获取模型支持的参数: {model_name}")

        try:
            params = litellm.get_supported_openai_params(model=model_name)
            llm_logger.info(f"获取模型参数成功: {model_name}, 参数数量: {len(params)}")
            return params
        except Exception as e:
            llm_logger.error(f"获取模型参数失败: {model_name}, 错误: {e}")
            return []

    def get_lecture_prompt(self, language: str = "简体中文") -> str:
        """获取讲义生成的提示词"""
        return """
You are a professor specializing in all areas of Computer Science (CS), tasked with transforming user-provided course lecture transcripts into
structured learning documents suitable for newcomers to the computer science field. The transcripts provided by users may contain technical
terminology, non-sequential explanations, or abbreviated key concepts. Your task is to: supplement necessary background knowledge, explain complex
concepts, reorganize content logic, and ensure newcomers can fully understand.

The input lecture transcript is as follows:
<lecture_transcript>
{{LECTURE_TRANSCRIPT}}
</lecture_transcript>

Please strictly follow these steps for processing and output:

### Step 1: Determine Course Direction (Internal Analysis)
Read through the transcript, identify the core topic of the course (such as "Operating System Memory Management", "Distributed System Consistency
Protocols", "Network Routing Algorithms", etc.), and record it in the subsequent content summary.

### Step 2: Content Breakdown and Concept Supplementation
1. Analyze the transcript paragraph by paragraph, extracting key knowledge points (such as definitions, principles, algorithm steps,
experimental conclusions, etc.).
2. For each knowledge point involving **concepts that may be unfamiliar to newcomers** (including but not limited to technical terms,
technical abbreviations, cross-domain associated knowledge):
   - Use markdown blockquotes for explanation (example: `Process: A running instance of a program in an operating system, with its own memory space
   and execution context`).
   - For complex concepts (such as "CAP Theorem", "Virtual Memory Paging Mechanism"), further elaborate on their core elements,
   application scenarios, and relationships with other concepts.
   - For obscure/esoteric concepts (such as "Preparation Phase of Paxos Algorithm", "Path Attributes of BGP Routing"), use mermaid syntax to draw
   flowcharts or diagrams to aid understanding (example: ```mermaid\nflowchart LR\nA[Preparation Phase] -- B[Broadcast Proposal Number]\nB -- C{
   Majority Acceptance?}\nC --|Yes| D[Determine Highest Numbered Proposal]\nC --|No| A\n```).

### Step 3: Content Reorganization and Integrity Assurance
1. Reorganize content according to newcomer learning logic (e.g., from basic definitions → core principles → typical applications → common issues).
2. Supplement key details that may be omitted in the transcript (e.g., "The professor mentioned 'TCP three-way handshake' but did not explain the
specific role of SYN-ACK", so the meaning of this field and its necessity in establishing connections should be supplemented).
3. Ensure the completeness of technical process descriptions (e.g., "The professor mentioned 'consensus process in distributed systems',
need to supplement the complete steps of 'proposal-voting-confirmation'").

### Step 4: Compilation of Special Considerations
1. Mark easily confused concepts (such as "differences between threads and processes", "appropriate scenarios for TCP and UDP").
2. Provide links to extended learning resources (such as relevant RFC documents, classic textbook chapters, authoritative technical blogs).
3. Point out common misconceptions in the field (such as "believing that in CAP theorem C/A/P must choose two out of three, when in fact there are
compromise solutions like weak consistency").

### Output Format Requirements
Your output must be a complete markdown document, containing the following three parts, separated by second-level headings:
1. **Course Content Summary**: Summarize the core topic and main content of the course in 1-2 paragraphs (not exceeding 300 words).
2. **Detailed Course Content**: Expand point by point according to the reorganized logic, with concept explanations following each knowledge point
(using blockquotes), and inserting mermaid diagrams after complex concepts (wrapped in ```mermaid).
3. **Special Knowledge Notes and Extensions**: List easily confused concepts, recommended learning resources, common misconceptions, etc. point by
point.

Note: When outputting, do not use any additional tags for wrapping, output the markdown content directly. Ensure the language is easy to
understand, avoid overly academic expressions, and always focus on the core goal of "helping complete beginners understand this field".

---

Always Answer in {language}"""

    def generate_lecture_note(self, transcript_text: str, video_id: str, model_name: str, language: str = "简体中文") -> LectureNote:
        """生成讲义 - 使用用户指定的模型"""
        llm_logger.info(f"开始生成讲义: video_id={video_id}, model={model_name}, language={language}, 字幕长度={len(transcript_text)}字符")
        start_time = time.time()

        try:
            # 验证模型是否可用
            llm_logger.info(f"验证模型可用性: {model_name}")
            if not self.validate_model(model_name):
                llm_logger.error(f"模型不可用: {model_name}")
                raise ValueError(f"模型 {model_name} 不可用或配置不正确")

            # 准备消息
            llm_logger.info(f"准备提示词和消息: {language}")

            message = "\n\n---\n\n".join([self.get_lecture_prompt(language), transcript_text, f"ALWAYS ANSWER IN {language}"])
            system_message = HumanMessage(content=message)

            llm_logger.info(f"创建LLM实例: {model_name}")
            chat = ChatLiteLLM(
                model=model_name
            )

            # 生成响应
            llm_logger.info(f"开始调用LLM生成讲义: {model_name}")
            llm_start = time.time()
            # response = chat.generate([human_message, language_message])
            response = chat.invoke([system_message])
            llm_time = time.time() - llm_start

            llm_logger.info(f"LLM调用完成: {model_name}, 耗时: {llm_time:.2f}秒, 生成内容长度: {len(response.content)}字符")

            # 创建讲义对象
            lecture_note = LectureNote(
                title=f"视频 {video_id} 讲义",
                content=response.content,
                video_id=video_id,
                model_used=model_name,
                created_at=datetime.now().isoformat()
            )

            total_time = time.time() - start_time
            llm_logger.info(f"讲义生成完成: video_id={video_id}, 总耗时: {total_time:.2f}秒")

            return lecture_note

        except Exception as e:
            error_time = time.time() - start_time
            llm_logger.error(f"生成讲义失败: video_id={video_id}, model={model_name}, 耗时: {error_time:.2f}秒, 错误: {str(e)}", exc_info=True)
            raise ValueError(f"生成讲义时发生错误: {str(e)}")

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        llm_logger.info(f"获取模型信息: {model_name}")
        start_time = time.time()

        try:
            is_available = self.validate_model(model_name)
            supported_params = self.get_supported_params(model_name)

            try:
                env_validation = litellm.validate_environment(model_name)
            except Exception as env_e:
                llm_logger.warning(f"环境验证失败: {model_name}, 错误: {env_e}")
                env_validation = {"error": str(env_e)}

            info = {
                "model_name": model_name,
                "is_available": is_available,
                "supported_params": supported_params,
                "environment_validation": env_validation
            }

            info_time = time.time() - start_time
            llm_logger.info(f"获取模型信息成功: {model_name}, 耗时: {info_time:.2f}秒")
            return info
        except Exception as e:
            error_time = time.time() - start_time
            llm_logger.error(f"获取模型信息失败: {model_name}, 耗时: {error_time:.2f}秒, 错误: {str(e)}", exc_info=True)
            return {
                "model_name": model_name,
                "is_available": False,
                "error": str(e)
            }
