# md2wechat-py

> 写纯 Markdown，AI 自动排版增强，一键推送微信公众号草稿箱。

[English](#english) | 中文

## 为什么做这个工具

一直想写公众号，但每次都被排版劝退：

- 微信编辑器难用，格式经常错乱
- 135Editor 等工具要手动拖拽，改一处全局重排
- Markdown 写完还得复制粘贴再调格式
- 封面图、摘要、推送……每个环节都是手工活

所以做了这个工具：**用 Markdown 写完，一条命令直接进草稿箱**。

## 它能做什么

```
你的 Markdown 文稿（或 AI 聊天记录 / 零散笔记）
       ↓
Agent 自动判断内容类型（完整文章 / AI聊天记录 / 笔记 / 零散想法）
       ↓
AI聊天记录 → 双输出：对话整理版 + 论文风格版
笔记/零散想法 → 单输出：论文风格版
       ↓
Agent 自动分析内容，插入 :::block 排版模块（hero / callout / verdict / cta 等）
       ↓
wechat-pub inspect article.md --json          ← 检查文章状态
       ↓
wechat-pub generate-cover --article article.md --format png --json  ← 生成封面
       ↓
wechat-pub publish article.md --auto-cover --json   ← 推送草稿箱
       ↓
微信公众号草稿箱中出现排版精美的文章 ✅
```

## 核心特性

- **Claude 风格排版**：3 套精心调校的主题（暖阳 / 极简 / 暗夜），赭石橙+奶油白的经典配色
- **6 个排版模块**：hero、callout、verdict、toc、faq、cta —— 自动插入，无需手写
- **纯内联样式**：微信公众号会删除 `<style>` 标签，本工具将所有样式以 inline style 注入，保证渲染一致
- **AI 配图**：自动生成占位封面，也可接入 AI 绘画
- **一键推送**：从 Markdown 到微信草稿箱，一条命令
- **Agent 原生**：所有命令支持 `--json` 输出，AI IDE 可直接调用
- **多文件批量处理**：支持 `data/` 文件夹批量扫描，子文件夹合并、独立文件分别生成
- **AI聊天记录双输出**：自动识别聊天记录，同时生成对话整理版和论文风格版
- **规范化输出目录**：生成的改写稿统一保存到 `output/` 文件夹

## 快速开始

### 安装

```bash
cd design/code/python
pip install -e .
wechat-pub version   # 验证安装
```

### 配置微信凭证

```bash
# 交互式配置（配置文件在 ~/.config/wechat-pub/config.yaml）
wechat-pub config init

# 或使用环境变量
export WECHAT_APP_ID=你的AppID
export WECHAT_APP_SECRET=你的AppSecret
```

获取 AppID/AppSecret：登录[微信公众平台](https://mp.weixin.qq.com) → 开发 → 基本配置。

### 使用方式一：配合 AI Agent（推荐）

你只需要在 `data/` 文件夹中放入 Markdown 笔记或 AI 聊天记录，Agent 自动完成类型判断、改写、排版、配图和推送。

支持批量处理：

```
data/
├── 话题A/              ← 子文件夹 → 合并为1篇文章
│   ├── 01_intro.md
│   ├── 02_detail.md
│   └── 03_summary.md
├── 独立笔记.md          ← 直接 .md 文件 → 各生成1篇
└── chat_with_ai.md     ← AI聊天记录 → 自动生成对话版+论文版两篇
```

支持：CodeBuddy、Claude Code、Trae、Cursor 等 AI IDE。

Skill 定义在项目根目录 `SKILL.md`（自动安装到 `.codebuddy/skills/公众号skill/SKILL.md`）。

### 使用方式二：命令行

```bash
# 转换为 HTML
wechat-pub convert article.md -o output.html

# 一键发布（排版 + 封面 + 推送草稿箱）
wechat-pub publish article.md --auto-cover

# 本地预览
wechat-pub preview article.md

# 生成封面
wechat-pub generate-cover --article article.md --format png -o cover.png

# 检查文章发布准备状态
wechat-pub inspect article.md --json
```

## CLI 命令一览

| 命令 | 用途 |
|------|------|
| `convert` | Markdown → HTML |
| `publish` | 一键发布（排版+配图+草稿） |
| `inspect` | 检查文章发布准备状态 |
| `preview` | 本地预览排版效果 |
| `generate-cover` | 生成封面图 |
| `upload-image` | 上传图片到微信素材库 |
| `layout list` | 查看排版模块 |
| `layout show` | 查看模块详情 |
| `layout validate` | 验证 :::block 语法 |
| `config init` | 配置微信凭证 |
| `config show` | 查看当前配置 |
| `capabilities` | 查看 CLI 能力 |

所有命令支持 `--json` 输出。

## 排版模块

Agent 会根据内容结构自动插入排版模块，你不需要手写：

```markdown
:::hero
eyebrow: 物权法专题
title: 地下车库的产权到底归谁
subtitle: 从学说分歧到制度逻辑的系统梳理
:::

:::callout
type: tip
body: 提示内容
:::

:::verdict
eyebrow: 核心理念
title: 排版的本质不是审美，而是降低读者的决策成本
body: 详细说明
:::
```

| 模块 | 分类 | 用途 |
|------|------|------|
| `hero` | 开场 | 首屏大标题 + 副标题 |
| `callout` | 提示 | tip / warning / info 提示块 |
| `verdict` | 判断 | 核心观点卡片 |
| `toc` | 目录 | 文章目录列表 |
| `faq` | 问答 | 常见问题折叠 |
| `cta` | 转化 | 行动号召按钮 |

**使用原则**：一篇文章不超过 5 个模块，hero + verdict + cta 是标配，其余按需。

## 主题

| 主题名 | 风格 | 色系 |
|--------|------|------|
| `claude-warm` | 暖阳（默认） | 赭石橙 + 奶油白 |
| `claude-clean` | 极简 | 白底 + 赭石点缀 |
| `claude-dark` | 暗夜 | 深色暖棕调 |

## 项目结构

```
design/code/python/
├── wechat_pub/
│   ├── cli/                # CLI 命令（publish/convert/inspect/...）
│   ├── engine/             # 核心排版引擎
│   │   ├── converter.py    #   Markdown → HTML 转换器
│   │   ├── layout_renderer.py  # :::block 渲染引擎
│   │   ├── inline_styler.py    # 内联样式注入器（微信兼容）
│   │   ├── theme_manager.py    # 主题管理器
│   │   └── image_engine.py     # 封面图生成引擎
│   ├── wechat/             # 微信 API 客户端
│   ├── layout/             # 6 个排版模块 YAML 定义
│   └── templates/          # 6 个 Jinja2 HTML 模板
├── 地下车库产权之谜.md       # 示例文章
├── pyproject.toml
└── setup.py
```

## 技术细节

### 为什么用内联样式？

微信公众号编辑器会**删除 `<style>` 标签和 `class` 属性**，导致 CSS 类样式完全失效。本工具将所有排版样式以 `style=""` 属性逐元素注入，确保在微信中渲染一致。

### HTML 压缩

微信对文章内容有 20000 字符限制。内联样式比 CSS 类更长，因此本工具内置 HTML 压缩：移除注释、压缩多行 style 为单行、去除多余空白。

## 相关项目

- **[essence-programming](https://github.com/zh2673-git/essence-programming)** — 本质探索方法论，本工具诞生过程中使用的思维框架

## 许可

MIT License

---

<a id="english"></a>

# md2wechat-py

> Write pure Markdown, AI auto-enhances layout, one-click publish to WeChat Official Account drafts.

## Why This Tool

I always wanted to write for WeChat Official Accounts, but the formatting process kept stopping me:

- WeChat's editor is clunky, formats break easily
- Tools like 135Editor require manual drag-and-drop
- After writing in Markdown, you still have to copy-paste and reformat
- Cover images, summaries, publishing... every step is manual

So I built this tool: **write in Markdown, one command to draft**.

## Features

- **Claude-style layout**: 3 carefully tuned themes (warm / clean / dark)
- **6 layout modules**: hero, callout, verdict, toc, faq, cta — auto-inserted
- **Pure inline styles**: WeChat strips `<style>` tags; we inject inline styles for consistent rendering
- **AI cover**: Auto-generate placeholder covers, or integrate AI image generation
- **One-click publish**: From Markdown to WeChat draft in one command
- **Agent-native**: All commands support `--json` output for AI IDE integration

## Quick Start

```bash
cd design/code/python
pip install -e .
wechat-pub config init    # Configure WeChat credentials
wechat-pub publish article.md --auto-cover --json
```

## License

MIT License
