from web.app import create_app


def test_platforms_endpoint_uses_registered_adapters(monkeypatch):
    for key in (
        "WECHAT_APP_ID",
        "WECHAT_APP_SECRET",
        "ZHIHU_USERNAME",
        "ZHIHU_PASSWORD",
        "BILIBILI_SESS_DATA",
        "BILIBILI_CSRF",
        "XIAOHONGSHU_COOKIE",
        "DOUYIN_COOKIE",
        "WEIBO_COOKIE",
    ):
        monkeypatch.delenv(key, raising=False)

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/api/platforms")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert {p["name"] for p in data["platforms"]} == {
        "wechat",
        "zhihu",
        "bilibili",
        "xiaohongshu",
        "douyin",
        "weibo",
    }


def test_preview_returns_platform_adaptations():
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/preview",
        json={
            "title": "x" * 80,
            "content": "# Title\n\n- item\n\n```python\nprint('hi')\n```",
            "tags": "AI,教程",
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "xiaohongshu" in data["previews"]
    assert len(data["previews"]["xiaohongshu"]["title"]) <= 30
    assert "content" in data["previews"]["wechat"]


def test_publish_defaults_to_simulate():
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/publish",
        json={
            "title": "Demo",
            "content": "Body",
            "platforms": ["wechat"],
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["results"]["wechat"]["success"] is True
    assert "[模拟发布]" in data["results"]["wechat"]["message"]


def test_rpa_status_endpoint_reports_prelogin_profiles(monkeypatch, tmp_path):
    monkeypatch.setenv("MULTI_PUBLISHER_RPA_PROFILE_DIR", str(tmp_path / "profiles"))

    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/api/rpa/status")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert {p["name"] for p in data["platforms"]} == {
        "zhihu",
        "bilibili",
        "xiaohongshu",
        "douyin",
        "weibo",
    }
    assert all(str(tmp_path / "profiles") in p["profile_path"] for p in data["platforms"])


def test_rpa_login_rejects_unknown_platform():
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post("/api/rpa/login", json={"platform": "unknown"})
    data = response.get_json()

    assert response.status_code == 400
    assert data["success"] is False


# ──────────────────── 定时发布 API 测试 ────────────────────

def test_schedule_publish_creates_scheduled_tasks():
    """测试 POST /api/schedule 创建定时任务."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/schedule",
        json={
            "title": "定时文章",
            "content": "正文内容",
            "tags": "标签1,标签2",
            "platforms": ["wechat", "zhihu"],
            "delay_seconds": 3600,
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "wechat" in data["results"]
    assert "zhihu" in data["results"]
    for platform in ["wechat", "zhihu"]:
        assert "task_id" in data["results"][platform]
        assert "scheduled_at" in data["results"][platform]


def test_schedule_publish_with_iso_time():
    """测试使用 ISO 格式时间创建定时任务."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/schedule",
        json={
            "title": "未来文章",
            "content": "正文",
            "platforms": ["wechat"],
            "scheduled_at": "2027-01-01T00:00:00",
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["results"]["wechat"]["task_id"]


def test_schedule_publish_requires_title_or_content():
    """测试创建定时任务需要标题和内容."""
    app = create_app()
    app.config["TESTING"] = True

    # 缺少标题和内容
    response = app.test_client().post(
        "/api/schedule",
        json={"title": "", "content": "", "platforms": ["wechat"], "delay_seconds": 60},
    )
    data = response.get_json()
    assert response.status_code == 400
    assert data["success"] is False

    # 缺少平台
    response = app.test_client().post(
        "/api/schedule",
        json={"title": "T", "content": "C", "platforms": [], "delay_seconds": 60},
    )
    assert response.status_code == 400


def test_schedule_publish_requires_time():
    """测试创建定时任务需要指定时间."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/schedule",
        json={"title": "T", "content": "C", "platforms": ["wechat"]},
    )
    data = response.get_json()
    assert response.status_code == 400
    assert data["success"] is False


def test_list_scheduled_tasks():
    """测试 GET /api/schedule 列出定时任务."""
    app = create_app()
    app.config["TESTING"] = True

    # 先创建一个定时任务
    app.test_client().post(
        "/api/schedule",
        json={
            "title": "列出测试",
            "content": "内容",
            "platforms": ["wechat"],
            "delay_seconds": 99999,
        },
    )

    # 列出
    response = app.test_client().get("/api/schedule")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert len(data["tasks"]) >= 1
    task = data["tasks"][0]
    assert task["status"] == "scheduled"
    assert task["scheduled_at"] is not None


def test_cancel_scheduled_task():
    """测试 DELETE /api/schedule/<id> 取消定时任务."""
    app = create_app()
    app.config["TESTING"] = True

    # 创建
    resp = app.test_client().post(
        "/api/schedule",
        json={
            "title": "取消测试",
            "content": "内容",
            "platforms": ["wechat"],
            "delay_seconds": 99999,
        },
    )
    data = resp.get_json()
    task_id = data["results"]["wechat"]["task_id"]

    # 取消
    response = app.test_client().delete(f"/api/schedule/{task_id}")
    data = response.get_json()
    assert response.status_code == 200
    assert data["success"] is True


def test_cancel_nonexistent_task():
    """测试取消不存在的任务."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().delete("/api/schedule/nonexistent-id")
    data = response.get_json()
    assert data["success"] is False


def test_scheduler_status_endpoint():
    """测试 GET /api/scheduler/status 返回调度器状态."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().get("/api/scheduler/status")
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "status" in data
    assert "running" in data["status"]
    assert "scheduled_count" in data["status"]


def test_schedule_with_delay():
    """测试使用 delay_seconds 参数."""
    app = create_app()
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/schedule",
        json={
            "title": "延迟发布",
            "content": "正文内容测试",
            "platforms": ["wechat"],
            "delay_seconds": 1800,  # 30分钟
        },
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    result = data["results"]["wechat"]
    assert result["task_id"]
    # 验证 scheduled_at 时间在合理范围（约30分钟后）
    from datetime import datetime, timedelta
    scheduled = datetime.fromisoformat(result["scheduled_at"].replace("Z", "+00:00"))
    now = datetime.now()
    expected = now + timedelta(seconds=1800)
    diff = abs((scheduled - expected).total_seconds())
    assert diff < 5, f"时间偏差过大: {diff}秒"
