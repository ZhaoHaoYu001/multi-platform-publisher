# Multi-Platform Publisher

题目二：多平台内容发布工具。用户输入一份内容后，系统自动适配微信公众号、知乎、B站、小红书等平台的格式与风格，并支持一键模拟发布或真实发布。

## 当前开发阶段

本次检查时间：2026-05-31。

当前项目已经进入“可演示的功能完善阶段”：

- 已有平台抽象层：`PlatformBase` 统一标题、正文、图片校验和发布模式。
- 已支持 4 个核心平台：微信公众号、知乎、B站专栏、小红书。
- 已具备自动适配能力：不同平台有不同标题长度、正文长度、内容类型和格式转换规则。
- 已具备发布能力：默认支持模拟发布，配置凭证后可走 API；部分平台在无 API 凭证时可回退到 Playwright RPA。
- 已具备 Web 演示链路：输入内容、选择平台、生成适配预览、保存草稿、一键发布。
- 已具备扩展基础：新增平台可以通过平台类、平台目录配置和 Web 注册信息接入。

远端 GitHub `main` 分支已经推进到更完整的 v2 架构方向，包含规则引擎、适配器注册、发布管线、任务队列、定时发布、模板系统、抖音/微博扩展等。当前工作区仍在 `feat/rpa-publish` 分支上，并保留了本地未提交的 RPA/Web 修改；本次改动优先补齐题目要求的演示闭环。

## 功能对应题目要求

| 题目要求 | 项目实现 |
| --- | --- |
| 用户输入内容 | Web 面板提供标题、正文、标签输入 |
| 自动适配各平台格式与风格 | 每个平台实现 `adapt_title`、`adapt_content`、图片数量限制和内容类型 |
| 一键发布 | Web 面板可勾选多个平台并一次提交 |
| 可选模拟发布 | Web 默认“模拟发布”，不会调用真实平台接口 |
| 扩展更多平台架构设计 | `src/core/platform_catalog.py` + `src/platforms/*` + `PlatformManager` |

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python web/app.py
```

访问：

```text
http://localhost:5000
```

命令行模拟发布：

```bash
python publish.py -t "我的文章标题" -c "这里是 Markdown 正文" -p wechat,zhihu,bilibili,xiaohongshu
```

真实发布需要先配置 `.env`：

```env
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret
ZHIHU_USERNAME=your_username
ZHIHU_PASSWORD=your_password
BILIBILI_SESS_DATA=your_sess_data
BILIBILI_CSRF=your_csrf
XIAOHONGSHU_COOKIE=your_cookie
```

请勿把 token、cookie、密码提交到仓库。

## 平台适配策略

| 平台 | 标题限制 | 正文限制 | 图片限制 | 内容类型 | 风格适配 |
| --- | ---: | ---: | ---: | --- | --- |
| 微信公众号 | 64 | 20000 | 10 | 富文本 | Markdown 转 HTML，保留图文排版 |
| 知乎 | 60 | 20000 | 30 | Markdown | 保留知识型长文结构，代码块补默认语言 |
| B站专栏 | 80 | 15000 | 100 | 富文本 | 标题强化、分割线转换、社区化专栏格式 |
| 小红书 | 20 | 1000 | 9 | 纯文本 | Markdown 转纯文本，自动加入话题和口吻 |

## Web 演示流程

1. 输入标题、正文和标签。
2. 选择目标平台。
3. 点击“生成适配预览”，查看每个平台的标题、正文和限制提醒。
4. 默认保持“模拟发布”，点击“一键发布”查看发布结果。
5. 如需真实发布，配置凭证后切换为“真实发布”。

## 架构设计

```text
Web/CLI
  |
  v
PlatformManager
  |
  +-- PlatformBase
      |
      +-- WechatPlatform
      +-- ZhihuPlatform
      +-- BilibiliPlatform
      +-- XiaohongshuPlatform
  |
  +-- platform_catalog.py
      |
      +-- 平台展示信息
      +-- 凭证环境变量
      +-- 平台实例构造
```

核心接口：

- `adapt_title(title)`：按平台标题限制裁剪或风格化。
- `adapt_content(content)`：把 Markdown 转换为平台需要的内容形态。
- `validate_images(images)`：检查图片数量与平台限制。
- `publish(..., mode=PublishMode.SIMULATE)`：统一发布入口。
- `_do_publish(...)`：平台真实发布实现，可走 API 或 RPA。

## 扩展新平台

新增平台建议按以下步骤：

1. 在 `src/platforms/` 新建平台类，继承 `PlatformBase`。
2. 设置 `name`、`max_title_length`、`max_content_length`、`max_images`、`content_type`。
3. 实现 `adapt_content`，处理该平台的格式和风格。
4. 实现 `_do_publish`，支持 API 发布；没有开放 API 时可新增 RPA fallback。
5. 在 `src/core/platform_catalog.py` 注册平台展示信息和凭证环境变量。
6. 在 Web 或 CLI 的平台列表中暴露该平台。
7. 为标题截断、正文适配、图片限制、模拟发布添加测试。

这样扩展抖音、微博、今日头条等平台时，不需要改动发布主流程，只要新增平台实现并注册即可。
