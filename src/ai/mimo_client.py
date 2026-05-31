"""MiMo 大模型 API 客户端.

基于 OpenAI 兼容格式，支持小米 MiMo 模型的调用。
支持通过环境变量配置 API Key 和 Base URL。
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# 候选 API 端点列表（按优先级排序）
_CANDIDATE_BASE_URLS = [
    "https://api.xiaomi.com/v1",
    "https://api.mi.com/v1",
    "https://open.bigmodel.cn/api/v1",
    "https://api.siliconflow.cn/v1",
]


@dataclass
class ChatMessage:
    """聊天消息."""
    role: str
    content: str


@dataclass
class ChatResponse:
    """聊天响应."""
    content: str = ""
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""


class MiMoClient:
    """MiMo 大模型 API 客户端."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "MiMo-7B-RL",
        temperature: float = 0.6,
        top_p: float = 0.95,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self.base_url = (base_url or os.getenv("MIMO_BASE_URL", "")).rstrip("/")
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self._client = None
        self._available = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError:
            logger.warning("openai 包未安装，请执行: pip install openai")
            return None
        if not self.api_key:
            logger.warning("未配置 MIMO_API_KEY，AI 生成功能不可用")
            return None
        if not self.base_url:
            self.base_url = self._detect_base_url()
            if not self.base_url:
                logger.warning("无法检测到可用的 MiMo API 端点")
                return None
        try:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120.0,
            )
            logger.info("MiMo 客户端初始化成功: %s", self.base_url)
            return self._client
        except Exception as e:
            logger.error("MiMo 客户端初始化失败: %s", e)
            return None

    def _detect_base_url(self) -> Optional[str]:
        try:
            import httpx
        except ImportError:
            return _CANDIDATE_BASE_URLS[0] if _CANDIDATE_BASE_URLS else None
        for url in _CANDIDATE_BASE_URLS:
            try:
                resp = httpx.get(
                    f"{url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0,
                )
                if resp.status_code in (200, 401, 403):
                    logger.info("检测到可用端点: %s (status=%d)", url, resp.status_code)
                    return url
            except Exception:
                continue
        return None

    @property
    def is_available(self) -> bool:
        if self._available is None:
            client = self._get_client()
            self._available = client is not None
        return self._available

    def chat(
        self,
        messages: List[ChatMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> ChatResponse:
        client = self._get_client()
        if client is None:
            raise RuntimeError("MiMo 客户端不可用，请检查 API Key 和网络配置")
        msg_dicts = [{"role": m.role, "content": m.content} for m in messages]
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=msg_dicts,
                temperature=temperature or self.temperature,
                top_p=self.top_p,
                max_tokens=max_tokens or self.max_tokens,
            )
            choice = response.choices[0]
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            return ChatResponse(
                content=choice.message.content or "",
                model=response.model or self.model,
                usage=usage,
                finish_reason=choice.finish_reason or "",
            )
        except Exception as e:
            logger.error("MiMo API 调用失败: %s", e)
            raise RuntimeError(f"MiMo API 调用失败: {e}") from e

    def chat_simple(self, user_message: str, system_message: str = "") -> str:
        messages = []
        if system_message:
            messages.append(ChatMessage(role="system", content=system_message))
        messages.append(ChatMessage(role="user", content=user_message))
        response = self.chat(messages)
        return response.content
