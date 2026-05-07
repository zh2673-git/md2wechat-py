# 公众号发布工具 - Go 核心引擎骨架

Go 版本适用于生产环境部署，产生单二进制可执行文件。

## 项目结构

```
wechat-pub-go/
├── cmd/wechat-pub/
│   ├── main.go              # 主入口 + JSON envelope
│   ├── convert.go           # convert 命令
│   ├── inspect.go           # inspect 命令
│   ├── preview.go           # preview 命令
│   ├── layout.go            # layout 命令
│   ├── image.go             # image 命令
│   └── config.go            # config 命令
├── internal/
│   ├── engine/
│   │   ├── converter.go     # MD→HTML 转换
│   │   ├── layout.go        # :::block 渲染
│   │   └── theme.go         # 主题管理
│   ├── wechat/
│   │   ├── client.go        # 微信 API
│   │   ├── draft.go         # 草稿适配
│   │   └── material.go      # 素材上传
│   ├── image/
│   │   ├── provider.go      # 图片 provider 接口
│   │   └── upload.go        # 上传
│   └── model.go             # 统一模型
├── go.mod
├── Makefile
└── README.md
```

## 与 Python 版本的关系

| 版本 | 用途 | 开发阶段 |
|------|------|---------|
| Python CLI | 快速原型、MVP、开发者调试 | 阶段一 |
| Go CLI | 生产部署、Agent 安装、单二进制分发 | 阶段二 |

建议先用 Python 快速验证所有业务逻辑，再用 Go 重写核心引擎。
