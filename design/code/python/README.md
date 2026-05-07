# wechat-pub — Claude 风格公众号排版 CLI

Markdown → 微信公众号 HTML，支持 6 个排版模块和 3 套 Claude 风格主题。

## 安装

```bash
pip install -e .
```

依赖：`click`, `markdown-it-py`, `pyyaml`, `jinja2`, `httpx`

## 快速开始

```bash
# 查看能力
wechat-pub capabilities --json

# 转换为 HTML
wechat-pub convert article.md -o output.html

# 一键发布
wechat-pub publish article.md --auto-cover --json

# 生成封面
wechat-pub generate-cover --article article.md --format png --json
```

## :::block 排版模块

在 Markdown 中用 `:::block name ... :::` 插入排版模块：

```markdown
:::hero
eyebrow: 排版新思维
title: 为什么你的公众号文章读者读不完
subtitle: 不是内容不好，是手机上 3 秒没给读者理由继续
:::

:::callout
type: tip
body: 排版不是让文章"好看"，而是让读者更容易做出"继续读"的决定。
:::

:::verdict
eyebrow: 核心理念
title: 排版的本质不是审美，而是降低读者的决策成本
body: 每一次在手机上阅读，读者都在做决策：继续还是划走。
:::

:::cta
title: 从今天开始用模块化排版
button_text: 安装 wechat-pub
button_url: "#"
:::
```

## 主题

| 主题名 | 风格 |
|--------|------|
| `claude-warm`（默认） | 暖阳：赭石橙 + 奶油白 |
| `claude-clean` | 极简：白底 + 赭石点缀 |
| `claude-dark` | 暗夜：深色暖棕调 |

## 微信配置

```bash
wechat-pub config init    # 交互式配置
# 或设置环境变量 WECHAT_APP_ID / WECHAT_APP_SECRET
```

## 项目结构

```
wechat_pub/
├── cli/                  # CLI 命令
│   ├── main.py           #   主入口 + publish
│   ├── convert.py        #   convert 命令
│   ├── inspect.py        #   inspect / preview
│   ├── layout.py         #   layout 子命令
│   ├── cover.py          #   封面生成/上传
│   └── config.py         #   配置管理
├── engine/               # 核心引擎
│   ├── converter.py      #   Markdown → HTML 转换器
│   ├── layout_renderer.py#   :::block 渲染引擎
│   ├── inline_styler.py  #   内联样式注入器（微信兼容）
│   ├── theme_manager.py  #   主题管理器
│   └── image_engine.py   #   封面图生成引擎
├── wechat/               # 微信 API 客户端
├── layout/               # 6 个排版模块 YAML 定义
└── templates/            # 6 个 Jinja2 HTML 模板
```

## 许可

MIT License
