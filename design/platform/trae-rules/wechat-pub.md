# 公众号发布工具 - Trae 规则

本项目提供 `wechat-pub` CLI 工具，用于微信公众号内容创作。

## 核心能力

| 命令 | 说明 |
|------|------|
| `wechat-pub inspect <file>` | 检查文章发布准备状态 |
| `wechat-pub preview <file>` | 本地预览排版 |
| `wechat-pub convert <file> [-o output] [--draft] [--cover path]` | 转换 HTML / 推送草稿 |
| `wechat-pub layout list/show/render/validate` | 排版模块管理 |
| `wechat-pub generate_cover --article <file>` | AI 生成封面 |
| `wechat-pub generate_infographic --article <file> --preset <name>` | AI 生成信息图 |
| `wechat-pub humanize <file>` | AI 去痕 |
| `wechat-pub capabilities --json` | 查看所有可用能力 |

## 工作流

### 用户说"发布文章"
执行：`inspect → preview → convert --draft`

### 用户说"排版这篇文章"
1. 检查文章中是否有 `:::block` 语法
2. 执行 `layout validate --file article.md`
3. 执行 `convert article.md --preview`

### 用户说"配图"
1. `providers list --json` 发现可用 AI 图片服务
2. `generate_cover --article article.md`
3. 可选：`generate_infographic --article article.md --preset infographic-timeline`

### 用户说"去除AI痕迹"
执行：`humanize article.md`

## 排版模块原则
- hero 1个 / verdict 1个 / cta 1个
- 按 4 件事选：attention + readability + memorability + conversion
- 每类最多 1 个，一篇文章 3-5 个模块
