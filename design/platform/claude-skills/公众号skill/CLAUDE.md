# 公众号发布工具 - Claude Code 工作指南

本工具提供 `wechat-pub` CLI，用于将 Markdown 文章转换为微信公众号排版并推送草稿箱。

## Core Commands

### Discovery First
```bash
wechat-pub version
wechat-pub capabilities --json
wechat-pub themes list --json
wechat-pub providers list --json
wechat-pub layout list --json
```

### Conversion
```bash
wechat-pub inspect article.md --json
wechat-pub preview article.md
wechat-pub convert article.md --preview
wechat-pub convert article.md -o output.html
wechat-pub convert article.md --draft --cover cover.jpg
```

### Layout Modules
```bash
wechat-pub layout list --serves attention --json
wechat-pub layout show hero --json
wechat-pub layout render hero --var title="标题" --var eyebrow="观察"
wechat-pub layout validate --file article.md --json
```

### Image Generation
```bash
wechat-pub generate_cover --article article.md
wechat-pub generate_infographic --article article.md --preset infographic-timeline
wechat-pub upload_image photo.jpg
```

### AI Humanize
```bash
wechat-pub humanize article.md
wechat-pub humanize article.md --intensity gentle
wechat-pub humanize article.md --intensity aggressive
```

## Metadata Rules
- Title: `--title` > frontmatter title > first H1 > "未命名文章"
- Author: `--author` > frontmatter author
- Digest: `--digest` > frontmatter digest/summary/description
- Title max 64 chars, Author max 16 chars, Digest max 128 chars

## Agent Rules
1. Start with discovery before selecting providers/themes/prompts
2. Prefer confirm-first flow: `inspect → preview → convert --draft`
3. Layout modules: max 1 per purpose, 3-5 total per article
4. Draft requires cover (`--cover` or `--cover-media-id`)
