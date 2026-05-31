# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [1.1.0] - 2026-05-31

### ✨ 新增
- **RPA浏览器自动化模块** (`src/rpa/`)
  - `RPABase` 基类：封装Playwright浏览器自动化、Cookie持久化、截图保存
  - `BilibiliRPA`：B站专栏RPA发布
  - `ZhihuRPA`：知乎文章RPA发布
  - `XiaohongshuRPA`：小红书笔记RPA发布
- API凭证缺失时自动降级到RPA发布模式
- 新增RPA模块测试（190行）

### 🐛 修复
- 修复 `app.py` 凭证加载Bug：知乎和小红书现在正确从环境变量读取凭证
- 修复 `zhihu.py` 的 `login()` 方法：之前错误地调用 `check_login()` 而非实际登录

### 🔧 改进
- 平台 `_do_publish()` 拆分为 `_publish_via_api()` 和 `_publish_via_rpa()` 双路径
- 更新 `.gitignore`：覆盖RPA运行时文件（cookies/、screenshots/）
- 更新 `requirements.txt`：添加 `playwright>=1.40.0` 依赖

---

## [1.0.0] - 2026-05-30

### ✨ 新增
- **核心架构**
  - `PlatformBase` 平台基类：统一的平台抽象层
  - `PlatformManager` 平台管理器：多平台注册、批量发布、结果汇总
- **四平台支持**
  - 微信公众号（API模式）
  - 知乎（API模式）
  - B站（API模式）
  - 小红书（API模式）
- **媒体处理** (`src/media/`)
  - `ImageProcessor`：图片裁剪、压缩、格式转换
  - `VideoProcessor`：视频转码、封面提取
  - `MediaManager`：媒体文件统一管理
- **草稿系统** (`src/draft/`)
  - `DraftManager`：草稿保存、版本管理、导出Markdown
- **预览系统** (`src/review/`)
  - `Previewer`：各平台发布前效果预览（HTML渲染）
- **API封装** (`src/api/`)
  - `WechatAPI`：微信公众号API
  - `BilibiliAPI`：B站API
- **用户界面**
  - `app.py`：交互式菜单程序
  - `publish.py`：命令行发布工具
- **测试覆盖**
  - 180+测试用例，覆盖全部模块

---

## [未发布]

### 计划中
- 抖音平台支持
- 微博平台支持
- 定时发布功能
- 内容模板系统
