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

    # ── 定时任务测试 ──

    def test_schedule_at(self):
        """测试 schedule_at 创建定时任务."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        future = datetime.now() + timedelta(hours=1)
        task_id = queue.schedule_at(
            platform="wechat",
            title="定时文章",
            scheduled_at=future,
            content="正文内容",
        )
        task = queue.get_status(task_id)
        assert task is not None
        assert task.status == "scheduled"
        assert task.scheduled_at == future
        assert task.is_scheduled is True
        assert task.metadata["content"] == "正文内容"

    def test_schedule_delay(self):
        """测试 schedule_delay 按延迟创建定时任务."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        task_id = queue.schedule_delay(
            platform="zhihu",
            title="延迟文章",
            delay_seconds=1800,
            content="延迟发布内容",
        )
        task = queue.get_status(task_id)
        assert task is not None
        assert task.status == "scheduled"
        # 验证时间约在30分钟后
        expected = datetime.now() + timedelta(seconds=1800)
        diff = abs((task.scheduled_at - expected).total_seconds()) if task.scheduled_at else 999
        assert diff < 5, f"时间偏差过大: {diff}秒"

    def test_is_due(self):
        """测试任务到期判断."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        # 过去的时间 → 已到期
        past = datetime.now() - timedelta(minutes=10)
        task_id = queue.schedule_at(
            platform="wechat",
            title="已到期",
            scheduled_at=past,
        )
        task = queue.get_status(task_id)
        assert task.is_due is True
        # 未来的时间 → 未到期
        future = datetime.now() + timedelta(hours=2)
        task_id2 = queue.schedule_at(
            platform="zhihu",
            title="未到期",
            scheduled_at=future,
        )
        task2 = queue.get_status(task_id2)
        assert task2.is_due is False

    def test_list_due_tasks(self):
        """测试列出到期任务."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        # 过去
        queue.schedule_at(platform="wechat", title="到期", scheduled_at=datetime.now() - timedelta(minutes=5))
        # 未来
        queue.schedule_at(platform="zhihu", title="未到期", scheduled_at=datetime.now() + timedelta(hours=5))
        due = queue.list_due_tasks()
        assert len(due) == 1
        assert due[0].platform == "wechat"

    def test_list_scheduled_tasks(self):
        """测试列出所有定时任务."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        queue.schedule_at(platform="wechat", title="t1", scheduled_at=datetime.now() + timedelta(hours=2))
        queue.schedule_at(platform="zhihu", title="t2", scheduled_at=datetime.now() + timedelta(hours=1))
        scheduled = queue.list_scheduled_tasks()
        assert len(scheduled) == 2
        # 按时间排序，最早的在前
        assert scheduled[0].platform == "zhihu"

    def test_cancel_scheduled_task(self):
        """测试取消定时任务."""
        from datetime import datetime, timedelta
        queue = TaskQueue()
        task_id = queue.schedule_at(
            platform="wechat",
            title="取消",
            scheduled_at=datetime.now() + timedelta(hours=1),
        )
        assert queue.cancel_task(task_id) is True
        task = queue.get_status(task_id)
        assert task.status == "failed"
        assert "取消" in task.error

    def test_cancel_non_scheduled_task(self):
        """测试取消非定时任务返回 False."""
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="普通任务")
        queue.update_status(task_id, "success")
        assert queue.cancel_task(task_id) is False


class TestScheduler:
    """Scheduler 定时调度器测试."""

    def test_scheduler_start_stop(self):
        """测试调度器启停."""
        from src.core.scheduler import Scheduler
        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=0.5)
        assert scheduler.is_running is False
        scheduler.start()
        assert scheduler.is_running is True
        scheduler.stop()
        assert scheduler.is_running is False

    def test_scheduler_executes_due_task(self):
        """测试调度器执行到期任务."""
        import time
        from datetime import datetime, timedelta
        from src.core.scheduler import Scheduler

        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=0.3)

        # 创建已到期的定时任务
        task_id = queue.schedule_at(
            platform="wechat",
            title="到期执行",
            scheduled_at=datetime.now() - timedelta(seconds=1),
        )

        executed_tasks = []
        scheduler.on_execute(lambda t: executed_tasks.append(t.id))
        scheduler.start()

        # 等待调度器执行
        deadline = time.time() + 3
        while not executed_tasks and time.time() < deadline:
            time.sleep(0.1)

        scheduler.stop()

        assert task_id in executed_tasks, f"任务未被执行，已执行: {executed_tasks}"

    def test_scheduler_updates_status_on_execute(self):
        """测试调度器执行时更新任务状态."""
        import time
        from datetime import datetime, timedelta
        from src.core.scheduler import Scheduler

        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=0.3)

        task_id = queue.schedule_at(
            platform="wechat",
            title="状态更新测试",
            scheduled_at=datetime.now() - timedelta(seconds=1),
        )

        def mock_publish(task):
            queue.update_status(task.id, "success")

        scheduler.on_execute(mock_publish)
        scheduler.start()

        deadline = time.time() + 3
        task = queue.get_status(task_id)
        while task and task.status != "success" and time.time() < deadline:
            time.sleep(0.1)
            task = queue.get_status(task_id)

        scheduler.stop()

        assert task is not None
        assert task.status == "success", f"任务状态应为 success，实际为 {task.status}"

    def test_scheduler_get_status(self):
        """测试获取调度器状态."""
        from datetime import datetime, timedelta
        from src.core.scheduler import Scheduler

        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=5.0)
        queue.schedule_at(
            platform="wechat",
            title="状态测试",
            scheduled_at=datetime.now() + timedelta(hours=1),
        )

        status = scheduler.get_status()
        assert status["running"] is False
        assert status["scheduled_count"] == 1
        assert status["check_interval"] == 5.0
        assert status["next_task"] is not None
        assert status["next_task"]["platform"] == "wechat"

    def test_scheduler_handles_callback_error(self):
        """测试调度器优雅处理回调异常."""
        import time
        from datetime import datetime, timedelta
        from src.core.scheduler import Scheduler

        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=0.3)

        task_id = queue.schedule_at(
            platform="wechat",
            title="异常测试",
            scheduled_at=datetime.now() - timedelta(seconds=1),
        )

        def failing_callback(task):
            raise RuntimeError("模拟发布失败")

        executed = []
        def success_callback(task):
            executed.append(task.id)
            queue.update_status(task.id, "success")

        scheduler.on_execute(failing_callback)
        scheduler.on_execute(success_callback)
        scheduler.start()

        deadline = time.time() + 3
        while not executed and time.time() < deadline:
            time.sleep(0.1)

        scheduler.stop()

        task = queue.get_status(task_id)
        assert task.status == "success", f"fallback 回调应成功，实际: {task.status}"

    def test_scheduler_no_duplicate_start(self):
        """测试重复启动调度器不报错."""
        from src.core.scheduler import Scheduler
        queue = TaskQueue()
        scheduler = Scheduler(queue, check_interval=1.0)
        scheduler.start()
        scheduler.start()  # 不应报错
        assert scheduler.is_running is True
        scheduler.stop()
