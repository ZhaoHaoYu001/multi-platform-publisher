"""任务调度器.

提供定时任务的调度和执行功能。
基于 threading 实现轻量级后台调度。
"""

import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .task_queue import TaskQueue


class Scheduler:
    """任务调度器.

    使用示例:
        queue = TaskQueue()
        scheduler = Scheduler(queue)

        # 注册执行回调
        scheduler.on_execute(lambda task: print(f"执行任务: {task.id}"))

        # 启动调度器
        scheduler.start()

        # 添加定时任务
        queue.schedule_at("wechat", "标题", datetime(2026, 6, 1, 10, 0))

        # 停止调度器
        scheduler.stop()
    """

    def __init__(
        self,
        task_queue: TaskQueue,
        check_interval: float = 10.0,
    ) -> None:
        """初始化调度器.

        Args:
            task_queue: 任务队列
            check_interval: 检查间隔（秒）
        """
        self._queue = task_queue
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable] = []
        self._lock = threading.Lock()

    def on_execute(self, callback: Callable) -> None:
        """注册任务执行回调.

        Args:
            callback: 回调函数，接收 PublishTask 参数
        """
        self._callbacks.append(callback)

    def start(self) -> None:
        """启动调度器."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """停止调度器."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._check_interval + 1)
            self._thread = None

    @property
    def is_running(self) -> bool:
        """调度器是否运行中."""
        return self._running

    def _run(self) -> None:
        """调度器主循环."""
        while self._running:
            try:
                self._check_and_execute()
            except Exception:
                pass  # 忽略异常，继续运行
            time.sleep(self._check_interval)

    def _check_and_execute(self) -> None:
        """检查并执行到期任务."""
        due_tasks = self._queue.list_due_tasks()

        for task in due_tasks:
            with self._lock:
                # 更新状态为发布中
                self._queue.update_status(task.id, "publishing")

            # 执行回调
            success = False
            for callback in self._callbacks:
                try:
                    callback(task)
                    success = True
                    break
                except Exception as e:
                    self._queue.update_status(task.id, "failed", error=str(e))

    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态.

        Returns:
            状态信息
        """
        scheduled = self._queue.list_scheduled_tasks()
        return {
            "running": self._running,
            "check_interval": self._check_interval,
            "scheduled_count": len(scheduled),
            "next_task": {
                "id": scheduled[0].id,
                "platform": scheduled[0].platform,
                "title": scheduled[0].title,
                "scheduled_at": scheduled[0].scheduled_at.isoformat() if scheduled[0].scheduled_at else None,
            } if scheduled else None,
        }
