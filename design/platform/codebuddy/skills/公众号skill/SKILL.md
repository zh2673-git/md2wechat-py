---
name: 公众号发布
description: 将 Markdown 文章转换为 Claude 风格微信公众号排版并推送草稿箱。Agent 自动为纯 Markdown 内容插入 :::block 排版模块（hero/toc/callout/verdict/faq/cta）、生成封面、推送微信草稿箱。当用户需要写公众号文章、排版或推送时激活此技能。
---

# 公众号发布 Skill

> 用户提供纯 Markdown → Agent 自动加 :::block 增强排版 → 生成封面 → 推送微信草稿箱

## 核心流程（用户只写 Markdown，Agent 负责排版）

**用户只需要写纯 Markdown 文本**，不需要手写任何 `:::block` 语法。Agent 会自动分析内容结构，为文章插入合适的排版模块。

### Agent 完整执行步骤

```
步骤1：接收用户纯 Markdown 内容，保存为 .md 文件
步骤2：分析文章结构，自动插入 :::block 排版模块
步骤3：检查文章  →  wechat-pub inspect article.md --json
步骤4：生成封面   →  wechat-pub generate-cover --article article.md --format png --json
步骤5：转换+推送  →  wechat-pub publish article.md --auto-cover --json
```

### 步骤2详解：如何自动添加 :::block

Agent 读取用户 Markdown 后，根据内容结构自动插入排版模块。规则如下：

#### 插入规则

| 条件 | 插入模块 | 位置 |
|------|---------|------|
| 文章有标题/H1 | `:::block hero` | 文章最开头（frontmatter 之后） |
| 文章有小标题段落，且有核心观点 | `:::block verdict` | 核心观点段落处 |
| 文章有提示/注意/警告性质的内容 | `:::block callout` | 提示内容处 |
| 文章有3个以上小节 | `:::block toc` | hero 之后、正文之前 |
| 文章末尾需要行动号召 | `:::block cta` | 文章末尾 |
| 文章有问答内容 | `:::block faq` | 问答段落处 |

#### 排版模块语法（三个冒号，不是四个）

```markdown
:::block hero
eyebrow: 简短分类标签
title: 文章主标题
subtitle: 一句话副标题
:::

:::block callout
type: tip
body: 提示内容文字
:::

:::block verdict
eyebrow: 标签
title: 核心判断句
body: 展开说明
:::

:::block toc
items:
  - 目录项1
  - 目录项2
:::

:::block faq
items:
  - question: 问题？
    answer: 回答。
:::

:::block cta
title: 行动号召标题
button_text: 按钮文字
button_url: https://example.com
:::
```

也可简写为 `:::hero` （省略 `block` 关键字）。

#### 示例：纯 Markdown → 增强后

**用户写的原始 Markdown：**
```markdown
## 为什么你的文章读者读不完

你有没有花了一整天写的好文章，发出去后阅读量惨淡？

问题可能不是内容，而是排版。好的排版要在 3 秒内让读者决定继续读。

## 排版的核心

排版的本质不是审美，而是降低读者的决策成本。每一次在手机上阅读，读者都在做决策：继续还是划走。

## 开始行动

从今天开始重构你的公众号文章吧。
```

**Agent 自动增强后：**
```markdown
:::block hero
eyebrow: 排版思维
title: 为什么你的文章读者读不完
subtitle: 不是内容不好，是手机上3秒没给读者理由继续
:::

你有没有花了一整天写的好文章，发出去后阅读量惨淡？

:::block callout
type: tip
body: 排版不是让文章"好看"，而是让读者更容易做出"继续读"的决定。
:::

## 排版的核心

:::block verdict
eyebrow: 核心理念
title: 排版的本质不是审美，而是降低读者的决策成本
body: 每一次在手机上阅读，读者都在做决策：继续还是划走。排版要做的是让"继续"这个决策更容易。
:::

## 开始行动

:::block cta
title: 从今天开始，重构你的公众号文章
button_text: 立即开始
button_url: #
:::
```

#### 模块使用原则

- **不超过 5 个**：一篇文章 hero 1个 + verdict 1个 + cta 1个 足够，callout 0-2个
- **hero 必有**：每篇文章开头都需要一个 hero
- **cta 必有**：文章末尾引导行动
- **verdict 最多 1 个**：一篇文章只有一个核心判断
- **不重复**：同类型模块不重复出现

## 安装

```bash
cd d:\self_test\project\codebuddy\公众号skill\design\code\python
pip install -e .
```

## 使用前必做

```bash
wechat-pub capabilities --json    # 确认 CLI 可用
wechat-pub config init             # 配置微信凭证
```

## CLI 命令速查

| 命令 | 用途 |
|------|------|
| `wechat-pub inspect article.md --json` | 检查文章准备状态 |
| `wechat-pub convert article.md -o output.html` | 仅转换 HTML |
| `wechat-pub preview article.md` | 本地预览 |
| `wechat-pub generate-cover --article article.md --format png --json` | 生成占位封面 |
| `wechat-pub publish article.md --auto-cover --json` | 一键排版+封面+推送草稿 |
| `wechat-pub upload-image cover.png --type thumb --json` | 上传图片到微信素材库 |
| `wechat-pub layout list --json` | 查看排版模块列表 |
| `wechat-pub layout show hero --json` | 查看某个模块详情 |
| `wechat-pub config init` | 初始化微信凭证配置 |
| `wechat-pub config show` | 查看当前配置 |
| `wechat-pub capabilities --json` | 查看 CLI 能力 |

## Agent 规则

1. **自动增强排版**：用户只需提供纯 Markdown，Agent 负责分析内容并自动插入 `:::block` 排版模块
2. **先 inspect 再操作**：增强完 `:::block` 后，先 `inspect --json` 确认无 error
3. **先 capabilities**：不确定命令是否存在时，先执行 `capabilities --json`
4. **模块不超过 5 个**：hero + verdict + cta 是标配，callout 按需
5. **草稿需要封面**：没有封面时用 `--auto-cover` 自动生成占位封面
6. **摘要自动生成**：不需要手动指定 digest，微信会自动截取
7. **JSON 输出**：Agent 调用 CLI 时始终加 `--json`，便于解析
8. **确认后再推送**：先 preview 让用户确认效果，再 publish
9. **微信凭证安全**：配置文件在 `~/.config/wechat-pub/config.yaml`，不在项目目录内，不会随代码提交

## 主题

| 主题名 | 风格 |
|--------|------|
| `claude-warm` | 暖阳：赭石橙+奶油白（默认，推荐） |
| `claude-clean` | 极简：白底+赭石点缀 |
| `claude-dark` | 暗夜：深色暖棕调 |

## 关于封面

- `generate-cover` 生成**占位封面**（标题文字 + 背景色），不是 AI 绘画
- 如需 AI 配图，Agent 可用 `image_gen` 工具生成，然后 `publish --cover 图片.png` 指定

## 微信公众号配置

1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入「开发 → 基本配置」→ 获取 AppID 和 AppSecret
3. 将服务器 IP 加入白名单（或使用测试号）
4. 运行 `wechat-pub config init`，配置文件在 `~/.config/wechat-pub/config.yaml`
5. 或设置环境变量：`WECHAT_APP_ID` / `WECHAT_APP_SECRET`

**安全说明**：配置文件存储在用户主目录 `~/.config/wechat-pub/` 下，不在项目目录内，推送到 GitHub 不会暴露凭证。

**测试号**：如需测试，可在「开发 → 开发者工具」申请测试号，不受 IP 白名单限制。
