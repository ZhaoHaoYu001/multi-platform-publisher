# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

## [2.0.0] - 2026-05-31

### ✨ 新增
- **Phase 5: Web管理面板重构**
  - 迁移到 adapter/pipeline 架构
  - 新增模板管理页面 (`/templates`)
  - 新增任务监控页面 (`/tasks`)
  - 新增设置页面 (`/settings`)
  - 内置4个内容模板（技术教程/产品评测/日常分享/行业分析）
  - 前端: Markdown工具栏、图片上传、Toast提示、响应式布局

- **Phase 6: 图片处理管线增强**
  - `ImageProcessStage` 读取 YAML media 规则自动裁剪/压缩
  - 新增 `MediaUploadStage` 媒体上传阶段
  - Pipeline 顺序: Parse → Adapt → ImageProcess → MediaUpload → Deliver

- **Phase 7: 凭证存储集中化**
  - 新增 `CredentialStore` 统一凭证管理
  - 支持 .env 文件和环境变量两种来源
  - 提供 `is_platform_ready()` 检查凭证完整性
  - 支持6个平台凭证管理

- **Phase 8: 新平台接入**
  - 新增抖音平台支持（API + RPA）
  - 新增微博平台支持（API + RPA）
  - 新增 YAML 适配规则: `config/rules/douyin.yaml`, `config/rules/weibo.yaml`

- **定时发布功能**
  - `TaskQueue` 新增 `schedule_at()` 和 `schedule_delay()` 方法
  - 新增 `Scheduler` 调度器（基于 threading）
  - 新增 API: `/api/schedule` (创建/列出/取消定时任务)

- **内容模板系统**
  - 新增 `TemplateManager` 模板管理器
  - 支持 `{{variable}}` 变量语法
  - 支持 YAML 文件扩展模板

### 🔧 改进
- 统一发布管线支持5个阶段
- Web面板使用 `AdapterRegistry` + `PublishPipeline`
- 所有适配器支持 API/RPA 双路径投递

### 📝 文档
- 更新 README: 添加新功能说明和架构图
- 更新 CHANGELOG: 记录所有新变更

---

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

## [Phase 1-4] - 2026-05-31 (架构重构)

### Phase 1: ContentDocument 模型
- 新增 `ContentDocument`, `ContentSection`, `ImageRef` 结构化文档模型
- 新增 `ContentParser` Markdown 解析器

### Phase 2: YAML 规则引擎
- 新增 `RuleEngine` YAML 规则引擎
- 新增 `ContentTransforms` 变换函数集（16个变换函数）

### Phase 3: 平台适配器层
- 新增 `PlatformAdapter` 适配器基类
- 新增 `AdapterRegistry` 适配器注册中心
- 适配与投递分离设计

### Phase 4: 统一发布管线
- 新增 `PublishPipeline` 发布管线
- 新增 `TaskQueue` 任务队列
- 管线阶段: Parse → Adapt → ImageProcess → Deliver
