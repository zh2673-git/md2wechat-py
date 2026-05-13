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
@click.option('--min-chars', default=19000, type=int, help='正文最小字符数（默认19000）')
@click.option('--upload-images/--no-upload-images', default=True, help='自动上传正文图片到微信CDN')
@click.pass_context
def publish(ctx, file, theme, cover, title, author, auto_cover, min_chars, upload_images):
    """一键发布：转换 + 配图 + 推送微信草稿箱"""
    from ..engine import Converter
    from ..engine.image_engine import ImageEngine
    from ..models import ConvertRequest
    import tempfile
    from pathlib import Path
    import re

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

    # 2. 字数检查（强制 >= min_chars）
    plain_text = re.sub(r"<[^>]+>", "", html)
    char_count = len(plain_text)
    if char_count < min_chars:
        click.echo(f"⚠️ 正文纯文本仅 {char_count} 字符，未达 {min_chars} 字符要求，需补充内容后重试。", err=True)
        click.echo(f"   可用 wechat-pub publish --min-chars 0 跳过检查", err=True)
        emit_json(False, code="CONTENT_TOO_SHORT",
                  error=f"正文仅 {char_count} 字符，需 >= {min_chars} 字符", data={
                      "char_count": char_count, "min_chars": min_chars})
        return

    # 3. 处理封面
    cover_path = cover
    if not cover_path and auto_cover:
        click.echo("🎨 自动生成封面...", err=True)
        img_engine = ImageEngine()
        # 尝试 SVG→PNG (用 cairosvg 如果可用)
        _cairosvg_ok = False
        try:
            import cairosvg
            # 验证一下能否真正使用
            _test_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" fill="red"/></svg>'
            cairosvg.svg2png(bytestring=_test_svg.encode())
            _cairosvg_ok = True
        except Exception:
            pass

        if _cairosvg_ok:
            try:
                import cairosvg
                svg_result = img_engine.generate_cover(
                    title=article_title,
                    subtitle=article_digest,
                    author=article_author,
                    theme=theme,
                )
                if svg_result.success:
                    png_path = svg_result.file_path.replace(".svg", ".png")
                    cairosvg.svg2png(url=svg_result.file_path, write_to=png_path)
                    cover_path = png_path
                    click.echo(f"   封面已生成 (SVG→PNG): {png_path}", err=True)
            except Exception:
                pass

        if not cover_path:
            cover_result = img_engine.generate_placeholder_png(
                title=article_title,
                subtitle=article_digest,
                author=article_author,
                theme=theme,
                output_path="",
            )
            if cover_result.success:
                cover_path = cover_result.file_path
                click.echo(f"   封面已生成 (PIL): {cover_path}", err=True)

    # 4. 上传正文图片到微信 CDN
    img_replacements = []
    if upload_images:
        try:
            from ..wechat import WeChatClient
            client = WeChatClient()
            if client.is_configured():
                img_tags = re.findall(r'<img[^>]+src="([^"]+)"', html)
                for img_src in img_tags:
                    if img_src.startswith("http") or img_src.startswith("data:"):
                        continue
                    # 尝试多种路径解析：绝对路径 → 相对文件的路径 → 相对 CWD
                    found_path = None
                    for try_path in [
                        img_src,  # 已经是绝对路径
                        str(Path(img_src)),  # CWD 相对路径
                        str(Path(file).parent / img_src),  # 文件所在目录相对路径
                    ]:
                        p = Path(try_path)
                        if p.exists() and p.is_file():
                            found_path = str(p)
                            break
                    if not found_path:
                        click.echo(f"   ⚠️ 找不到图片文件: {img_src}", err=True)
                        continue
                    local_path = found_path
                    upload_path = local_path
                    # 如果是 SVG，尝试转 PNG
                    if local_path.lower().endswith('.svg'):
                        if not _cairosvg_ok:
                            click.echo(f"   ⚠️ 跳过 SVG (系统缺少 Cairo 库): {img_src}", err=True)
                            continue
                        try:
                            import cairosvg
                            png_path = local_path.replace('.svg', '_upload.png')
                            cairosvg.svg2png(url=local_path, write_to=png_path)
                            upload_path = png_path
                        except Exception:
                            click.echo(f"   ⚠️ SVG转换失败: {img_src}", err=True)
                            continue
                    try:
                        cdn_url = client.upload_content_image(upload_path)
                        img_replacements.append((img_src, cdn_url))
                        click.echo(f"   📤 上传图片: {img_src} → CDN", err=True)
                    except Exception as e:
                        click.echo(f"   ⚠️ 上传失败: {img_src} ({e})", err=True)
                    if upload_path != local_path:
                        try:
                            Path(upload_path).unlink(missing_ok=True)
                        except Exception:
                            pass

                for old_src, new_src in img_replacements:
                    html = html.replace(f'src="{old_src}"', f'src="{new_src}"')
                    html = html.replace(f"src='{old_src}'", f"src='{new_src}'")
        except Exception as e:
            click.echo(f"   ⚠️ 图片上传出错: {e}", err=True)

    # 5. 输出 HTML 文件（临时）
    tmp_html = Path(tempfile.mktemp(suffix=".html"))
    tmp_html.write_text(html, encoding="utf-8")

    # 6. 推送微信草稿箱
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

    # 7. 输出结果
    img_count = len(img_replacements)
    if json_mode:
        emit_json(True, code="DRAFT_CREATED" if draft_media_id else "CONVERT_COMPLETED", data={
            "html_length": len(html),
            "char_count": char_count,
            "images_uploaded": img_count,
            "draft_created": bool(draft_media_id),
            "draft_media_id": draft_media_id,
            "cover_used": cover_path or "",
            "title": article_title,
        })
    else:
        click.echo(f"\n✅ 完成! 标题: {article_title}")
        click.echo(f"   正文字数: {char_count} 字符")
        if img_count > 0:
            click.echo(f"   上传图片: {img_count} 张")
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
