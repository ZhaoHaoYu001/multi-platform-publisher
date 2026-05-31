"""发布任务队列.

提供发布任务的状态追踪和管理功能。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .platform_base import PublishMode, PublishResult


@dataclass
class PublishTask:
    """发布任务.

    Attributes:
        id: 任务唯一ID
        platform: 目标平台
        title: 文章标题
        status: 任务状态 (pending/publishing/success/failed)
        result: 发布结果
        created_at: 创建时间
        updated_at: 更新时间
        error: 错误信息
    """

    id: str = ""
    platform: str = ""
    title: str = ""
    status: str = "pending"  # pending, publishing, success, failed
    result: Optional[PublishResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    error: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class TaskQueue:
    """发布任务队列.

    使用示例:
        queue = TaskQueue()
        task_id = queue.enqueue(platform="wechat", title="文章标题")
        task = queue.get_status(task_id)
        queue.update_status(task_id, "success", result=...)
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, PublishTask] = {}

    def enqueue(self, platform: str, title: str = "") -> str:
        """添加发布任务到队列.

        Args:
            platform: 目标平台
            title: 文章标题

        Returns:
            任务ID
        """
        task = PublishTask(platform=platform, title=title)
        self._tasks[task.id] = task
        return task.id

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

    def get_task_count(self) -> int:
        """获取任务总数."""
        return len(self._tasks)

    def clear(self) -> None:
        """清空所有任务."""
        self._tasks.clear()
