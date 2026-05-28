# 公众号发布完整工作流

> 用户提供任意内容 → 判断类型并改写 → 排版配图 → 推送微信草稿箱

---

## 步骤0：扫描输入源

检查当前目录下 `data/` 文件夹是否存在，存在则按分组规则批量处理。

### data/ 文件夹批量模式

```
data/
├── 话题A/              ← 子文件夹 → 合并为1篇文章
│   ├── 01_intro.md
│   ├── 02_detail.md
│   └── 03_summary.md
├── 话题B/              ← 子文件夹 → 合并为1篇文章
├── 独立笔记1.md        ← 直接的 .md 文件 → 各生成1篇文章
└── 独立笔记2.md
```

---

## 步骤1：判断输入类型

| 输入类型 | 特征 | 输出策略 |
|---------|------|---------|
| 完整文章 | 有标题、段落分明、结构完整 | 单输出，跳过改写 |
| AI聊天记录 | 多轮人机对话、有"你"/"我"交替、口语化 | **双输出**：对话整理版 + 论文风格版 |
| 笔记文件 | 有结构化标题和要点、非对话形式 | 单输出，论文风格版 |
| 零散想法 | 只有要点或片段、缺结构 | 单输出，论文风格版 |

---

## 步骤2：根据类型决定输出策略

- AI聊天记录 → 生成两个版本（对话整理版 + 论文风格版）
- 笔记/零散想法 → 生成一个版本（论文风格版）
- 完整文章 → 直接进入排版（跳过改写）

---

## 步骤3：风格改写

详见 [references/writing-style-guide.md](../references/writing-style-guide.md)

### 论文风格版改写规则

1. 按「引言/背景 → 核心论点（2-4个）→ 深度分析 → 结论/展望 → 参考文献」五段式组织
2. 提炼论点，每个论点独立成节
3. 去口语化，用书面语替代
4. 补充论证逻辑，但不加虚构内容
5. 专业概念保留术语但加通俗解释
6. 引用标注来源
7. 文末附参考文献列表

### 对话风格版改写规则

1. 保留对话骨架，保持 Q&A 结构
2. 去口语化冗余
3. 精简寒暄
4. 合并相关问答
5. 保留追问深度
6. 标注角色：**「我：」** / **「AI：」**

---

## 步骤3.5：材料验证与引用溯源

详见 [references/fact-checking.md](../references/fact-checking.md)

---

## 步骤4：分析文章结构，用原生 Markdown 增强排版

详见 [references/wechat-formatting.md](../references/wechat-formatting.md)

**核心约束**：
- 禁止使用 :::block 容器模块
- 正文不用 # H1
- 优先原生 Markdown 语法
- emoji + 加粗辅助视觉

---

## 步骤4.5：分析文章内容，自动生成配图并插入对应位置

详见 [references/image-generation.md](../references/image-generation.md)

**配图要求**：
- 每个主要章节开头放一张配图
- 每篇文章至少5张配图
- 静态结构用SVG→PNG，变化过程用Canvas→GIF
- 论文风格版优先配图，对话风格版一般不配图

---

## 步骤5：检查文章

```bash
wechat-pub inspect article.md --json
```

---

## 步骤6：字数检查

| 指标 | 目标值 |
|------|--------|
| 纯文本字数 | 7000-8000字 |
| 总字符数（含HTML/图片标签） | 19000-20000字符 |

**扩充技巧**：补充类比、添加反例、延伸应用、引入对比、操作细化

---

## 步骤7：生成封面

```bash
wechat-pub generate-cover --article article.md --format png --json
```

---

## 步骤8：转换+推送

```bash
wechat-pub publish article.md --auto-cover --author "公众号名"
```

---

## 快速排版（不推送）

```bash
wechat-pub inspect article.md --json
wechat-pub preview article.md
wechat-pub convert article.md -o output.html
```

---

## 图片处理

```bash
wechat-pub providers list --json
wechat-pub prompts list --kind image --json
wechat-pub generate-cover --article article.md
wechat-pub generate-infographic --article article.md --preset <name>
wechat-pub upload-image <file>
```
