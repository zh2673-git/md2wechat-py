# wechat-pub MCP Server

通过 MCP (Model Context Protocol) 协议，让任何支持 MCP 的 IDE 都能调用公众号发布工具的排版、配图和推送能力。

## 支持的 IDE

- **Trae** — 在设置中添加 MCP Server
- **Cursor** — 在 `.cursor/mcp.json` 中配置
- **VS Code + GitHub Copilot** — 编辑 `~/.vscode/mcp.json`
- **Claude Desktop** — 编辑 `claude_desktop_config.json`

## 安装

```bash
pip install wechat-pub
```

## 配置

在每个 IDE 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "wechat-pub": {
      "command": "python",
      "args": ["-m", "wechat_pub.mcp_server"],
      "env": {
        "WECHAT_APPID": "your_app_id",
        "WECHAT_SECRET": "your_app_secret"
      }
    }
  }
}
```

## 可用工具

| 工具名 | 说明 | 参数 |
|--------|------|------|
| `convert` | Markdown → HTML | markdown, theme, output |
| `inspect` | 检查文章 | markdown_file |
| `publish_draft` | 推送草稿 | md_file, cover, title, author |
| `generate_cover` | 生成封面 | article_file, title, summary |
| `layout_list` | 列出排版模块 | serves |
| `layout_validate` | 验证排版语法 | markdown_file |
