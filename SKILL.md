---
name: 公众号发布
description: 将 Markdown 文章（或零散内容）按公众号风格改写、转换为微信公众号排版并推送草稿箱。Agent 自动用原生 Markdown 排版、自动生成并插入配图、生成封面、推送微信草稿箱。当用户需要写公众号文章、排版或推送时激活此技能。
---

# 公众号发布 Skill

> 用户提供任意内容（完整文章 / 聊天记录 / 零散想法 / 笔记文件）→ Agent 判断类型并改写 → 自动用原生 Markdown 增强排版 → 自动用 SVG/AI 生成配图并插入 → 生成封面 → 推送微信草稿箱

---

## 核心流程

```
步骤0：扫描输入源，确定文章分组
步骤1：对每个分组分别处理——判断输入类型（完整文章 / AI聊天记录 / 笔记 / 零散想法）
步骤2：根据类型决定输出策略：
       - AI聊天记录 → 生成两个版本（对话整理版 + 论文风格版）
       - 笔记/零散想法 → 生成一个版本（论文风格版）
       - 完整文章 → 直接进入排版（跳过改写）
步骤3：对每个版本分别进行风格改写
步骤3.5：材料验证与引用溯源
步骤4：分析文章结构，用原生 Markdown 增强排版
步骤4.5：分析文章内容，自动生成配图并插入对应位置
步骤5：检查文章  →  wechat-pub inspect article.md --json
步骤6：字数检查   →  确认纯文本字数在7000-8000字之间，总字符在19000-20000之间
步骤7：生成封面   →  wechat-pub generate-cover --article article.md --format png --json
步骤8：转换+推送  →  wechat-pub publish article.md --auto-cover --author "公众号名"
```

**详细工作流** → [workflows/wechat-publishing.md](workflows/wechat-publishing.md)

---

## 核心概念（速览）

| 概念 | 一句话 | 详见 |
|-----|--------|------|
| **写作风格规范** | 真实、自然、不端着，禁止AI味 | [references/writing-style-guide.md](references/writing-style-guide.md) |
| **微信安全排版** | 只用原生Markdown，禁用:::block | [references/wechat-formatting.md](references/wechat-formatting.md) |
| **配图方案** | SVG→PNG首选，Canvas→GIF动态，AI生图备选 | [references/image-generation.md](references/image-generation.md) |
| **材料验证** | 引用必须真实，出处必须可查 | [references/fact-checking.md](references/fact-checking.md) |
| **字数约束** | 纯文本7000-8000字，总字符19000-20000 | [workflows/wechat-publishing.md](workflows/wechat-publishing.md) |

---

## Agent 规则

1. **优先扫描 data/ 文件夹**：检查当前目录下 `data/` 文件夹是否存在，存在则按分组规则批量处理
2. **再判断输入类型**：完整文章跳过改写，AI聊天记录双输出，笔记/零散想法单输出
3. **批量逐篇处理**：多篇文章逐篇执行步骤1-7，每篇独立改写、排版、推送
4. **⚠️ 字数优化约束**：纯文本7000-8000字，总字符19000-20000。充分展开是硬约束，禁止过度精简
5. **双输出处理**：AI聊天记录需要生成两个独立的 Markdown 文件，分别推送两个草稿
6. **风格区分**：对话整理版和论文风格版使用不同的改写规则和语言风格
7. **自动增强排版**：用微信原生语法增强排版。**禁止使用 :::block 容器模块**
8. **自动生成配图（图文并茂是硬要求）**：每个主要章节开头放一张配图，每篇文章至少5张配图。静态结构用PNG，变化过程用GIF
9. **先 inspect 再操作**：排版和配图完成后，先 inspect --json 确认无 error
10. **先 capabilities**：不确定命令是否存在时，先执行 capabilities --json
11. **排版适量，内容优先**：以"对读者有用"为标准，不堆砌样式模块
12. **草稿需要封面**：没有封面时用 --auto-cover 自动生成
13. **摘要自动生成**：不需要手动指定 digest
14. **JSON 输出**：Agent 调用 CLI 时始终加 --json（publish 命令除外）
15. **确认后再推送**：先 preview 让用户确认效果，再 publish
16. **微信凭证安全**：配置文件在 ~/.config/wechat-pub/config.yaml，不在项目目录内
17. **避免 AI 味**：严格遵循语言风格规范中的禁用表达列表
18. **文件存放**：改写稿统一保存在 `output/` 文件夹下
19. **data/ 文件夹不提交**：`data/` 是临时输入目录

---

## 安装

```bash
pip install md2wechat-py
```

如需 Canvas 动画录制 GIF 功能：

```bash
pip install md2wechat-py[gif]
playwright install chromium
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
| `wechat-pub generate-cover --article article.md --format png --json` | 生成封面 |
| `wechat-pub record-gif animation.html -o output/images/demo.gif` | Canvas动画录制GIF |
| `wechat-pub publish article.md --auto-cover --author "公众号名"` | 一键排版+封面+推送草稿 |
| `wechat-pub upload-image cover.png --type thumb --json` | 上传图片到微信素材库 |
| `wechat-pub layout list --json` | 查看排版模块列表 |
| `wechat-pub config init` | 初始化微信凭证配置 |
| `wechat-pub capabilities --json` | 查看 CLI 能力 |

---

## 主题

| 主题名 | 风格 |
|--------|------|
| `claude-warm` | 暖阳：赭石橙+奶油白（默认，推荐） |
| `claude-clean` | 极简：白底+赭石点缀 |
| `claude-dark` | 暗夜：深色暖棕调 |

---

## 文件结构

```
md2wechat-py/
├── SKILL.md                              # 本文件（主入口）
├── references/                           # 参考文档
│   ├── writing-style-guide.md            # 写作风格规范
│   ├── wechat-formatting.md              # 微信排版规范
│   ├── image-generation.md               # 配图方案
│   └── fact-checking.md                  # 材料验证与引用溯源
├── workflows/                            # 工作流
│   └── wechat-publishing.md              # 公众号发布完整工作流
└── design/                               # 源码（Python CLI 工具）
```
