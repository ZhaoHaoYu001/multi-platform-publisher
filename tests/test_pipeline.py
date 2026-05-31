"""发布管线和任务队列测试."""

import pytest
from unittest.mock import MagicMock

from src.core.content_document import ContentDocument, ContentSection
from src.core.platform_base import PublishMode, PublishResult
from src.core.rule_engine import RuleEngine
from src.core.task_queue import TaskQueue, PublishTask
from src.adapters.wechat_adapter import WechatAdapter
from src.pipeline.publish_pipeline import (
    PipelineContext,
    ParseStage,
    AdaptStage,
    DeliverStage,
    PublishPipeline,
)


import os
RULES_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "rules")


class TestPipelineContext:
    """PipelineContext 测试."""

    def test_create_default(self):
        ctx = PipelineContext()
        assert ctx.platform == ""
        assert ctx.adapted is None
        assert ctx.processed_images == []
        assert ctx.errors == []

    def test_with_metadata(self):
        ctx = PipelineContext(platform="wechat", metadata={"title": "t"})
        assert ctx.platform == "wechat"
        assert ctx.metadata["title"] == "t"


class TestParseStage:
    """ParseStage 测试."""

    def test_parse_markdown(self):
        stage = ParseStage(title="标题")
        ctx = PipelineContext(metadata={"raw_content": "# H1\n\n正文内容"})
        result = stage.execute(ctx)
        assert result.document.title == "标题"
        assert len(result.document.body) >= 1


class TestAdaptStage:
    """AdaptStage 测试."""

    def test_adapt_content(self):
        engine = RuleEngine(RULES_DIR)
        adapter = WechatAdapter(engine, {})
        stage = AdaptStage(adapter)

        doc = ContentDocument(
            title="标题",
            body=[ContentSection(section_type="paragraph", text="正文")],
        )
        ctx = PipelineContext(document=doc, platform="wechat")
        result = stage.execute(ctx)
        assert result.adapted is not None
        assert result.adapted.title == "标题"
        assert len(result.adapted.content) > 0


class TestDeliverStage:
    """DeliverStage 测试."""

    def test_deliver_simulate(self):
        engine = RuleEngine(RULES_DIR)
        adapter = WechatAdapter(engine, {})
        stage = DeliverStage(adapter)

        doc = ContentDocument(
            title="标题",
            body=[ContentSection(section_type="paragraph", text="正文")],
        )
        from src.adapters.base_adapter import AdaptationResult
        ctx = PipelineContext(
            document=doc,
            platform="wechat",
            adapted=AdaptationResult(title="标题", content="正文"),
            metadata={"mode": PublishMode.SIMULATE},
        )
        result = stage.execute(ctx)
        assert result.result is not None
        assert result.result.success is True

    def test_deliver_no_adapted_returns_error(self):
        engine = RuleEngine(RULES_DIR)
        adapter = WechatAdapter(engine, {})
        stage = DeliverStage(adapter)

        ctx = PipelineContext(platform="wechat")
        result = stage.execute(ctx)
        assert len(result.errors) > 0


class TestPublishPipeline:
    """PublishPipeline 测试."""

    def test_create_default(self):
        engine = RuleEngine(RULES_DIR)
        adapter = WechatAdapter(engine, {})
        pipeline = PublishPipeline.create_default(adapter, title="标题")
        assert len(pipeline._stages) == 5

    def test_execute_simulate(self):
        engine = RuleEngine(RULES_DIR)
        adapter = WechatAdapter(engine, {})
        pipeline = PublishPipeline.create_default(adapter, title="标题")

        ctx = PipelineContext(
            metadata={
                "raw_content": "# 标题\n\n正文内容",
                "title": "标题",
                "mode": PublishMode.SIMULATE,
            }
        )
        result = pipeline.execute(ctx)
        assert result.result is not None
        assert result.result.success is True


class TestTaskQueue:
    """TaskQueue 测试."""

    def test_enqueue(self):
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="标题")
        assert len(task_id) > 0

    def test_get_status(self):
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="标题")
        task = queue.get_status(task_id)
        assert task is not None
        assert task.platform == "wechat"
        assert task.status == "pending"

    def test_get_nonexistent(self):
        queue = TaskQueue()
        task = queue.get_status("nonexistent")
        assert task is None

    def test_update_status(self):
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="标题")
        queue.update_status(task_id, "success")
        task = queue.get_status(task_id)
        assert task.status == "success"

    def test_update_with_result(self):
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="标题")
        result = PublishResult(success=True, platform="wechat", message="ok")
        queue.update_status(task_id, "success", result=result)
        task = queue.get_status(task_id)
        assert task.result is not None
        assert task.result.success is True

    def test_list_all(self):
        queue = TaskQueue()
        queue.enqueue(platform="wechat", title="t1")
        queue.enqueue(platform="zhihu", title="t2")
        tasks = queue.list_tasks()
        assert len(tasks) == 2

    def test_list_by_status(self):
        queue = TaskQueue()
        t1 = queue.enqueue(platform="wechat", title="t1")
        t2 = queue.enqueue(platform="zhihu", title="t2")
        queue.update_status(t1, "success")

        success_tasks = queue.list_tasks(status="success")
        assert len(success_tasks) == 1
        assert success_tasks[0].id == t1

        pending_tasks = queue.list_tasks(status="pending")
        assert len(pending_tasks) == 1
        assert pending_tasks[0].id == t2

    def test_task_count(self):
        queue = TaskQueue()
        assert queue.get_task_count() == 0
        queue.enqueue(platform="wechat", title="t1")
        assert queue.get_task_count() == 1

    def test_clear(self):
        queue = TaskQueue()
        queue.enqueue(platform="wechat", title="t1")
        queue.clear()
        assert queue.get_task_count() == 0
