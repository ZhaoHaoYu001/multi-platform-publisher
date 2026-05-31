"""Web管理面板.

基于Flask的内容管理和多平台发布Web界面。
"""

import json
import os
import sys

# 将项目根目录加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, render_template, request

from src.core.platform_base import PublishMode
from src.core.platform_manager import PlatformManager
from src.draft.draft_manager import DraftManager
from src.platforms.bilibili import BilibiliPlatform
from src.platforms.wechat import WechatPlatform
from src.platforms.xiaohongshu import XiaohongshuPlatform
from src.platforms.zhihu import ZhihuPlatform
from src.review.previewer import Previewer

app = Flask(__name__)

# 初始化草稿管理器
draft_manager = DraftManager(storage_dir=os.path.join(os.path.dirname(__file__), "..", "drafts"))
previewer = Previewer()


def get_platform_manager() -> PlatformManager:
    """根据环境变量初始化平台管理器."""
    from dotenv import load_dotenv

    load_dotenv()

    manager = PlatformManager()

    # 微信
    wechat_id = os.getenv("WECHAT_APP_ID", "")
    wechat_secret = os.getenv("WECHAT_APP_SECRET", "")
    if wechat_id and wechat_secret:
        manager.register(WechatPlatform(app_id=wechat_id, app_secret=wechat_secret))

    # 知乎
    zhihu_user = os.getenv("ZHIHU_USERNAME", "")
    zhihu_pass = os.getenv("ZHIHU_PASSWORD", "")
    manager.register(ZhihuPlatform(username=zhihu_user, password=zhihu_pass))

    # B站
    sess_data = os.getenv("BILIBILI_SESS_DATA", "")
    csrf = os.getenv("BILIBILI_CSRF", "")
    manager.register(BilibiliPlatform(sess_data=sess_data, csrf=csrf))

    # 小红书
    xhs_cookie = os.getenv("XIAOHONGSHU_COOKIE", "")
    manager.register(XiaohongshuPlatform(cookie=xhs_cookie))

    return manager


@app.route("/")
def index():
    """首页 - 内容编辑."""
    return render_template("index.html")


@app.route("/api/preview", methods=["POST"])
def preview():
    """预览各平台格式."""
    data = request.json
    title = data.get("title", "")
    content = data.get("content", "")

    previews = {}
    for platform_name in ["wechat", "zhihu", "bilibili", "xiaohongshu"]:
        html = previewer.generate_preview(title=title, content=content, platform=platform_name)
        previews[platform_name] = html

    return jsonify({"success": True, "previews": previews})


@app.route("/api/publish", methods=["POST"])
def publish():
    """发布到选中平台."""
    data = request.json
    title = data.get("title", "")
    content = data.get("content", "")
    images = data.get("images", [])
    platforms = data.get("platforms", [])

    manager = get_platform_manager()

    results = {}
    for platform_name in platforms:
        platform = manager.get_platform(platform_name)
        if platform:
            result = platform.publish(
                title=title,
                content=content,
                images=images,
                mode=PublishMode.REAL,
            )
            results[platform_name] = {
                "success": result.success,
                "message": result.message,
                "url": result.url,
            }
        else:
            results[platform_name] = {
                "success": False,
                "message": f"平台 {platform_name} 未配置",
            }

    return jsonify({"success": True, "results": results})


@app.route("/api/drafts", methods=["GET"])
def list_drafts():
    """获取草稿列表."""
    drafts = draft_manager.list_drafts()
    return jsonify({
        "success": True,
        "drafts": [
            {
                "id": d.id,
                "title": d.content.title,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in drafts
        ],
    })


@app.route("/api/drafts", methods=["POST"])
def save_draft():
    """保存草稿."""
    data = request.json
    title = data.get("title", "")
    content = data.get("content", "")
    tags = data.get("tags", "")

    draft = draft_manager.new_draft(title=title, content=content)
    if tags:
        draft.content.tags = tags
    draft_manager.save_draft(draft)

    return jsonify({"success": True, "draft_id": draft.id})


@app.route("/api/drafts/<draft_id>", methods=["GET"])
def load_draft(draft_id):
    """加载草稿."""
    draft = draft_manager.load_draft(draft_id)
    if draft:
        return jsonify({
            "success": True,
            "draft": {
                "id": draft.id,
                "title": draft.content.title,
                "content": draft.content.content,
                "tags": draft.content.tags,
            },
        })
    return jsonify({"success": False, "message": "草稿不存在"}), 404


@app.route("/api/drafts/<draft_id>", methods=["DELETE"])
def delete_draft(draft_id):
    """删除草稿."""
    success = draft_manager.delete_draft(draft_id)
    return jsonify({"success": success})


@app.route("/api/platforms", methods=["GET"])
def list_platforms():
    """获取平台列表和状态."""
    manager = get_platform_manager()
    platforms = []
    for p in manager.platforms:
        platforms.append({
            "name": p.name,
            "max_title_length": p.max_title_length,
            "max_content_length": p.max_content_length,
            "max_images": p.max_images,
            "content_type": p.content_type,
        })
    return jsonify({"success": True, "platforms": platforms})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
