"""AI 内容生成器.

支持一句话生成完整文案，并自动适配各平台格式。
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.ai.mimo_client import MiMoClient, ChatMessage

logger = logging.getLogger(__name__)

STYLES = {
    "tech-tutorial": {
        "name": "技术教程",
        "description": "专业技术教程，结构清晰，包含代码示例",
        "instruction": "写一篇专业技术教程，要求：结构清晰有层次，包含代码示例，语言通俗易懂。",
    },
    "product-review": {
        "name": "产品评测",
        "description": "产品深度评测，包含优缺点分析",
        "instruction": "写一篇产品深度评测，要求：客观公正，包含优缺点分析，有使用体验。",
    },
    "daily-share": {
        "name": "日常分享",
        "description": "轻松的生活分享，亲切自然",
        "instruction": "写一篇轻松的日常分享，要求：语气亲切自然，有个人感受，贴近生活。",
    },
    "industry-analysis": {
        "name": "行业分析",
        "description": "深度行业分析，数据支撑，有洞见",
        "instruction": "写一篇深度行业分析，要求：有数据支撑，观点独到，逻辑严密。",
    },
    "general": {
        "name": "通用",
        "description": "通用内容风格",
        "instruction": "写一篇优质内容，要求：结构清晰，内容充实，有吸引力。",
    },
}

PLATFORM_TRAITS = {
    "wechat": {"name": "微信公众号", "traits": "文章可以较长（2000-5000字），支持富文本格式", "length": "2000-5000字"},
    "zhihu": {"name": "知乎", "traits": "专业性强，需要有理有据，支持 Markdown 格式", "length": "1500-4000字"},
    "bilibili": {"name": "B站专栏", "traits": "风格轻松活泼，可以使用网络用语", "length": "1000-3000字"},
    "xiaohongshu": {"name": "小红书", "traits": "标题要有吸引力（20字以内），正文简洁，多用 emoji", "length": "300-800字"},
    "douyin": {"name": "抖音", "traits": "内容简洁有力，开头要有 hook，添加互动引导", "length": "200-600字"},
    "weibo": {"name": "微博", "traits": "内容精炼，话题性强，添加话题标签", "length": "100-500字"},
}

_SYSTEM_PROMPT = """你是一个专业的内容创作助手。你擅长根据简短的描述生成完整的优质文章。

你的输出必须是严格的 JSON 格式，包含以下字段：
{
  "title": "文章标题（简洁有力，吸引读者）",
  "content": "文章正文（Markdown 格式）",
  "tags": ["标签1", "标签2", "标签3"],
  "summary": "一句话摘要（50字以内）"
}

要求：
1. 标题要吸引人，能引起读者点击欲望
2. 正文结构清晰，使用 Markdown 标题、列表、代码块等格式
3. 内容充实有价值，不要空洞的废话
4. 标签选择精准，3-5个为宜
5. 输出必须是合法的 JSON，不要包含任何其他文本"""

_PLATFORM_PROMPT = """
目标平台：{platform_name}
平台特点：{traits}
建议长度：{length}
请根据平台特点调整内容风格和长度。"""

_STYLE_PROMPT = """
内容风格：{style_name}
风格要求：{instruction}"""


@dataclass
class GeneratedContent:
    """AI 生成的内容."""
    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    prompt: str = ""
    style: str = "general"
    target_platform: str = ""


class ContentGenerator:
    """AI 内容生成器."""

    def __init__(self, client: Optional[MiMoClient] = None):
        self.client = client or MiMoClient()

    @property
    def is_available(self) -> bool:
        return self.client.is_available

    def generate(
        self,
        prompt: str,
        style: str = "general",
        target_platform: Optional[str] = None,
        title: Optional[str] = None,
    ) -> GeneratedContent:
        if not prompt or not prompt.strip():
            raise ValueError("内容描述不能为空")
        if style not in STYLES:
            raise ValueError(f"不支持的内容风格: {style}，可选: {list(STYLES.keys())}")
        if target_platform and target_platform not in PLATFORM_TRAITS:
            raise ValueError(f"不支持的平台: {target_platform}，可选: {list(PLATFORM_TRAITS.keys())}")

        system_prompt = _SYSTEM_PROMPT
        style_info = STYLES[style]
        system_prompt += _STYLE_PROMPT.format(
            style_name=style_info["name"], instruction=style_info["instruction"],
        )
        if target_platform:
            platform_info = PLATFORM_TRAITS[target_platform]
            system_prompt += _PLATFORM_PROMPT.format(
                platform_name=platform_info["name"], traits=platform_info["traits"], length=platform_info["length"],
            )

        user_prompt = prompt
        if title:
            user_prompt = f"请以「{title}」为标题，{prompt}"

        logger.info("AI 生成内容: prompt=%s, style=%s, platform=%s", prompt[:50], style, target_platform)
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt),
        ]
        response_text = self.client.chat(messages)
        result = self._parse_response(response_text.content)

        return GeneratedContent(
            title=result.get("title", title or ""),
            content=result.get("content", ""),
            tags=result.get("tags", []),
            summary=result.get("summary", ""),
            prompt=prompt, style=style, target_platform=target_platform or "",
        )

    def generate_for_platforms(
        self, prompt: str, style: str = "general", platforms: Optional[List[str]] = None, title: Optional[str] = None,
    ) -> Dict[str, GeneratedContent]:
        if platforms is None:
            platforms = list(PLATFORM_TRAITS.keys())
        results = {}
        for platform in platforms:
            try:
                results[platform] = self.generate(prompt=prompt, style=style, target_platform=platform, title=title)
            except Exception as e:
                logger.error("为平台 %s 生成内容失败: %s", platform, e)
                results[platform] = GeneratedContent(prompt=prompt, style=style, target_platform=platform)
        return results

    @staticmethod
    def _parse_response(text: str) -> Dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(text[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass
        logger.warning("无法解析 AI 响应为 JSON，使用原始文本作为内容")
        return {"title": "", "content": text, "tags": [], "summary": ""}

    @staticmethod
    def list_styles() -> Dict[str, Dict[str, str]]:
        return dict(STYLES)

    @staticmethod
    def list_platforms() -> Dict[str, Dict[str, str]]:
        return dict(PLATFORM_TRAITS)
