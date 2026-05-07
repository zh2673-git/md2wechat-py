# 公众号发布

当用户需要写公众号文章、排版、配图或发布时，使用以下规则：

## 可用命令
- `wechat-pub inspect <file>` — 检查文章
- `wechat-pub preview <file>` — 预览排版
- `wechat-pub convert <file> [--draft]` — 转换/发布
- `wechat-pub layout list --serves <name>` — 排版模块
- `wechat-pub generate_cover --article <file>` — 封面图
- `wechat-pub humanize <file>` — AI 去痕

## 工作流
1. 检查：`inspect article.md`
2. 预览：`preview article.md`
3. 发布：`convert article.md --draft --cover cover.jpg`
