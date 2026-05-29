# Multi-Platform Publisher

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

一个支持多平台内容发布的Python工具，支持微信公众号、知乎、B站、小红书等平台的一键发布。

## 功能特性

- 🚀 **一键多平台发布** - 同时发布到微信公众号、知乎、B站、小红书
- 📝 **内容自适应** - 自动适配各平台的标题长度、内容格式限制
- 🖼️ **媒体处理** - 支持图片和视频的上传与处理
- 📁 **草稿管理** - 支持草稿保存和版本管理
- 👁️ **发布预览** - 发布前预览各平台的最终效果
- 🔌 **可扩展架构** - 轻松添加新平台支持

## 支持平台

| 平台 | 状态 | 标题限制 | 内容限制 | 图片限制 |
|------|------|----------|----------|----------|
| 微信公众号 | ✅ | 64字 | 富文本 | 10张 |
| 知乎 | ✅ | 60字 | 20000字 | 30张 |
| B站 | ✅ | 80字 | 15000字 | 100张 |
| 小红书 | ✅ | 20字 | 1000字 | 9张 |

## 安装方法

### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/multi-platform-publisher.git
cd multi-platform-publisher

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的平台凭证
```

## 使用示例

### 基本使用

```python
from src.core.platform_manager import PlatformManager
from src.platforms.wechat import WechatPlatform
from src.platforms.zhihu import ZhihuPlatform

# 创建管理器
manager = PlatformManager()

# 注册平台
manager.register(WechatPlatform())
manager.register(ZhihuPlatform())

# 发布内容
result = manager.publish_to_all(
    title="我的第一篇文章",
    content="# Hello World\n\n这是文章内容。",
    images=["image1.jpg", "image2.jpg"]
)

print(result)
```

### 使用草稿

```python
from src.draft.draft_manager import DraftManager

# 创建草稿管理器
draft_mgr = DraftManager()

# 保存草稿
draft_id = draft_mgr.save(
    title="草稿标题",
    content="草稿内容"
)

# 加载草稿
draft = draft_mgr.load(draft_id)
```

### 发布预览

```python
from src.review.preview import Preview

# 创建预览
preview = Preview(platform_manager)
html = preview.generate(
    title="文章标题",
    content="文章内容",
    platform="wechat"
)
```

## 项目结构

```
multi-platform-publisher/
├── src/
│   ├── core/           # 核心模块
│   │   ├── platform_base.py    # 平台基类
│   │   └── platform_manager.py # 平台管理器
│   ├── platforms/      # 平台实现
│   │   ├── wechat.py
│   │   ├── zhihu.py
│   │   ├── bilibili.py
│   │   └── xiaohongshu.py
│   ├── media/          # 媒体处理
│   ├── draft/          # 草稿管理
│   ├── review/         # 预览功能
│   └── api/            # API接口
├── tests/              # 测试文件
├── examples/           # 使用示例
├── requirements.txt    # 依赖列表
├── .env.example        # 环境变量模板
└── README.md          # 本文档
```

## 开发指南

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

### 运行测试

```bash
pytest tests/
```

## 贡献

欢迎提交Pull Request！请确保：
1. 每个PR只做一件事
2. 所有代码符合PEP8规范
3. 添加类型注解和docstring
4. 提交前运行测试

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
