"""CLI 主入口"""
import json
import sys
import click

from ..models import CLIResponse


def emit_json(success: bool, code: str = "OK", message: str = "",
              status: str = "completed", data: dict = None, error: str = ""):
    """输出 JSON envelope"""
    resp = CLIResponse(
        success=success, code=code, message=message,
        status=status, data=data or {}, error=error,
    )
    click.echo(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))
    if not success:
        sys.exit(1)


@click.group()
@click.option('--json', 'json_flag', is_flag=True, help='JSON 格式输出')
@click.pass_context
def cli(ctx, json_flag):
    """wechat-pub: Markdown → 微信公众号排版工具 (Claude 风格)"""
    ctx.ensure_object(dict)
    ctx.obj["JSON"] = json_flag


# 注册子命令
from .convert import convert
from .inspect import inspect, preview
from .layout import layout
from .config import config
from .cover import generate_cover, upload_image

cli.add_command(convert)
cli.add_command(inspect)
cli.add_command(preview)
cli.add_command(layout)
cli.add_command(config)
cli.add_command(generate_cover)
cli.add_command(upload_image)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--theme', default='claude-warm', help='主题')
@click.option('--cover', type=click.Path(exists=True), help='封面图片路径')
@click.option('--title', default='', help='覆盖标题')
@click.option('--author', default='', help='覆盖作者')
@click.option('--auto-cover', is_flag=True, help='自动生成封面（无封面时）')
@click.pass_context
def publish(ctx, file, theme, cover, title, author, auto_cover):
    """一键发布：转换 + 配图 + 推送微信草稿箱"""
    from ..engine import Converter
    from ..engine.image_engine import ImageEngine
    from ..models import ConvertRequest

    json_mode = ctx.obj.get("JSON", False)

    # 1. 转换 Markdown → HTML
    converter = Converter()
    req = ConvertRequest(file_path=file, theme=theme, title=title, author=author)
    result = converter.convert(req)

    if not result.success:
        emit_json(False, code="CONVERT_FAILED", error=result.error)
        return

    article_title = result.title or title or "未命名文章"
    article_author = result.author or author or ""
    article_digest = result.digest or ""
    html = result.html

    # 2. 处理封面
    cover_path = cover
    if not cover_path and auto_cover:
        click.echo("🎨 自动生成封面...", err=True)
        img_engine = ImageEngine()
        # 先尝试 SVG（微信不一定支持），再尝试 PNG
        cover_result = img_engine.generate_placeholder_png(
            title=article_title,
            subtitle=article_digest,
            author=article_author,
            theme=theme,
            output_path=str(click.get_app_dir("wechat-pub") + "/auto_cover.png") if False else "",
        )
        if cover_result.success:
            cover_path = cover_result.file_path
            click.echo(f"   封面已生成: {cover_path}", err=True)

    # 3. 输出 HTML 文件（临时）
    import tempfile
    from pathlib import Path
    tmp_html = Path(tempfile.mktemp(suffix=".html"))
    tmp_html.write_text(html, encoding="utf-8")

    # 4. 推送微信草稿箱
    draft_media_id = ""
    try:
        from ..wechat import WeChatClient
        client = WeChatClient()

        if not client.is_configured():
            click.echo("⚠️ 微信凭证未配置，仅输出 HTML。", err=True)
            click.echo("   运行 wechat-pub config init 配置 app_id 和 app_secret", err=True)
        else:
            # 上传封面
            thumb_media_id = ""
            if cover_path:
                click.echo("📤 上传封面图片...", err=True)
                upload = client.upload_image(cover_path, "thumb")
                thumb_media_id = upload.media_id
                click.echo(f"   封面 media_id: {thumb_media_id}", err=True)

            # 创建草稿
            click.echo("📤 推送草稿到微信公众号...", err=True)
            draft_result = client.create_draft(
                title=article_title[:64],
                content=html,
                thumb_media_id=thumb_media_id,
                author=article_author[:16],
                digest=article_digest[:128],
                show_cover_pic=0,
            )
            draft_media_id = draft_result.media_id
            click.echo(f"✅ 草稿已推送! media_id: {draft_media_id}", err=True)

    except Exception as e:
        click.echo(f"❌ 推送草稿失败: {e}", err=True)
        if json_mode:
            emit_json(False, code="DRAFT_FAILED", error=str(e))
            return

    # 5. 输出结果
    if json_mode:
        emit_json(True, code="DRAFT_CREATED" if draft_media_id else "CONVERT_COMPLETED", data={
            "html_length": len(html),
            "images_count": len(result.images),
            "draft_created": bool(draft_media_id),
            "draft_media_id": draft_media_id,
            "cover_used": cover_path or "",
            "title": article_title,
        })
    else:
        click.echo(f"\n✅ 完成! 标题: {article_title}")
        if draft_media_id:
            click.echo(f"   草稿 media_id: {draft_media_id}")
        if cover_path:
            click.echo(f"   封面: {cover_path}")
        click.echo(f"   HTML 大小: {len(html)} 字符")

    # 清理临时文件
    try:
        tmp_html.unlink(missing_ok=True)
    except Exception:
        pass


@cli.command()
@click.pass_context
def version(ctx):
    """显示版本号"""
    if ctx.obj.get("JSON"):
        emit_json(True, code="VERSION_SHOWN", data={"version": "0.1.0"})
    else:
        click.echo("wechat-pub v0.1.0")


@cli.command()
@click.pass_context
def capabilities(ctx):
    """显示当前 CLI 能力"""
    caps = {
        "version": "0.1.0",
        "commands": [
            "convert", "inspect", "preview", "publish", "layout",
            "config", "generate-cover", "upload-image", "version", "capabilities",
        ],
        "modes": {"api": "确定性渲染（支持 :::block）"},
        "themes": ["claude-warm", "claude-clean", "claude-dark"],
        "layout_modules": 6,
        "wechat_integration": "draft",
        "cover_generation": "svg + png placeholder",
        "json_envelope": True,
    }
    if ctx.obj.get("JSON"):
        emit_json(True, data=caps)
    else:
        click.echo("=== wechat-pub 能力总览 ===")
        for k, v in caps.items():
            click.echo(f"  {k}: {v}")
