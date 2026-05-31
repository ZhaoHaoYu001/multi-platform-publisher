"""发布任务队列.

提供发布任务的状态追踪和管理功能，支持定时发布。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .platform_base import PublishMode, PublishResult


@dataclass
class PublishTask:
    """发布任务.

    Attributes:
        id: 任务唯一ID
        platform: 目标平台
        title: 文章标题
        status: 任务状态 (pending/publishing/success/failed/scheduled)
        result: 发布结果
        created_at: 创建时间
        updated_at: 更新时间
        scheduled_at: 计划执行时间
        error: 错误信息
        metadata: 额外元数据
    """

    id: str = ""
    platform: str = ""
    title: str = ""
    status: str = "pending"  # pending, publishing, success, failed, scheduled
    result: Optional[PublishResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

    @property
    def is_scheduled(self) -> bool:
        """是否为定时任务."""
        return self.scheduled_at is not None

    @property
    def is_due(self) -> bool:
        """定时任务是否到期."""
        if not self.scheduled_at:
            return False
        return datetime.now() >= self.scheduled_at


class TaskQueue:
    """发布任务队列.

    使用示例:
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="文章标题")
        task = queue.get_status(task_id)
        queue.update_status(task_id, "success", result=...)

        # 定时发布
        scheduled_id = queue.schedule_at(
            platform="wechat",
            title="定时文章",
            scheduled_at=datetime(2026, 6, 1, 10, 0),
        )
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, PublishTask] = {}

    def enqueue(self, platform: str, title: str = "", **kwargs: Any) -> str:
        """添加发布任务到队列.

        Args:
            platform: 目标平台
            title: 文章标题
            **kwargs: 额外元数据

        Returns:
            任务ID
        """
        task = PublishTask(
            platform=platform,
            title=title,
            metadata=kwargs,
        )
        self._tasks[task.id] = task
        return task.id

    def schedule_at(
        self,
        platform: str,
        title: str,
        scheduled_at: datetime,
        content: str = "",
        images: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """添加定时发布任务.

        Args:
            platform: 目标平台
            title: 文章标题
            scheduled_at: 计划执行时间
            content: 文章内容
            images: 图片列表
            **kwargs: 额外元数据

        Returns:
            任务ID
        """
        task = PublishTask(
            platform=platform,
            title=title,
            status="scheduled",
            scheduled_at=scheduled_at,
            metadata={
                "content": content,
                "images": images or [],
                **kwargs,
            },
        )
        self._tasks[task.id] = task
        return task.id

    def schedule_delay(
        self,
        platform: str,
        title: str,
        delay_seconds: int,
        content: str = "",
        images: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> str:
        """添加延迟发布任务.

        Args:
            platform: 目标平台
            title: 文章标题
            delay_seconds: 延迟秒数
            content: 文章内容
            images: 图片列表
            **kwargs: 额外元数据

        Returns:
            任务ID
        """
        scheduled_at = datetime.now() + timedelta(seconds=delay_seconds)
        return self.schedule_at(
            platform=platform,
            title=title,
            scheduled_at=scheduled_at,
            content=content,
            images=images,
            **kwargs,
        )

    def get_status(self, task_id: str) -> Optional[PublishTask]:
        """获取任务状态.

        Args:
            task_id: 任务ID

        Returns:
            PublishTask 实例，不存在时返回 None
        """
        return self._tasks.get(task_id)

    def update_status(
        self,
        task_id: str,
        status: str,
        result: Optional[PublishResult] = None,
        error: str = "",
    ) -> bool:
        """更新任务状态.

        Args:
            task_id: 任务ID
            status: 新状态
            result: 发布结果
            error: 错误信息

        Returns:
            是否更新成功
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False

        task.status = status
        task.updated_at = datetime.now()
        if result:
            task.result = result
        if error:
            task.error = error
        return True

    def list_tasks(self, status: Optional[str] = None) -> List[PublishTask]:
        """列出任务.

        Args:
            status: 按状态过滤（None 表示全部）

        Returns:
            任务列表
        """
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def list_due_tasks(self) -> List[PublishTask]:
        """列出到期的定时任务.

        Returns:
            到期任务列表
        """
        return [t for t in self._tasks.values() if t.status == "scheduled" and t.is_due]

    def list_scheduled_tasks(self) -> List[PublishTask]:
        """列出所有定时任务.

        Returns:
            定时任务列表
        """
        return sorted(
            [t for t in self._tasks.values() if t.status == "scheduled"],
            key=lambda t: t.scheduled_at or datetime.max,
        )

    def cancel_task(self, task_id: str) -> bool:
        """取消任务.

        Args:
            task_id: 任务ID

        Returns:
            是否取消成功
        """
        task = self._tasks.get(task_id)
        if task is None:
            return False

        if task.status in ("pending", "scheduled"):
            task.status = "failed"
            task.error = "用户取消"
            task.updated_at = datetime.now()
            return True
        return False

    def get_task_count(self) -> int:
        """获取任务总数."""
        return len(self._tasks)

    def clear(self) -> None:
        """清空所有任务."""
        self._tasks.clear()
