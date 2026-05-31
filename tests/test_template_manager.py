"""内容模板管理器测试."""
import pytest
from src.core.template_manager import ContentTemplate, TemplateManager


class TestTemplateManager:
    """TemplateManager 测试."""

    def setup_method(self):
        self.manager = TemplateManager()

    def test_list_templates(self):
        templates = self.manager.list_templates()
        assert len(templates) >= 4  # 至少4个内置模板

    def test_builtin_templates(self):
        templates = self.manager.list_templates()
        ids = [t.id for t in templates]
        assert "tech-tutorial" in ids
        assert "product-review" in ids
        assert "daily-share" in ids
        assert "industry-analysis" in ids

    def test_get_template(self):
        tpl = self.manager.get_template("tech-tutorial")
        assert tpl is not None
        assert tpl.name == "技术教程"
        assert tpl.category == "技术"
        assert len(tpl.variables) > 0

    def test_get_template_not_found(self):
        tpl = self.manager.get_template("nonexistent")
        assert tpl is None

    def test_apply_template(self):
        title, content = self.manager.apply_template("tech-tutorial", {
            "title": "Python入门",
            "topic": "基础语法",
            "package": "requests",
            "code_example": "import requests",
            "advanced_content": "高级内容",
            "summary": "总结",
            "tags": "Python,教程",
        })
        assert "Python入门" in title
        assert "基础语法" in content
        assert "requests" in content

    def test_apply_template_not_found(self):
        with pytest.raises(ValueError, match="模板不存在"):
            self.manager.apply_template("nonexistent", {})

    def test_list_categories(self):
        categories = self.manager.list_categories()
        assert "技术" in categories
        assert "评测" in categories
        assert "生活" in categories
        assert "行业" in categories

    def test_search_templates(self):
        results = self.manager.search_templates("教程")
        assert len(results) > 0
        assert any("教程" in t.name for t in results)

    def test_search_templates_no_match(self):
        results = self.manager.search_templates("xyznonexistent")
        assert len(results) == 0

    def test_add_template(self):
        tpl = ContentTemplate(
            id="custom",
            name="自定义模板",
            description="测试模板",
            title_template="自定义: {{title}}",
            content_template="内容: {{content}}",
            variables=["title", "content"],
        )
        self.manager.add_template(tpl)
        assert self.manager.get_template("custom") is not None

    def test_remove_template(self):
        tpl = ContentTemplate(id="to-remove", name="待删除")
        self.manager.add_template(tpl)
        assert self.manager.remove_template("to-remove") is True
        assert self.manager.get_template("to-remove") is None

    def test_remove_template_not_found(self):
        assert self.manager.remove_template("nonexistent") is False

    def test_template_properties(self):
        tpl = self.manager.get_template("product-review")
        assert tpl is not None
        assert "product" in tpl.variables
        assert "verdict" in tpl.variables
        assert "评测" in tpl.tags
