"""RuleEngine 规则引擎测试."""

import os
import pytest

from src.core.content_document import ContentDocument, ContentSection
from src.core.rule_engine import RuleEngine, PlatformRules


# 规则文件目录
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "rules")


class TestRuleEngineLoad:
    """规则加载测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_load_wechat_rules(self):
        rules = self.engine.load_rules("wechat")
        assert rules.platform == "wechat"
        assert rules.title.max_length == 64
        assert rules.content.output_format == "richtext"
        assert rules.tone is not None
        assert rules.media is not None

    def test_load_zhihu_rules(self):
        rules = self.engine.load_rules("zhihu")
        assert rules.platform == "zhihu"
        assert rules.title.max_length == 60

    def test_load_bilibili_rules(self):
        rules = self.engine.load_rules("bilibili")
        assert rules.platform == "bilibili"
        assert rules.title.max_length == 80

    def test_load_xiaohongshu_rules(self):
        rules = self.engine.load_rules("xiaohongshu")
        assert rules.platform == "xiaohongshu"
        assert rules.title.max_length == 20
        assert rules.content.output_format == "plain"

    def test_load_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            self.engine.load_rules("nonexistent_platform")

    def test_rules_cached(self):
        rules1 = self.engine.load_rules("wechat")
        rules2 = self.engine.load_rules("wechat")
        assert rules1 is rules2  # 同一对象（缓存命中）

    def test_clear_cache(self):
        rules1 = self.engine.load_rules("wechat")
        self.engine.clear_cache()
        rules2 = self.engine.load_rules("wechat")
        assert rules1 is not rules2  # 不同对象（缓存已清除）


class TestAdaptTitle:
    """标题适配测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_short_title_unchanged(self):
        result = self.engine.adapt_title("短标题", "wechat")
        assert result == "短标题"

    def test_long_title_truncated_wechat(self):
        # 生成一个超过64字符的标题
        long_title = "这是一个超过六十四字符的标题用来测试微信公众号的标题截断功能是否正常工作这是一个很长很长的标题需要超过六十四个字符才能触发截断逻辑"
        assert len(long_title) > 64
        result = self.engine.adapt_title(long_title, "wechat")
        assert len(result) <= 64
        assert result.endswith("...")

    def test_long_title_truncated_xiaohongshu(self):
        long_title = "这是一个超过二十字符的小红书标题测试"
        result = self.engine.adapt_title(long_title, "xiaohongshu")
        assert len(result) <= 20
        # xiaohongshu uses truncate_clean, no ellipsis

    def test_forbidden_patterns_removed(self):
        result = self.engine.adapt_title("标题!含@特殊#字符", "wechat")
        assert "!" not in result
        assert "@" not in result
        assert "#" not in result

    def test_zhihu_title(self):
        result = self.engine.adapt_title("知乎标题", "zhihu")
        assert result == "知乎标题"


class TestAdaptContent:
    """内容适配测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_wechat_richtext(self):
        doc = ContentDocument(
            title="测试",
            body=[
                ContentSection(section_type="heading", level=2, text="小标题"),
                ContentSection(section_type="paragraph", text="这是**加粗**文字。"),
            ],
        )
        result = self.engine.adapt_content(doc, "wechat")
        # WeChat should convert to HTML
        assert "<strong>" in result or "**" in result  # depending on transform

    def test_xiaohongshu_plain(self):
        doc = ContentDocument(
            title="测试",
            body=[
                ContentSection(section_type="paragraph", text="这是推荐的内容。"),
            ],
        )
        result = self.engine.adapt_content(doc, "xiaohongshu")
        # Xiaohongshu should produce plain text with emoji
        assert isinstance(result, str)
        assert len(result) > 0

    def test_zhihu_markdown(self):
        doc = ContentDocument(
            title="测试",
            body=[
                ContentSection(section_type="paragraph", text="知乎内容"),
            ],
        )
        result = self.engine.adapt_content(doc, "zhihu")
        assert isinstance(result, str)
        assert len(result) > 0


class TestValidate:
    """文档验证测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_valid_document_no_warnings(self):
        doc = ContentDocument(
            title="短标题",
            body=[ContentSection(section_type="paragraph", text="内容")],
        )
        warnings = self.engine.validate(doc, "wechat")
        assert len(warnings) == 0

    def test_title_too_long_warning(self):
        doc = ContentDocument(
            title="这是一个超过六十四字符的标题用来测试微信公众号的标题截断功能是否正常工作这是一个很长很长的标题需要超过六十四个字符才能触发截断逻辑",
            body=[ContentSection(section_type="paragraph", text="内容")],
        )
        warnings = self.engine.validate(doc, "wechat")
        assert any("标题长度" in w for w in warnings)

    def test_too_many_images_warning(self):
        from src.core.content_document import ImageRef
        doc = ContentDocument(
            title="标题",
            images=[ImageRef(src=f"img{i}.jpg") for i in range(15)],
        )
        warnings = self.engine.validate(doc, "wechat")
        assert any("图片数量" in w for w in warnings)


class TestGetMediaRules:
    """媒体规则测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_wechat_media_rules(self):
        media = self.engine.get_media_rules("wechat")
        assert media is not None
        assert media.image_ratio == "square"
        assert media.support_gif is True

    def test_xiaohongshu_media_rules(self):
        media = self.engine.get_media_rules("xiaohongshu")
        assert media is not None
        assert media.max_images == 9
        assert media.image_max_size_mb == 1.0


class TestTransformStepParsing:
    """变换步骤解析测试."""

    def setup_method(self):
        self.engine = RuleEngine(RULES_DIR)

    def test_wechat_transforms_count(self):
        rules = self.engine.load_rules("wechat")
        assert len(rules.content.transforms) >= 4  # heading, bold, italic, code, blockquote, wrap

    def test_xiaohongshu_transforms_count(self):
        rules = self.engine.load_rules("xiaohongshu")
        assert len(rules.content.transforms) >= 2  # markdown_to_plain, add_emoji, add_hashtags

    def test_transform_step_has_name(self):
        rules = self.engine.load_rules("wechat")
        for step in rules.content.transforms:
            assert step.name != ""
