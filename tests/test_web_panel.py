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
