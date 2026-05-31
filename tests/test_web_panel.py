from web.app import app


def test_platforms_include_all_demo_targets(monkeypatch):
    for key in (
        "WECHAT_APP_ID",
        "WECHAT_APP_SECRET",
        "ZHIHU_USERNAME",
        "ZHIHU_PASSWORD",
        "BILIBILI_SESS_DATA",
        "BILIBILI_CSRF",
        "XIAOHONGSHU_COOKIE",
    ):
        monkeypatch.delenv(key, raising=False)

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
    }
    assert all(p["has_credentials"] is False for p in data["platforms"])


def test_preview_returns_platform_adaptation():
    app.config["TESTING"] = True
    response = app.test_client().post(
        "/api/preview",
        json={
            "title": "x" * 80,
            "content": "# Title\n\n- item\n\n```python\nprint('hi')\n```",
            "platforms": ["xiaohongshu"],
        },
    )
    data = response.get_json()
    preview = data["previews"]["xiaohongshu"]

    assert response.status_code == 200
    assert data["success"] is True
    assert len(preview["title"]) <= 20
    assert preview["content_type"] == "plain"
    assert "#" in preview["content"]


def test_publish_defaults_to_simulate():
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
    assert data["mode"] == "simulate"
    assert data["results"]["wechat"]["success"] is True
    assert data["results"]["wechat"]["raw_response"]["content_type"] == "richtext"
