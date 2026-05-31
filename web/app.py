"""Flask web panel for composing, adapting, and publishing content."""

import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, render_template, request

from src.core.platform_base import PublishMode, PublishResult
from src.core.platform_catalog import (
    PLATFORM_CATALOG,
    build_platform_manager,
    get_platform_catalog,
    is_credentials_ready,
)
from src.draft.draft_manager import DraftManager

app = Flask(__name__)

draft_manager = DraftManager(
    drafts_dir=os.path.join(os.path.dirname(__file__), "..", "drafts")
)


def get_platform_manager():
    """Create a manager with every supported platform registered."""

    return build_platform_manager()


def _payload() -> Dict:
    return request.get_json(silent=True) or {}


def _parse_tags(value) -> List[str]:
    if isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return [tag.strip() for tag in str(value or "").split(",") if tag.strip()]


def _selected_platforms(data: Dict, manager) -> List[str]:
    requested = data.get("platforms") or manager.platforms
    return [name for name in requested if name in PLATFORM_CATALOG]


def _adapt_preview(platform, title: str, content: str, images: List[str]) -> Dict:
    adapted_title = platform.adapt_title(title)
    adapted_content = platform.adapt_content(content)
    warnings = []

    if adapted_title != title:
        warnings.append(
            f"标题已按 {platform.max_title_length} 字限制自动截断。"
        )
    if adapted_content != content and len(content) > platform.max_content_length:
        warnings.append(
            f"正文已按 {platform.max_content_length} 字限制自动截断。"
        )

    try:
        platform.validate_images(images)
    except ValueError as exc:
        warnings.append(str(exc))

    return {
        "title": adapted_title,
        "content": adapted_content,
        "content_length": len(adapted_content),
        "max_title_length": platform.max_title_length,
        "max_content_length": platform.max_content_length,
        "max_images": platform.max_images,
        "content_type": platform.content_type,
        "warnings": warnings,
    }


def _result_payload(result: PublishResult) -> Dict:
    return {
        "success": result.success,
        "platform": result.platform,
        "message": result.message,
        "url": result.url,
        "published_at": result.published_at.isoformat(),
        "raw_response": result.raw_response,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/platforms", methods=["GET"])
def list_platforms():
    manager = get_platform_manager()
    platforms = []

    for item in get_platform_catalog():
        platform = manager.get_platform(item.name)
        platforms.append(
            {
                "name": item.name,
                "display_name": item.display_name,
                "summary": item.summary,
                "style": item.style,
                "credential_env": list(item.credential_env),
                "has_credentials": is_credentials_ready(item.name),
                "supports_rpa": item.supports_rpa,
                "max_title_length": platform.max_title_length if platform else None,
                "max_content_length": platform.max_content_length if platform else None,
                "max_images": platform.max_images if platform else None,
                "content_type": platform.content_type if platform else "",
            }
        )

    return jsonify({"success": True, "platforms": platforms})


@app.route("/api/preview", methods=["POST"])
def preview():
    data = _payload()
    title = data.get("title", "")
    content = data.get("content", "")
    images = data.get("images", []) or []

    manager = get_platform_manager()
    previews = {}

    for platform_name in _selected_platforms(data, manager):
        platform = manager.get_platform(platform_name)
        if platform is None:
            previews[platform_name] = {"error": "平台未注册"}
            continue
        previews[platform_name] = _adapt_preview(platform, title, content, images)

    return jsonify({"success": True, "previews": previews})


@app.route("/api/publish", methods=["POST"])
def publish():
    data = _payload()
    title = data.get("title", "")
    content = data.get("content", "")
    images = data.get("images", []) or []
    tags = _parse_tags(data.get("tags", ""))
    mode_value = str(data.get("mode", "simulate")).lower()
    real_requested = data.get("real", False) or mode_value == "real"
    mode = PublishMode.REAL if real_requested else PublishMode.SIMULATE

    manager = get_platform_manager()
    results = {}

    for platform_name in _selected_platforms(data, manager):
        platform = manager.get_platform(platform_name)
        if platform is None:
            results[platform_name] = {
                "success": False,
                "message": "平台未注册",
            }
            continue

        result = platform.publish(
            title=title,
            content=content,
            images=images,
            mode=mode,
            tags=",".join(tags),
            save_as_draft=True,
        )
        results[platform_name] = _result_payload(result)

    return jsonify(
        {
            "success": True,
            "mode": mode.value,
            "results": results,
        }
    )


@app.route("/api/drafts", methods=["GET"])
def list_drafts():
    drafts = draft_manager.list_drafts()
    return jsonify(
        {
            "success": True,
            "drafts": [
                {
                    "id": draft.get("id", ""),
                    "title": draft.get("title", ""),
                    "updated_at": draft.get("updated_at"),
                }
                for draft in drafts
            ],
        }
    )


@app.route("/api/drafts", methods=["POST"])
def save_draft():
    data = _payload()
    draft = draft_manager.new_draft(
        title=data.get("title", ""),
        content=data.get("content", ""),
        tags=_parse_tags(data.get("tags", "")),
    )
    draft_manager.save_current(draft)
    return jsonify({"success": True, "draft_id": draft.id})


@app.route("/api/drafts/<draft_id>", methods=["GET"])
def load_draft(draft_id):
    try:
        draft = draft_manager.load_draft(draft_id)
        return jsonify(
            {
                "success": True,
                "draft": {
                    "id": draft.id,
                    "title": draft.content.title,
                    "content": draft.content.content,
                    "tags": ",".join(draft.content.tags)
                    if draft.content.tags
                    else "",
                },
            }
        )
    except FileNotFoundError:
        return jsonify({"success": False, "message": "草稿不存在"}), 404


@app.route("/api/drafts/<draft_id>", methods=["DELETE"])
def delete_draft(draft_id):
    return jsonify({"success": draft_manager.delete_draft(draft_id)})


@app.route("/api/rpa/login", methods=["POST"])
def rpa_login():
    data = _payload()
    platform = data.get("platform", "")
    rpa_map = {
        "bilibili": "BilibiliRPA",
        "xiaohongshu": "XiaohongshuRPA",
        "zhihu": "ZhihuRPA",
    }

    if platform not in rpa_map:
        return jsonify({"success": False, "message": f"不支持的平台: {platform}"})

    try:
        module = __import__(
            f"src.rpa.{platform}_rpa",
            fromlist=[rpa_map[platform]],
        )
        rpa_class = getattr(module, rpa_map[platform])
        rpa = rpa_class(headless=False)
        success = rpa.login(timeout=120)
        rpa.close()

        return jsonify(
            {
                "success": success,
                "message": f"{platform} 登录{'成功' if success else '失败或超时'}",
            }
        )
    except ImportError:
        return jsonify(
            {
                "success": False,
                "message": "需要安装 Playwright: pip install playwright && playwright install chromium",
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "message": f"RPA 登录异常: {exc}"})


@app.route("/api/rpa/status", methods=["GET"])
def rpa_status():
    platform_status = {}
    rpa_map = {
        "bilibili": "BilibiliRPA",
        "xiaohongshu": "XiaohongshuRPA",
        "zhihu": "ZhihuRPA",
    }

    for platform, class_name in rpa_map.items():
        try:
            module = __import__(f"src.rpa.{platform}_rpa", fromlist=[class_name])
            rpa_class = getattr(module, class_name)
            rpa = rpa_class()
            platform_status[platform] = rpa.check_login()
            rpa.close()
        except Exception:
            platform_status[platform] = False

    return jsonify({"success": True, "login_status": platform_status})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
