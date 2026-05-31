"""结构化内容文档模型.

提供内容的中间表示，替代原始 Markdown 字符串在管线中流转。
支持序列化为 Markdown / 纯文本，供各平台适配器消费。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ImageRef:
    """图片引用.

    Attributes:
        src: 图片路径或URL
        alt: 替代文本
        title: 图片标题
        caption: 图片说明
        width: 图片宽度（像素）
        height: 图片高度（像素）
    """

    src: str
    alt: str = ""
    title: str = ""
    caption: str = ""
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class ContentSection:
    """内容段落.

    Attributes:
        section_type: 段落类型 (heading/paragraph/code/blockquote/list/image/divider)
        level: 层级（标题级别、列表缩进等）
        text: 文本内容
        children: 子段落（用于列表项、嵌套引用等）
        metadata: 扩展元数据（代码语言、列表类型等）
    """

    section_type: str
    level: int = 0
    text: str = ""
    children: List["ContentSection"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_plain_text(self) -> str:
        """获取段落的纯文本表示."""
        if self.section_type == "divider":
            return "---"
        if self.section_type == "list":
            lines = []
            for i, child in enumerate(self.children):
                prefix = "- " if self.metadata.get("list_type", "unordered") == "unordered" else f"{i + 1}. "
                lines.append(prefix + child.get_plain_text())
            return "\n".join(lines)
        if self.section_type == "code":
            lang = self.metadata.get("language", "")
            return f"```{lang}\n{self.text}\n```"
        if self.section_type == "blockquote":
            lines = self.text.split("\n")
            return "\n".join(f"> {line}" for line in lines)
        return self.text


@dataclass
class ContentDocument:
    """结构化内容文档.

    替代原始 Markdown 字符串，作为内容在管线中的标准表示。
    支持序列化回 Markdown / 纯文本。

    Attributes:
        title: 文章标题
        subtitle: 副标题
        body: 正文段落列表
        images: 图片引用列表
        tags: 标签列表
        category: 分类
        metadata: 扩展元数据
    """

    title: str = ""
    subtitle: str = ""
    body: List[ContentSection] = field(default_factory=list)
    images: List[ImageRef] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """序列化为 Markdown 格式."""
        parts: List[str] = []

        # 标题
        if self.title:
            parts.append(f"# {self.title}")
            parts.append("")

        # 副标题
        if self.subtitle:
            parts.append(f"## {self.subtitle}")
            parts.append("")

        # 元数据行
        if self.category or self.tags:
            meta_parts: List[str] = []
            if self.category:
                meta_parts.append(f"分类: {self.category}")
            if self.tags:
                meta_parts.append(f"标签: {', '.join(self.tags)}")
            parts.append(f"> {' | '.join(meta_parts)}")
            parts.append("")

        # 正文段落
        for section in self.body:
            if section.section_type == "heading":
                parts.append(f"{'#' * section.level} {section.text}")
            else:
                parts.append(section.get_plain_text())
            parts.append("")

        return "\n".join(parts).strip()

    def to_plain_text(self) -> str:
        """序列化为纯文本（去除所有 Markdown 标记）."""
        parts: List[str] = []

        if self.title:
            parts.append(self.title)
            parts.append("")

        if self.subtitle:
            parts.append(self.subtitle)
            parts.append("")

        for section in self.body:
            text = section.text
            # 去除行内 Markdown 标记
            import re
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
            text = re.sub(r"\*(.+?)\*", r"\1", text)  # italic
            text = re.sub(r"`(.+?)`", r"\1", text)  # code
            text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # links
            parts.append(text)
            parts.append("")

        return "\n".join(parts).strip()

    def get_word_count(self) -> int:
        """获取正文字数（中文按字计数，英文按词计数）."""
        import re
        text = " ".join(s.text for s in self.body)
        # 中文字符数
        chinese_chars = len(re.findall(r"[一-鿿]", text))
        # 英文单词数
        english_words = len(re.findall(r"[a-zA-Z]+", text))
        return chinese_chars + english_words

    def get_image_count(self) -> int:
        """获取图片总数."""
        return len(self.images)

    @classmethod
    def from_draft(cls, draft: Any) -> "ContentDocument":
        """从 Draft 对象创建 ContentDocument.

        Args:
            draft: Draft 对象（来自 draft_manager）

        Returns:
            ContentDocument 实例
        """
        from .content_parser import ContentParser

        parser = ContentParser()
        return parser.parse(
            draft.content.content,
            title=draft.content.title,
            tags=draft.content.tags,
        )
