"""config 命令"""
import os
from pathlib import Path
import click

CONFIG_DIR = Path.home() / ".config" / "wechat-pub"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


@click.group()
def config():
    """管理配置"""
    pass


@config.command()
def init():
    """初始化配置文件"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        click.echo(f"⚠️ 配置已存在: {CONFIG_FILE}")
        return

    example = """# wechat-pub 配置
wechat:
  app_id: ""           # 微信公众号 AppID
  app_secret: ""       # 微信公众号 AppSecret

image:
  provider: volcengine  # 图片生成服务
  api_key: ""
  model: ""

theme: claude-warm      # 默认主题
"""
    CONFIG_FILE.write_text(example, encoding="utf-8")
    click.echo(f"✅ 配置已创建: {CONFIG_FILE}")
    click.echo("请编辑此文件，填入微信 AppID 和 Secret")


@config.command()
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
@click.pass_context
def show(ctx, json_flag):
    """显示当前配置"""
    if CONFIG_FILE.exists():
        content = CONFIG_FILE.read_text(encoding="utf-8")
        if json_flag or ctx.obj.get("JSON", False):
            from .main import emit_json
            emit_json(True, data={"config_file": str(CONFIG_FILE), "content": content})
        else:
            click.echo(f"配置路径: {CONFIG_FILE}")
            click.echo(content)
    else:
        click.echo("⚠️ 配置未初始化，请运行 `wechat-pub config init`")
