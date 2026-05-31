"""MiMo 大模型 API 客户端.

基于 Anthropic 兼容格式，支持小米 MiMo 模型的调用。
支持通过环境变量配置 API Key 和 Base URL。
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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
    """MiMo 大模型 API 客户端.

    使用 Anthropic 兼容的 Messages API 格式。

    Attributes:
        api_key: API 密钥
        base_url: API 基础地址
        model: 模型名称
        temperature: 生成温度 (0-1)
        max_tokens: 最大生成 token 数
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "mimo-v2.5-pro",
        temperature: float = 0.6,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or os.getenv("MIMO_API_KEY", "")
        self.base_url = (base_url or os.getenv("MIMO_BASE_URL", "")).rstrip("/")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None
        self._available = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic 包未安装，请执行: pip install anthropic")
            return None
        if not self.api_key:
            logger.warning("未配置 MIMO_API_KEY，AI 生成功能不可用")
            return None
        if not self.base_url:
            logger.warning("未配置 MIMO_BASE_URL，AI 生成功能不可用")
            return None
        try:
            self._client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=120.0,
            )
            logger.info("MiMo 客户端初始化成功: %s", self.base_url)
            return self._client
        except Exception as e:
            logger.error("MiMo 客户端初始化失败: %s", e)
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

        # 分离 system message 和 user/assistant messages
        system_text = ""
        api_messages = []
        for m in messages:
            if m.role == "system":
                system_text = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})

        try:
            kwargs = {
                "model": self.model,
                "messages": api_messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
            }
            if system_text:
                kwargs["system"] = system_text

            response = client.messages.create(**kwargs)

            # 提取文本内容
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text

            usage = {}
            if response.usage:
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }

            return ChatResponse(
                content=content,
                model=response.model or self.model,
                usage=usage,
                finish_reason=response.stop_reason or "",
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
