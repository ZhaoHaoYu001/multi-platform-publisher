"""YAML 规则引擎.

从 YAML 配置文件加载平台适配规则，驱动内容变换流水线。
替代各平台类中硬编码的 regex 适配逻辑。
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import yaml

from .content_document import ContentDocument, ContentSection
from .transforms import ContentTransforms


@dataclass
class TitleRule:
    """标题适配规则."""

    max_length: int = 100
    strategy: str = "truncate_with_ellipsis"
    forbidden_patterns: List[str] = field(default_factory=list)
    add_hashtag: bool = False
    add_emoji: bool = False
    allow_question_ending: bool = False


@dataclass
class TransformStep:
    """单个变换步骤."""

    name: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentRule:
    """内容适配规则."""

    output_format: str = "markdown"
    paragraph_style: str = ""
    image_display: str = ""
    image_max_width: Optional[int] = None
    max_paragraph_length: Optional[int] = None
    transforms: List[TransformStep] = field(default_factory=list)


@dataclass
class ToneRule:
    """语气风格规则."""

    style: str = "neutral"
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaRule:
    """媒体资源规则."""

    image_ratio: str = ""
    image_min_size: int = 0
    image_max_size_mb: float = 10.0
    max_images: int = 10
    support_gif: bool = False
    video_max_resolution: str = ""
    video_max_fps: int = 0


@dataclass
class PlatformRules:
    """平台完整规则集."""

    platform: str = ""
    title: TitleRule = field(default_factory=TitleRule)
    content: ContentRule = field(default_factory=ContentRule)
    tone: Optional[ToneRule] = None
    media: Optional[MediaRule] = None


class RuleEngine:
    """规则引擎：加载 YAML 规则并执行内容适配.

    使用示例:
        engine = RuleEngine("config/rules")
        adapted_title = engine.adapt_title("长标题...", "wechat")
        adapted_content = engine.adapt_content(doc, "wechat")
    """

    # 变换函数名称到实际函数的映射
    _TRANSFORM_MAP: Dict[str, Callable] = {
        "heading_to_html": ContentTransforms.heading_to_html,
        "heading_to_bold": ContentTransforms.heading_to_bold,
        "bold_to_strong": ContentTransforms.bold_to_strong,
        "italic_to_em": ContentTransforms.italic_to_em,
        "code_to_code_tag": ContentTransforms.code_to_code_tag,
        "blockquote_to_html": ContentTransforms.blockquote_to_html,
        "wrap_paragraphs": ContentTransforms.wrap_paragraphs,
        "markdown_to_bbcode": ContentTransforms.markdown_to_bbcode,
        "markdown_to_plain": ContentTransforms.markdown_to_plain,
        "add_emoji_decorations": ContentTransforms.add_emoji_decorations,
        "add_hashtags": ContentTransforms.add_hashtags,
        "add_salt_marks": ContentTransforms.add_salt_marks,
        "add_code_language_annotation": ContentTransforms.add_code_language_annotation,
        "strip_code_language": ContentTransforms.strip_code_language,
        "divider_to_dash": ContentTransforms.divider_to_dash,
        "add_interaction_prompt": ContentTransforms.add_interaction_prompt,
        "add_original_declaration": ContentTransforms.add_original_declaration,
    }

    def __init__(self, rules_dir: str = "config/rules") -> None:
        """初始化规则引擎.

        Args:
            rules_dir: YAML 规则文件目录
        """
        self._rules_dir = rules_dir
        self._rules_cache: Dict[str, PlatformRules] = {}

    def load_rules(self, platform: str) -> PlatformRules:
        """加载平台规则（带缓存）.

        Args:
            platform: 平台名称

        Returns:
            PlatformRules 实例

        Raises:
            FileNotFoundError: 规则文件不存在时抛出
        """
        if platform in self._rules_cache:
            return self._rules_cache[platform]

        filepath = os.path.join(self._rules_dir, f"{platform}.yaml")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"规则文件不存在: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        rules = self._parse_rules(raw)
        self._rules_cache[platform] = rules
        return rules

    def _parse_rules(self, raw: Dict[str, Any]) -> PlatformRules:
        """将 YAML 字典解析为 PlatformRules."""
        title_raw = raw.get("title", {})
        title = TitleRule(
            max_length=title_raw.get("max_length", 100),
            strategy=title_raw.get("strategy", "truncate_with_ellipsis"),
            forbidden_patterns=title_raw.get("forbidden_patterns", []),
            add_hashtag=title_raw.get("add_hashtag", False),
            add_emoji=title_raw.get("add_emoji", False),
            allow_question_ending=title_raw.get("allow_question_ending", False),
        )

        content_raw = raw.get("content", {})
        transforms_raw = content_raw.get("transforms", [])
        transforms = [
            TransformStep(
                name=t.get("name", ""),
                params={k: v for k, v in t.items() if k != "name"},
            )
            for t in transforms_raw
        ]
        content = ContentRule(
            output_format=content_raw.get("output_format", "markdown"),
            paragraph_style=content_raw.get("paragraph_style", ""),
            image_display=content_raw.get("image_display", ""),
            image_max_width=content_raw.get("image_max_width"),
            max_paragraph_length=content_raw.get("max_paragraph_length"),
            transforms=transforms,
        )

        tone_raw = raw.get("tone")
        tone = None
        if tone_raw:
            extras = {k: v for k, v in tone_raw.items() if k != "style"}
            tone = ToneRule(
                style=tone_raw.get("style", "neutral"),
                extras=extras,
            )

        media_raw = raw.get("media")
        media = None
        if media_raw:
            media = MediaRule(
                image_ratio=media_raw.get("image_ratio", ""),
                image_min_size=media_raw.get("image_min_size", 0),
                image_max_size_mb=media_raw.get("image_max_size_mb", 10.0),
                max_images=media_raw.get("max_images", 10),
                support_gif=media_raw.get("support_gif", False),
                video_max_resolution=media_raw.get("video_max_resolution", ""),
                video_max_fps=media_raw.get("video_max_fps", 0),
            )

        return PlatformRules(
            platform=raw.get("platform", ""),
            title=title,
            content=content,
            tone=tone,
            media=media,
        )

    def adapt_title(self, title: str, platform: str) -> str:
        """适配标题.

        Args:
            title: 原始标题
            platform: 平台名称

        Returns:
            适配后的标题
        """
        rules = self.load_rules(platform)
        result = title

        # 去除禁止字符
        for pattern in rules.title.forbidden_patterns:
            result = re.sub(pattern, "", result)

        # 截断
        if len(result) > rules.title.max_length:
            if rules.title.strategy == "truncate_with_ellipsis":
                result = result[: rules.title.max_length - 3] + "..."
            else:  # truncate_clean
                result = result[: rules.title.max_length]

        return result

    def adapt_content(self, doc: ContentDocument, platform: str) -> str:
        """适配内容.

        Args:
            doc: ContentDocument 文档
            platform: 平台名称

        Returns:
            适配后的内容字符串
        """
        rules = self.load_rules(platform)

        # 将文档序列化为 Markdown 作为变换输入
        text = doc.to_markdown()

        # 跳过标题部分（标题单独处理）
        lines = text.split("\n")
        body_lines = []
        skip_header = True
        for line in lines:
            if skip_header and (line.startswith("# ") or line.strip() == "" or line.startswith("> ")):
                continue
            skip_header = False
            body_lines.append(line)
        text = "\n".join(body_lines).strip()

        # 应用变换流水线
        for step in rules.content.transforms:
            func = self._TRANSFORM_MAP.get(step.name)
            if func:
                # 合并语气风格中的额外参数（如 emoji_map）
                params = dict(step.params)
                if rules.tone and step.name == "add_emoji_decorations":
                    params.setdefault("emoji_map", rules.tone.extras.get("emoji_map", {}))
                text = func(text, **params)

        # 应用语气风格
        if rules.tone:
            text = self._apply_tone(text, rules.tone)

        return text

    def _apply_tone(self, text: str, tone: ToneRule) -> str:
        """应用语气风格规则."""
        if tone.extras.get("add_original_declaration"):
            text = ContentTransforms.add_original_declaration(text)
        if tone.extras.get("add_interaction_prompt"):
            text = ContentTransforms.add_interaction_prompt(text)
        return text

    def validate(self, doc: ContentDocument, platform: str) -> List[str]:
        """验证文档是否符合平台规则.

        Args:
            doc: ContentDocument 文档
            platform: 平台名称

        Returns:
            警告/错误消息列表
        """
        rules = self.load_rules(platform)
        warnings: List[str] = []

        # 标题长度
        if len(doc.title) > rules.title.max_length:
            warnings.append(
                f"标题长度({len(doc.title)})超过平台限制({rules.title.max_length})"
            )

        # 图片数量
        if rules.media and doc.get_image_count() > rules.media.max_images:
            warnings.append(
                f"图片数量({doc.get_image_count()})超过平台限制({rules.media.max_images})"
            )

        # 内容长度（按字符计）
        content_text = doc.to_plain_text()
        if rules.content.max_paragraph_length:
            for para in doc.body:
                if para.section_type == "paragraph":
                    for line in para.text.split("\n"):
                        if len(line) > rules.content.max_paragraph_length * 2:
                            warnings.append(
                                f"段落行长度({len(line)})建议不超过{rules.content.max_paragraph_length * 2}字符"
                            )

        return warnings

    def get_media_rules(self, platform: str) -> Optional[MediaRule]:
        """获取平台媒体规则.

        Args:
            platform: 平台名称

        Returns:
            MediaRule 实例，无媒体规则时返回 None
        """
        rules = self.load_rules(platform)
        return rules.media

    def clear_cache(self) -> None:
        """清除规则缓存."""
        self._rules_cache.clear()
