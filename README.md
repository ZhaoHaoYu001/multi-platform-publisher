# Multi-Platform Publisher

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Tests](https://img.shields.io/badge/tests-200%2B-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/ZhaoHaoYu001/multi-platform-publisher/releases)

一个功能完整的多平台内容发布Python工具，支持微信公众号、知乎、B站、小红书、抖音、微博等6个平台的一键发布。

## ✨ 功能特性

- 🚀 **一键多平台发布** - 同时发布到6个平台
- 📝 **内容自适应** - YAML规则引擎自动适配各平台格式
- 🖼️ **智能图片处理** - 按平台规则自动裁剪、压缩、调整比例
- 📁 **草稿管理** - 支持草稿保存、版本管理和导出
- 👁️ **发布预览** - 发布前预览各平台的最终效果
- 🔌 **可扩展架构** - 适配器模式，轻松添加新平台
- 💻 **Web管理面板** - 现代化Web界面，支持所有功能
- 🤖 **RPA浏览器自动化** - 无API凭证时自动降级到Playwright
- ⏰ **定时发布** - 支持定时和延迟发布
- 📋 **内容模板** - 内置4个模板，支持自定义模板

## 📊 支持平台

| 平台 | 状态 | 标题限制 | 内容限制 | 图片限制 | 内容类型 | 特殊处理 |
|------|------|----------|----------|----------|----------|----------|
| 微信公众号 | ✅ | 64字 | 20000字 | 10张 | 富文本 | Markdown→HTML |
| 知乎 | ✅ | 60字 | 20000字 | 30张 | Markdown | 代码块语言标注 |
| B站 | ✅ | 80字 | 15000字 | 100张 | 富文本 | Markdown→BBCode |
| 小红书 | ✅ | 20字 | 1000字 | 9张 | 纯文本 | 自动emoji+话题标签 |
| 抖音 | ✅ | 30字 | 1000字 | 35张 | 纯文本 | 竖版图片+互动引导 |
| 微博 | ✅ | 32字 | 2000字 | 18张 | 纯文本 | 话题标签+GIF支持 |

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ZhaoHaoYu001/multi-platform-publisher.git
cd multi-platform-publisher

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的平台凭证
```

`.env` 文件配置示例：

```env
# 微信公众号
WECHAT_APP_ID=your_app_id
WECHAT_APP_SECRET=your_app_secret

# 知乎
ZHIHU_USERNAME=your_username
ZHIHU_PASSWORD=your_password

# B站
BILIBILI_SESS_DATA=your_sess_data
BILIBILI_CSRF=your_csrf

# 小红书
XIAOHONGSHU_COOKIE=your_cookie

# 抖音（可选）
DOUYIN_COOKIE=your_cookie

# 微博（可选）
WEIBO_COOKIE=your_cookie
```

## 📖 使用方式

### 方式一：Web管理面板（推荐）

```bash
python web/app.py
```

访问 http://localhost:5000 使用Web界面：
- **编辑页面** - Markdown编辑器 + 实时预览
- **模板页面** - 选择模板快速创建内容
- **任务页面** - 监控发布任务状态
- **设置页面** - 查看凭证配置状态

### 方式二：交互式程序

```bash
python app.py
```

### 方式三：命令行工具

```bash
# 模拟发布到所有平台
python publish.py -t "我的文章标题" -c "文章内容"

# 指定平台发布
python publish.py -t "标题" -c "内容" -p wechat,zhihu

# 真实发布
python publish.py -t "标题" -c "内容" --real

# 带图片发布
python publish.py -t "标题" -c "内容" -i image1.jpg image2.jpg
```

### 方式四：Python API

```python
from src.adapters.registry import AdapterRegistry
from src.adapters.wechat_adapter import WechatAdapter
from src.core.rule_engine import RuleEngine
from src.pipeline.publish_pipeline import PublishPipeline, PipelineContext

# 初始化
engine = RuleEngine("config/rules")
registry = AdapterRegistry(engine)
registry.register("wechat", WechatAdapter)

# 获取适配器
adapter = registry.get("wechat", credentials={"app_id": "xxx", "app_secret": "xxx"})

# 创建管线并执行
pipeline = PublishPipeline.create_default(adapter, title="标题")
ctx = PipelineContext(metadata={"raw_content": "# 内容\n\n正文", "mode": PublishMode.SIMULATE})
result = pipeline.execute(ctx)
```

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │  Web面板    │  │   app.py     │  │   publish.py      │  │
│  │  (Flask)    │  │  (交互式)    │  │   (命令行)        │  │
│  └──────┬──────┘  └──────┬───────┘  └────────┬──────────┘  │
│         │                │                    │             │
├─────────┼────────────────┼────────────────────┼─────────────┤
│         │       核心业务层                    │             │
│  ┌──────▼────────────────▼────────────────────▼──────────┐  │
│  │           PublishPipeline (发布管线)                   │  │
│  │    Parse → Adapt → ImageProcess → MediaUpload → Deliver│ │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │                                    │
│  ┌──────────────┐  ┌────▼──────┐  ┌────────────────────┐   │
│  │ RuleEngine   │  │ Adapter   │  │ CredentialStore    │   │
│  │ (YAML规则)   │  │ Registry  │  │ (凭证管理)         │   │
│  └──────────────┘  └───────────┘  └────────────────────┘   │
│                                                             │
│  ┌──────────────┐  ┌───────────┐  ┌────────────────────┐   │
│  │ TaskQueue    │  │ Scheduler │  │ TemplateManager    │   │
│  │ (任务队列)   │  │ (调度器)  │  │ (模板管理)         │   │
│  └──────────────┘  └───────────┘  └────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                     平台适配器层                             │
│  ┌────────┐ ┌───────┐ ┌──────────┐ ┌──────┐ ┌──────┐ ┌────┐│
│  │ Wechat │ │ Zhihu │ │ Bilibili │ │ XHS  │ │Douyin│ │Weibo│
│  └───┬────┘ └───┬───┘ └────┬─────┘ └──┬───┘ └──┬───┘ └──┬─┘│
│      │          │          │          │        │        │   │
├──────┼──────────┼──────────┼──────────┼────────┼────────┼───┤
│      │          │          │          │        │        │   │
│  ┌───▼──────────▼──────────▼──────────▼────────▼────────▼─┐ │
│  │                    API / RPA 层                        │ │
│  │  WechatAPI / ZhihuAPI / BilibiliAPI / DouyinAPI / ...  │ │
│  │  ZhihuRPA / BilibiliRPA / DouyinRPA / WeiboRPA / ...   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
multi-platform-publisher/
├── app.py                          # 交互式主程序
├── publish.py                      # 命令行工具
├── web/                            # Web管理面板
│   ├── app.py                      # Flask应用
│   ├── templates/                  # HTML模板
│   └── static/                     # 静态资源
├── src/
│   ├── core/                       # 核心模块
│   │   ├── platform_base.py        # 平台基类
│   │   ├── platform_manager.py     # 平台管理器
│   │   ├── content_document.py     # 文档模型
│   │   ├── content_parser.py       # Markdown解析器
│   │   ├── rule_engine.py          # YAML规则引擎
│   │   ├── transforms.py           # 内容变换函数
│   │   ├── task_queue.py           # 任务队列
│   │   ├── scheduler.py            # 任务调度器
│   │   ├── credential_store.py     # 凭证管理
│   │   └── template_manager.py     # 模板管理
│   ├── adapters/                   # 平台适配器层
│   │   ├── base_adapter.py         # 适配器基类
│   │   ├── registry.py             # 适配器注册中心
│   │   ├── wechat_adapter.py       # 微信适配器
│   │   ├── zhihu_adapter.py        # 知乎适配器
│   │   ├── bilibili_adapter.py     # B站适配器
│   │   ├── xiaohongshu_adapter.py  # 小红书适配器
│   │   ├── douyin_adapter.py       # 抖音适配器
│   │   └── weibo_adapter.py        # 微博适配器
│   ├── pipeline/                   # 发布管线
│   │   └── publish_pipeline.py     # 管线实现
│   ├── platforms/                  # 平台实现（旧层）
│   ├── api/                        # API封装
│   ├── rpa/                        # RPA自动化
│   ├── media/                      # 媒体处理
│   ├── draft/                      # 草稿管理
│   └── review/                     # 预览系统
├── config/
│   └── rules/                      # YAML规则配置
│       ├── wechat.yaml
│       ├── zhihu.yaml
│       ├── bilibili.yaml
│       ├── xiaohongshu.yaml
│       ├── douyin.yaml
│       └── weibo.yaml
├── tests/                          # 测试文件（200+用例）
├── requirements.txt                # 依赖列表
├── .env.example                    # 环境变量模板
└── README.md                       # 本文档
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_pipeline.py

# 带覆盖率
pytest tests/ --cov=src
```

## 🛠️ 开发指南

### 添加新平台

1. 创建 `config/rules/new_platform.yaml` - 适配规则
2. 创建 `src/platforms/new_platform.py` - 平台实现
3. 创建 `src/adapters/new_platform_adapter.py` - 适配器
4. 创建 `src/api/new_platform_api.py` - API封装（可选）
5. 创建 `src/rpa/new_platform_rpa.py` - RPA模块（可选）
6. 在 `web/app.py` 注册适配器
7. 编写测试 `tests/test_new_platform.py`

### 提交规范

```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具链相关
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
