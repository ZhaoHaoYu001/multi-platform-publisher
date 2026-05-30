# Multi-Platform Publisher

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Tests](https://img.shields.io/badge/tests-180%2B-brightgreen.svg)](tests/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/ZhaoHaoYu001/multi-platform-publisher/releases)

一个功能完整的多平台内容发布Python工具，支持微信公众号、知乎、B站、小红书等平台的一键发布。

## ✨ 功能特性

- 🚀 **一键多平台发布** - 同时发布到微信公众号、知乎、B站、小红书
- 📝 **内容自适应** - 自动适配各平台的标题长度、内容格式限制
- 🖼️ **媒体处理** - 支持图片和视频的上传、裁剪、压缩
- 📁 **草稿管理** - 支持草稿保存、版本管理和导出
- 👁️ **发布预览** - 发布前预览各平台的最终效果
- 🔌 **可扩展架构** - 轻松添加新平台支持
- 💻 **双重界面** - 交互式程序 + 命令行工具

## 📊 支持平台

| 平台 | 状态 | 标题限制 | 内容限制 | 图片限制 | 内容类型 | 特殊处理 |
|------|------|----------|----------|----------|----------|----------|
| 微信公众号 | ✅ | 64字 | 20000字 | 10张 | 富文本 | Markdown→HTML |
| 知乎 | ✅ | 60字 | 20000字 | 30张 | Markdown | 代码块语言标注 |
| B站 | ✅ | 80字 | 15000字 | 100张 | 富文本 | Markdown→BBCode |
| 小红书 | ✅ | 20字 | 1000字 | 9张 | 纯文本 | 自动emoji+话题标签 |

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

# B站
BILIBILI_SESS_DATA=your_sess_data
BILIBILI_CSRF=your_csrf
```

## 📖 详细使用教程

### 方式一：交互式程序

运行交互式程序，通过菜单操作：

```bash
python app.py
```

菜单选项：
```
1. 编辑内容（标题/正文/标签）
2. 管理媒体（添加/删除/说明/排序）
3. 预览效果
4. 选择平台并发布
5. 草稿管理
6. 帮助
0. 保存并退出
```

### 方式二：命令行工具

使用命令行快速发布：

```bash
# 模拟发布到所有平台
python publish.py -t "我的文章标题" -c "文章内容"

# 从文件读取内容
python publish.py -t "标题" -f article.md

# 指定平台发布
python publish.py -t "标题" -c "内容" -p wechat,zhihu

# 真实发布
python publish.py -t "标题" -c "内容" --real

# 带图片发布
python publish.py -t "标题" -c "内容" -i image1.jpg image2.jpg

# 详细输出
python publish.py -t "标题" -c "内容" -v
```

### 方式三：Python API

在代码中使用：

```python
from src.core.platform_manager import PlatformManager
from src.core.platform_base import PublishMode
from src.platforms.wechat import WechatPlatform
from src.platforms.zhihu import ZhihuPlatform
from src.platforms.bilibili import BilibiliPlatform
from src.platforms.xiaohongshu import XiaohongshuPlatform

# 创建管理器并注册平台
manager = PlatformManager()
manager.register(WechatPlatform(app_id="xxx", app_secret="xxx"))
manager.register(ZhihuPlatform())
manager.register(BilibiliPlatform(sess_data="xxx"))
manager.register(XiaohongshuPlatform())

# 发布内容
results = manager.publish_to_all(
    title="Python异步编程入门",
    content=open("article.md").read(),
    images=["cover.jpg"],
    mode=PublishMode.SIMULATE,  # 先模拟
)

# 查看结果
print(manager.get_summary(results))
```

### 媒体处理

```python
from src.media.image_processor import ImageProcessor, AspectRatio

processor = ImageProcessor()

# 获取图片信息
info = processor.get_image_info("photo.jpg")
print(info)  # 1920x1080 JPEG 2.50MB RGB

# 裁剪为正方形
processor.crop_to_ratio("photo.jpg", "square.jpg", AspectRatio.SQUARE)

# 压缩图片
processor.compress_image("large.jpg", "small.jpg", max_size_mb=1.0)

# 为平台自动处理
processor.prepare_for_platform("photo.jpg", "wechat", "wechat_ready.jpg")
```

### 草稿管理

```python
from src.draft.draft_manager import DraftManager

draft_mgr = DraftManager()

# 创建并保存草稿
draft = draft_mgr.new_draft(
    title="我的文章",
    content="# 标题\n\n内容...",
    tags=["Python", "教程"],
    category="技术",
)
draft_mgr.save_current(draft)

# 列出所有草稿
drafts = draft_mgr.list_drafts()

# 导出为Markdown
draft_mgr.export(draft.id, "output.md")
```

### 生成预览

```python
from src.review.previewer import Previewer

previewer = Previewer()

# 生成所有平台预览
results = previewer.generate_all_previews(
    title="文章标题",
    content="# 内容\n\n正文...",
    tags=["话题"],
)

print(results)
# {'wechat': 'previews/wechat_preview.html', ...}
```

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层                              │
│  ┌─────────────────┐  ┌──────────────────────────────────┐  │
│  │   app.py        │  │   publish.py                     │  │
│  │   (交互式程序)   │  │   (命令行工具)                    │  │
│  └────────┬────────┘  └───────────────┬──────────────────┘  │
│           │                           │                     │
├───────────┼───────────────────────────┼─────────────────────┤
│           │       核心业务层          │                     │
│  ┌────────▼───────────────────────────▼──────────────────┐  │
│  │              PlatformManager                          │  │
│  │              (平台管理器)                              │  │
│  └────────┬──────────────────────────────────────────────┘  │
│           │                                                 │
│  ┌────────▼────────┐  ┌─────────────┐  ┌────────────────┐  │
│  │  PlatformBase   │  │  DraftMgr   │  │  Previewer     │  │
│  │  (平台基类)     │  │  (草稿管理)  │  │  (预览系统)    │  │
│  └────────┬────────┘  └─────────────┘  └────────────────┘  │
│           │                                                 │
├───────────┼─────────────────────────────────────────────────┤
│           │         平台实现层                              │
│  ┌────────┼───────────────────────────────────────────┐    │
│  │        │                                           │    │
│  │  ┌─────▼─────┐  ┌────────┐  ┌──────────┐  ┌──────┐│    │
│  │  │  Wechat   │  │ Zhihu  │  │ Bilibili │  │ XHS  ││    │
│  │  │ 微信公众号 │  │  知乎  │  │   B站    │  │小红书 ││    │
│  │  └─────┬─────┘  └───┬────┘  └────┬─────┘  └──┬───┘│    │
│  │        │            │            │            │     │    │
│  └────────┼────────────┼────────────┼────────────┼─────┘    │
│           │            │            │            │          │
├───────────┼────────────┼────────────┼────────────┼──────────┤
│           │            │            │            │          │
│  ┌────────▼────────┐   │   ┌────────▼────────┐   │          │
│  │  ImageProcessor │   │   │ VideoProcessor  │   │          │
│  │  (图片处理器)   │   │   │ (视频处理器)    │   │          │
│  └─────────────────┘   │   └─────────────────┘   │          │
│                        │                         │          │
├────────────────────────┼─────────────────────────┼──────────┤
│                        │       API层             │          │
│  ┌─────────────────────▼─────────────────────────▼───────┐  │
│  │     WechatAPI              BilibiliAPI                 │  │
│  │     (微信API)              (B站API)                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
multi-platform-publisher/
├── app.py                    # 交互式主程序
├── publish.py                # 命令行工具
├── src/
│   ├── core/                 # 核心模块
│   │   ├── platform_base.py  # 平台基类、枚举、数据类
│   │   └── platform_manager.py # 平台管理器
│   ├── platforms/            # 平台实现
│   │   ├── wechat.py         # 微信公众号
│   │   ├── zhihu.py          # 知乎
│   │   ├── bilibili.py       # B站
│   │   └── xiaohongshu.py    # 小红书
│   ├── api/                  # API接口
│   │   ├── wechat_api.py     # 微信API
│   │   └── bilibili_api.py   # B站API
│   ├── media/                # 媒体处理
│   │   ├── image_processor.py # 图片处理器
│   │   ├── video_processor.py # 视频处理器
│   │   └── media_manager.py  # 媒体管理器
│   ├── draft/                # 草稿管理
│   │   └── draft_manager.py  # 草稿管理器
│   └── review/               # 预览系统
│       └── previewer.py      # 预览生成器
├── tests/                    # 测试文件
├── examples/                 # 示例文件
├── requirements.txt          # 依赖列表
├── .env.example              # 环境变量模板
└── README.md                 # 本文档
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_platform_base.py

# 带覆盖率
pytest tests/ --cov=src
```

## 🛠️ 开发指南

### 分支规范

- `main` - 主分支，始终保持可运行状态
- `feature/xxx` - 功能开发分支
- `fix/xxx` - Bug修复分支
- `docs/xxx` - 文档更新分支

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

### 代码规范

- 符合PEP8规范
- 添加类型注解
- 添加完整的docstring
- 每个功能都有对应的测试

## 🤝 贡献

欢迎提交Pull Request！请确保：
1. 每个PR只做一件事
2. 所有代码符合PEP8规范
3. 添加类型注解和docstring
4. 提交前运行测试

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢所有贡献者和以下开源项目：
- [Pillow](https://python-pillow.org/) - 图片处理
- [requests](https://requests.readthedocs.io/) - HTTP请求
- [markdown](https://python-markdown.github.io/) - Markdown处理
- [python-dotenv](https://github.com/theskumar/python-dotenv) - 环境变量管理
