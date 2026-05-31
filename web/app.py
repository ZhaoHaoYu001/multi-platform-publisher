"""Web management panel with create_app() factory."""

import json, os, sys, uuid
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, jsonify, render_template, request
from src.adapters.registry import AdapterRegistry
from src.adapters.wechat_adapter import WechatAdapter
from src.adapters.zhihu_adapter import ZhihuAdapter
from src.adapters.bilibili_adapter import BilibiliAdapter
from src.adapters.xiaohongshu_adapter import XiaohongshuAdapter
from src.adapters.douyin_adapter import DouyinAdapter
from src.adapters.weibo_adapter import WeiboAdapter
from src.rpa.bilibili_rpa import BilibiliRPA
from src.rpa.douyin_rpa import DouyinRPA
from src.rpa.weibo_rpa import WeiboRPA
from src.rpa.xiaohongshu_rpa import XiaohongshuRPA
from src.rpa.zhihu_rpa import ZhihuRPA
from src.core.content_parser import ContentParser
from src.core.credential_store import CredentialStore
from src.core.platform_base import PublishMode
from src.core.rule_engine import RuleEngine
from src.core.task_queue import TaskQueue
from src.core.scheduler import Scheduler
from src.draft.draft_manager import DraftManager
from src.media.image_processor import ImageProcessor
from src.pipeline.publish_pipeline import (
    AdaptStage, DeliverStage, ImageProcessStage,
    ParseStage, PipelineContext, PublishPipeline,
)
from src.review.previewer import Previewer
from src.ai.mimo_client import MiMoClient
from src.ai.content_generator import ContentGenerator


RPA_LOGIN_PLATFORMS = {
    "zhihu": ("知乎", ZhihuRPA),
    "bilibili": ("B站", BilibiliRPA),
    "xiaohongshu": ("小红书", XiaohongshuRPA),
    "douyin": ("抖音", DouyinRPA),
    "weibo": ("微博", WeiboRPA),
}


def create_app():
    """Create and configure the Flask app."""
    app = Flask(__name__)

    # Init components
    base = os.path.join(os.path.dirname(__file__), "..")
    rule_engine = RuleEngine(rules_dir=os.path.join(base, "config", "rules"))
    draft_manager = DraftManager(drafts_dir=os.path.join(base, "drafts"))
    previewer = Previewer()
    task_queue = TaskQueue()
    image_processor = ImageProcessor()
    scheduler = Scheduler(task_queue)
    registry = AdapterRegistry(rule_engine)
    credential_store = CredentialStore()
    credential_store.load_from_env()

    # 初始化 AI 内容生成器
    mimo_client = MiMoClient()
    content_generator = ContentGenerator(client=mimo_client)

    for cls in [WechatAdapter, ZhihuAdapter, BilibiliAdapter, XiaohongshuAdapter, DouyinAdapter, WeiboAdapter]:
        registry.register(cls.platform_name, cls)

    def _creds():
        return {p: credential_store.get(p) for p in credential_store.list_platforms()}

    # Register routes
    _register_routes(app, registry, rule_engine, draft_manager, previewer,
                     task_queue, image_processor, scheduler, credential_store, _creds,
                     content_generator)

    return app


def _register_routes(app, registry, rule_engine, draft_manager, previewer,
                      task_queue, image_processor, scheduler, credential_store, _creds,
                      content_generator=None):
    """Register all routes."""

    BUILTIN_TEMPLATES = [
        {"id": "tech-tutorial", "name": "技术教程", "description": "适用于技术教程类文章",
         "title_template": "{{title}}：从入门到精通",
         "content_template": "# {{title}}\n\n## 前言\n\n在本教程中",
         "variables": ["title", "topic", "package", "code_example", "advanced_content", "summary", "tags"]},
        {"id": "product-review", "name": "产品评测", "description": "适用于产品评测类文章",
         "title_template": "{{product}} 深度评测：{{verdict}}",
         "variables": ["product", "brand", "category", "verdict", "design_review", "feature_review", "pros", "cons", "recommendation", "tags"]},
        {"id": "daily-share", "name": "日常分享", "description": "适用于日常分享类文章",
         "title_template": "{{title}}",
         "variables": ["title", "mood", "topic", "section1_title", "section1_content", "section2_title", "section2_content", "ending", "tags"]},
        {"id": "industry-analysis", "name": "行业分析", "description": "适用于行业分析类文章",
         "title_template": "{{year}}{{industry}}行业{{topic}}分析",
         "variables": ["year", "industry", "topic", "background", "market_status", "trends", "competition", "outlook", "tags"]},
    ]

    @app.route("/")
    def index():
        """首页 - 内容编辑."""
        return render_template("index.html")


    @app.route("/templates")
    def templates_page():
        """模板管理页面."""
        return render_template("templates.html")


    @app.route("/tasks")
    def tasks_page():
        """任务监控页面."""
        return render_template("tasks.html")


    @app.route("/settings")
    def settings_page():
        """设置页面."""
        return render_template("settings.html")


    # ──────────────────── 平台 API ────────────────────

    @app.route("/api/platforms", methods=["GET"])
    def list_platforms():
        """获取平台列表和规则."""
        platforms = []
        for name in registry.list_platforms():
            try:
                rules = rule_engine.load_rules(name)
                platforms.append({
                    "name": name,
                    "max_title_length": rules.title.max_length,
                    "max_content_length": 20000,
                    "content_type": rules.content.output_format,
                    "has_credentials": bool(_creds().get(name)),
                })
            except FileNotFoundError:
                platforms.append({"name": name, "error": "规则文件缺失"})
        return jsonify({"success": True, "platforms": platforms})


    # ──────────────────── 预览 API ────────────────────

    @app.route("/api/preview", methods=["POST"])
    def preview():
        """预览各平台格式（使用 RuleEngine 适配）."""
        data = request.json
        title = data.get("title", "")
        content = data.get("content", "")
        tags = data.get("tags", "")

        parser = ContentParser()
        doc = parser.parse(content, title=title, tags=tags.split(",") if tags else None)

        previews = {}
        for name in registry.list_platforms():
            try:
                adapter = registry.get(name, credentials=_creds().get(name, {}))
                adapted = adapter.adapt(doc)
                previews[name] = {
                    "title": adapted.title,
                    "content": adapted.content,
                    "warnings": adapted.warnings,
                }
            except Exception as e:
                previews[name] = {"error": str(e)}

        return jsonify({"success": True, "previews": previews})


    # ──────────────────── 发布 API ────────────────────

    @app.route("/api/publish", methods=["POST"])
    def publish():
        """发布到选中平台（使用 Pipeline）."""
        data = request.json
        title = data.get("title", "")
        content = data.get("content", "")
        tags = data.get("tags", "")
        images = data.get("images", [])
        platforms = data.get("platforms", [])
        mode = PublishMode.REAL if data.get("real", False) else PublishMode.SIMULATE
        adapted_contents = data.get("adapted_contents", {})  # 预适配的内容 {platform: {title, content}}

        credentials = _creds()
        results = {}

        for platform_name in platforms:
            adapter = registry.get(platform_name, credentials=credentials.get(platform_name, {}))
            if adapter is None:
                results[platform_name] = {"success": False, "message": f"平台 {platform_name} 未注册"}
                continue

            # 创建任务
            task_id = task_queue.enqueue(platform=platform_name, title=title)
            task_queue.update_status(task_id, "publishing")

            try:
                # 如果提供了预适配内容，直接使用；否则走完整 pipeline
                if platform_name in adapted_contents:
                    adapted = adapted_contents[platform_name]
                    adapted_title = adapted.get("title", title)
                    adapted_content = adapted.get("content", content)
                    # 构造 AdaptationResult 用于投递
                    from src.adapters.base_adapter import AdaptationResult
                    adapted_result = AdaptationResult(
                        title=adapted_title,
                        content=adapted_content,
                        warnings=[],
                    )
                    if mode == PublishMode.SIMULATE:
                        result = adapter._simulate(adapted_result)
                    else:
                        result = adapter.deliver(adapted_result, images)
                    results[platform_name] = {
                        "success": result.success,
                        "message": result.message,
                        "url": result.url,
                        "task_id": task_id,
                    }
                    status = "success" if result.success else "failed"
                    task_queue.update_status(task_id, status, result=result)
                    continue
                else:
                    pipeline = PublishPipeline.create_default(
                        adapter=adapter,
                        title=title,
                        tags=tags.split(",") if tags else None,
                    )
                    ctx = PipelineContext(
                        metadata={
                            "raw_content": content,
                            "title": title,
                            "tags": tags.split(",") if tags else [],
                            "images": images,
                            "mode": mode,
                        },
                        platform=platform_name,
                    )
                    ctx = pipeline.execute(ctx)
    
                if ctx.result:
                    results[platform_name] = {
                        "success": ctx.result.success,
                        "message": ctx.result.message,
                        "url": ctx.result.url,
                        "task_id": task_id,
                    }
                    status = "success" if ctx.result.success else "failed"
                    task_queue.update_status(task_id, status, result=ctx.result)
                else:
                    error_msg = "; ".join(ctx.errors) if ctx.errors else "未知错误"
                    results[platform_name] = {"success": False, "message": error_msg, "task_id": task_id}
                    task_queue.update_status(task_id, "failed", error=error_msg)

            except Exception as e:
                results[platform_name] = {"success": False, "message": str(e), "task_id": task_id}
                task_queue.update_status(task_id, "failed", error=str(e))

        return jsonify({"success": True, "results": results})


    # ──────────────────── 草稿 API ────────────────────

    @app.route("/api/drafts", methods=["GET"])
    def list_drafts():
        """获取草稿列表."""
        drafts = draft_manager.list_drafts()
        return jsonify({
            "success": True,
            "drafts": [
                {
                    "id": d.get("id"),
                    "title": d.get("title", "无标题"),
                    "updated_at": d.get("updated_at"),
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
            draft.content.tags = [t.strip() for t in tags.split(",") if t.strip()]
        draft_manager.save_current(draft)

        return jsonify({"success": True, "draft_id": draft.id})


    @app.route("/api/drafts/<draft_id>", methods=["GET"])
    def load_draft(draft_id):
        """加载草稿."""
        try:
            draft = draft_manager.load_draft(draft_id)
            return jsonify({
                "success": True,
                "draft": {
                    "id": draft.id,
                    "title": draft.content.title,
                    "content": draft.content.content,
                    "tags": ",".join(draft.content.tags) if draft.content.tags else "",
                },
            })
        except FileNotFoundError:
            return jsonify({"success": False, "message": "草稿不存在"}), 404


    @app.route("/api/drafts/<draft_id>", methods=["DELETE"])
    def delete_draft(draft_id):
        """删除草稿."""
        success = draft_manager.delete_draft(draft_id)
        return jsonify({"success": success})


    # ──────────────────── 任务 API ────────────────────

    @app.route("/api/tasks", methods=["GET"])
    def list_tasks():
        """获取任务列表."""
        status_filter = request.args.get("status")
        tasks = task_queue.list_tasks(status=status_filter)
        return jsonify({
            "success": True,
            "tasks": [
                {
                    "id": t.id,
                    "platform": t.platform,
                    "title": t.title,
                    "status": t.status,
                    "error": t.error,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in tasks
            ],
        })


    @app.route("/api/tasks/<task_id>", methods=["GET"])
    def get_task(task_id):
        """获取单个任务状态."""
        task = task_queue.get_status(task_id)
        if task is None:
            return jsonify({"success": False, "message": "任务不存在"}), 404
        return jsonify({
            "success": True,
            "task": {
                "id": task.id,
                "platform": task.platform,
                "title": task.title,
                "status": task.status,
                "error": task.error,
                "created_at": task.created_at.isoformat() if task.created_at else None,
            },
        })


    @app.route("/api/tasks", methods=["DELETE"])
    def clear_tasks():
        """清空任务队列."""
        task_queue.clear()
        return jsonify({"success": True})


    # ──────────────────── 模板 API ────────────────────

    # 内置模板
    BUILTIN_TEMPLATES = [
        {
            "id": "tech-tutorial",
            "name": "技术教程",
            "description": "适用于技术教程类文章",
            "title_template": "{{title}}：从入门到精通",
            "content_template": (
                "# {{title}}\n\n"
                "## 前言\n\n在本教程中，我们将学习{{topic}}。\n\n"
                "## 环境准备\n\n- Python 3.8+\n- pip install {{package}}\n\n"
                "## 基础用法\n\n```python\n# 示例代码\n{{code_example}}\n```\n\n"
                "## 进阶技巧\n\n{{advanced_content}}\n\n"
                "## 总结\n\n{{summary}}\n\n"
                "> 分类: 技术 | 标签: {{tags}}"
            ),
            "variables": ["title", "topic", "package", "code_example", "advanced_content", "summary", "tags"],
        },
        {
            "id": "product-review",
            "name": "产品评测",
            "description": "适用于产品评测类文章",
            "title_template": "{{product}} 深度评测：{{verdict}}",
            "content_template": (
                "# {{product}} 深度评测\n\n"
                "## 产品概述\n\n{{product}}是{{brand}}推出的{{category}}。\n\n"
                "## 外观设计\n\n{{design_review}}\n\n"
                "## 功能体验\n\n{{feature_review}}\n\n"
                "## 优缺点\n\n**优点：**\n{{pros}}\n\n**缺点：**\n{{cons}}\n\n"
                "## 购买建议\n\n{{recommendation}}\n\n"
                "> 分类: 评测 | 标签: {{tags}}"
            ),
            "variables": ["product", "brand", "category", "verdict", "design_review", "feature_review", "pros", "cons", "recommendation", "tags"],
        },
        {
            "id": "daily-share",
            "name": "日常分享",
            "description": "适用于日常分享类文章",
            "title_template": "{{title}}",
            "content_template": (
                "# {{title}}\n\n"
                "今天{{mood}}，想和大家分享一下{{topic}}。\n\n"
                "## {{section1_title}}\n\n{{section1_content}}\n\n"
                "## {{section2_title}}\n\n{{section2_content}}\n\n"
                "## 写在最后\n\n{{ending}}\n\n"
                "> 分类: 生活 | 标签: {{tags}}"
            ),
            "variables": ["title", "mood", "topic", "section1_title", "section1_content", "section2_title", "section2_content", "ending", "tags"],
        },
        {
            "id": "industry-analysis",
            "name": "行业分析",
            "description": "适用于行业分析类文章",
            "title_template": "{{year}}{{industry}}行业{{topic}}分析",
            "content_template": (
                "# {{year}}{{industry}}行业{{topic}}分析\n\n"
                "## 行业背景\n\n{{background}}\n\n"
                "## 市场现状\n\n{{market_status}}\n\n"
                "## 关键趋势\n\n{{trends}}\n\n"
                "## 竞争格局\n\n{{competition}}\n\n"
                "## 未来展望\n\n{{outlook}}\n\n"
                "> 分类: 行业 | 标签: {{tags}}"
            ),
            "variables": ["year", "industry", "topic", "background", "market_status", "trends", "competition", "outlook", "tags"],
        },
    ]


    @app.route("/api/templates", methods=["GET"])
    def list_templates():
        """获取模板列表."""
        return jsonify({"success": True, "templates": BUILTIN_TEMPLATES})


    @app.route("/api/templates/<template_id>", methods=["GET"])
    def get_template(template_id):
        """获取单个模板."""
        for tpl in BUILTIN_TEMPLATES:
            if tpl["id"] == template_id:
                return jsonify({"success": True, "template": tpl})
        return jsonify({"success": False, "message": "模板不存在"}), 404


    @app.route("/api/templates/<template_id>/apply", methods=["POST"])
    def apply_template(template_id):
        """应用模板（变量替换）."""
        data = request.json
        variables = data.get("variables", {})

        tpl = None
        for t in BUILTIN_TEMPLATES:
            if t["id"] == template_id:
                tpl = t
                break

        if tpl is None:
            return jsonify({"success": False, "message": "模板不存在"}), 404

        title = tpl["title_template"]
        content = tpl["content_template"]
        for key, value in variables.items():
            title = title.replace("{{" + key + "}}", value)
            content = content.replace("{{" + key + "}}", value)

        return jsonify({"success": True, "title": title, "content": content})


    # ──────────────────── 定时发布 API ────────────────────

    @app.route("/api/schedule", methods=["POST"])
    def schedule_publish():
        """创建定时发布任务."""
        data = request.json
        title = data.get("title", "")
        content = data.get("content", "")
        tags = data.get("tags", "")
        images = data.get("images", [])
        platforms = data.get("platforms", [])
        scheduled_at = data.get("scheduled_at")  # ISO格式时间
        delay_seconds = data.get("delay_seconds")  # 延迟秒数

        if not title or not content:
            return jsonify({"success": False, "message": "请填写标题和内容"}), 400

        if not platforms:
            return jsonify({"success": False, "message": "请至少选择一个平台"}), 400

        # 解析时间
        from datetime import datetime as dt, timedelta
        if scheduled_at:
            try:
                run_at = dt.fromisoformat(scheduled_at.replace("Z", "+00:00"))
            except ValueError:
                return jsonify({"success": False, "message": "时间格式无效"}), 400
        elif delay_seconds:
            run_at = dt.now() + timedelta(seconds=int(delay_seconds))
        else:
            return jsonify({"success": False, "message": "请指定执行时间或延迟"}), 400

        results = {}
        for platform_name in platforms:
            task_id = task_queue.schedule_at(
                platform=platform_name,
                title=title,
                scheduled_at=run_at,
                content=content,
                images=images,
                tags=tags,
            )
            results[platform_name] = {"task_id": task_id, "scheduled_at": run_at.isoformat()}

        return jsonify({"success": True, "results": results})


    @app.route("/api/schedule", methods=["GET"])
    def list_scheduled():
        """列出定时任务."""
        tasks = task_queue.list_scheduled_tasks()
        return jsonify({
            "success": True,
            "tasks": [
                {
                    "id": t.id,
                    "platform": t.platform,
                    "title": t.title,
                    "status": t.status,
                    "scheduled_at": t.scheduled_at.isoformat() if t.scheduled_at else None,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in tasks
            ],
        })


    @app.route("/api/schedule/<task_id>", methods=["DELETE"])
    def cancel_scheduled(task_id):
        """取消定时任务."""
        success = task_queue.cancel_task(task_id)
        return jsonify({"success": success})


    @app.route("/api/scheduler/status", methods=["GET"])
    def scheduler_status():
        """获取调度器状态."""
        return jsonify({"success": True, "status": scheduler.get_status()})
    
    
    # ──────────────────── AI 内容生成 API ────────────────────

    @app.route("/api/ai/generate", methods=["POST"])
    def ai_generate():
        """AI 一句话生成完整文案."""
        if content_generator is None or not content_generator.is_available:
            return jsonify({
                "success": False,
                "error": "AI 生成功能不可用，请检查 MIMO_API_KEY 配置",
            }), 503

        data = request.json
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return jsonify({"success": False, "error": "请输入内容描述"}), 400

        style = data.get("style", "general")
        target_platform = data.get("platform")
        title = data.get("title")

        try:
            result = content_generator.generate(
                prompt=prompt,
                style=style,
                target_platform=target_platform,
                title=title,
            )
            return jsonify({
                "success": True,
                "title": result.title,
                "content": result.content,
                "tags": result.tags,
                "summary": result.summary,
                "style": result.style,
                "platform": result.target_platform,
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/ai/styles", methods=["GET"])
    def ai_styles():
        """获取 AI 支持的内容风格列表."""
        return jsonify({
            "success": True,
            "styles": content_generator.list_styles() if content_generator else {},
        })

    @app.route("/api/ai/platforms", methods=["GET"])
    def ai_platforms():
        """获取 AI 支持的平台特性列表."""
        return jsonify({
            "success": True,
            "platforms": content_generator.list_platforms() if content_generator else {},
        })

    @app.route("/api/ai/status", methods=["GET"])
    def ai_status():
        """检查 AI 功能状态."""
        available = content_generator is not None and content_generator.is_available
        return jsonify({
            "success": True,
            "available": available,
            "has_api_key": bool(os.getenv("MIMO_API_KEY")),
            "has_base_url": bool(os.getenv("MIMO_BASE_URL")),
        })

    # ──────────────────── 凭证 API ────────────────────

    @app.route("/api/credentials", methods=["GET"])
    def get_credentials():
        """获取凭证状态（不返回实际值）."""
        status = credential_store.get_all_status()
        return jsonify({"success": True, "credentials": status})


    # ──────────────────── RPA 登录态 API ────────────────────

    @app.route("/api/rpa/status", methods=["GET"])
    def rpa_status():
        """获取RPA预登录状态."""
        platforms = []
        for name, (label, rpa_cls) in RPA_LOGIN_PLATFORMS.items():
            try:
                rpa = rpa_cls()
                status = rpa.session_status()
                status.update({"name": name, "label": label})
                platforms.append(status)
            except Exception as e:
                platforms.append({
                    "name": name,
                    "label": label,
                    "has_saved_session": False,
                    "error": str(e),
                })
        return jsonify({"success": True, "platforms": platforms})


    @app.route("/api/rpa/login", methods=["POST"])
    def rpa_login():
        """打开指定平台的RPA预登录窗口."""
        data = request.get_json(silent=True) or {}
        platform = data.get("platform")

        if platform not in RPA_LOGIN_PLATFORMS:
            return jsonify({"success": False, "message": "不支持的平台"}), 400

        label, rpa_cls = RPA_LOGIN_PLATFORMS[platform]
        rpa = rpa_cls()
        try:
            ok = rpa.login(interactive=True)
            message = (
                f"{label} 预登录成功，后续真实发布将复用该登录态。"
                if ok
                else f"{label} 预登录未完成，请确认已安装 Playwright 并在打开的窗口中完成登录。"
            )
            return jsonify({
                "success": ok,
                "message": message,
                "status": rpa.session_status(),
            })
        finally:
            rpa.close_browser()


    # ──────────────────── 启动 ────────────────────

    if __name__ == "__main__":
        app.run(debug=True, host="0.0.0.0", port=5000)



if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
