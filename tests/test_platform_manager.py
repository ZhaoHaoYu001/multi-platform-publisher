"""平台管理器测试模块."""

import pytest

from src.core.platform_base import PlatformBase, PublishMode, PublishResult
from src.core.platform_manager import PlatformManager


class MockPlatformA(PlatformBase):
    """模拟平台A."""

    name = "platform_a"
    max_title_length = 50

    def _do_publish(self, title, content, images, **kwargs):
        return PublishResult(
            success=True,
            platform=self.name,
            message="平台A发布成功",
        )


class MockPlatformB(PlatformBase):
    """模拟平台B."""

    name = "platform_b"
    max_title_length = 100

    def _do_publish(self, title, content, images, **kwargs):
        return PublishResult(
            success=True,
            platform=self.name,
            message="平台B发布成功",
        )


class MockFailPlatform(PlatformBase):
    """总是失败的模拟平台."""

    name = "fail_platform"

    def _do_publish(self, title, content, images, **kwargs):
        raise Exception("模拟发布失败")


class TestPlatformManager:
    """平台管理器测试."""

    def setup_method(self):
        """测试前准备."""
        self.manager = PlatformManager()
        self.platform_a = MockPlatformA()
        self.platform_b = MockPlatformB()

    def test_initial_state(self):
        """测试初始状态."""
        assert self.manager.count == 0
        assert self.manager.platforms == []

    def test_register_platform(self):
        """测试注册平台."""
        self.manager.register(self.platform_a)
        assert self.manager.count == 1
        assert "platform_a" in self.manager.platforms

    def test_register_multiple_platforms(self):
        """测试注册多个平台."""
        self.manager.register(self.platform_a)
        self.manager.register(self.platform_b)
        assert self.manager.count == 2
        assert set(self.manager.platforms) == {"platform_a", "platform_b"}

    def test_register_duplicate_platform(self):
        """测试注册重复平台."""
        self.manager.register(self.platform_a)
        with pytest.raises(ValueError, match="已注册"):
            self.manager.register(MockPlatformA())

    def test_register_invalid_type(self):
        """测试注册无效类型."""
        with pytest.raises(TypeError, match="PlatformBase"):
            self.manager.register("not a platform")

    def test_unregister_platform(self):
        """测试注销平台."""
        self.manager.register(self.platform_a)
        self.manager.unregister("platform_a")
        assert self.manager.count == 0

    def test_unregister_nonexistent(self):
        """测试注销不存在的平台."""
        with pytest.raises(KeyError, match="未注册"):
            self.manager.unregister("nonexistent")

    def test_get_platform(self):
        """测试获取平台."""
        self.manager.register(self.platform_a)
        platform = self.manager.get_platform("platform_a")
        assert platform is self.platform_a

    def test_get_nonexistent_platform(self):
        """测试获取不存在的平台."""
        platform = self.manager.get_platform("nonexistent")
        assert platform is None

    def test_has_platform(self):
        """测试检查平台是否存在."""
        self.manager.register(self.platform_a)
        assert self.manager.has_platform("platform_a") is True
        assert self.manager.has_platform("platform_b") is False

    def test_contains_operator(self):
        """测试 in 操作符."""
        self.manager.register(self.platform_a)
        assert "platform_a" in self.manager
        assert "platform_b" not in self.manager

    def test_len_operator(self):
        """测试 len 操作符."""
        assert len(self.manager) == 0
        self.manager.register(self.platform_a)
        assert len(self.manager) == 1


class TestPublishMethods:
    """发布方法测试."""

    def setup_method(self):
        """测试前准备."""
        self.manager = PlatformManager()
        self.manager.register(MockPlatformA())
        self.manager.register(MockPlatformB())

    def test_publish_to_platform(self):
        """测试发布到指定平台."""
        result = self.manager.publish_to_platform(
            platform_name="platform_a",
            title="测试标题",
            content="测试内容",
            mode=PublishMode.REAL,
        )
        assert result.success is True
        assert result.platform == "platform_a"

    def test_publish_to_nonexistent_platform(self):
        """测试发布到不存在的平台."""
        result = self.manager.publish_to_platform(
            platform_name="nonexistent",
            title="测试",
            content="内容",
        )
        assert result.success is False
        assert "未注册" in result.message

    def test_publish_to_all(self):
        """测试发布到所有平台."""
        results = self.manager.publish_to_all(
            title="测试标题",
            content="测试内容",
            mode=PublishMode.REAL,
        )
        assert len(results) == 2
        assert results["platform_a"].success is True
        assert results["platform_b"].success is True

    def test_publish_to_selected(self):
        """测试发布到指定多个平台."""
        results = self.manager.publish_to_selected(
            platforms=["platform_a"],
            title="测试",
            content="内容",
            mode=PublishMode.REAL,
        )
        assert len(results) == 1
        assert "platform_a" in results

    def test_publish_to_selected_with_invalid(self):
        """测试发布到包含无效平台的列表."""
        results = self.manager.publish_to_selected(
            platforms=["platform_a", "nonexistent"],
            title="测试",
            content="内容",
        )
        assert len(results) == 2
        assert results["platform_a"].success is True
        assert results["nonexistent"].success is False

    def test_simulate_mode(self):
        """测试模拟模式发布."""
        result = self.manager.publish_to_platform(
            platform_name="platform_a",
            title="测试",
            content="内容",
            mode=PublishMode.SIMULATE,
        )
        assert result.success is True
        assert "模拟发布" in result.message

    def test_get_summary(self):
        """测试获取摘要."""
        results = self.manager.publish_to_all(
            title="测试",
            content="内容",
            mode=PublishMode.REAL,
        )
        summary = self.manager.get_summary(results)
        assert "2/2 成功" in summary

    def test_get_summary_with_failure(self):
        """测试包含失败的摘要."""
        self.manager.register(MockFailPlatform())
        results = self.manager.publish_to_all(
            title="测试",
            content="内容",
            mode=PublishMode.REAL,
        )
        summary = self.manager.get_summary(results)
        assert "2/3 成功" in summary
        assert "失败平台: 1 个" in summary
