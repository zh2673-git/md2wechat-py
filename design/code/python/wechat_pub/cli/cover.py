"""封面生成 + 图片上传命令"""
import click


@click.command("generate-cover")
@click.option('--title', default='', help='文章标题')
@click.option('--subtitle', default='', help='副标题')
@click.option('--author', default='', help='作者')
@click.option('--theme', default='claude-warm', help='主题 (claude-warm/claude-clean/claude-dark)')
@click.option('-o', '--output', default='', help='输出文件路径')
@click.option('--format', 'fmt', default='png', type=click.Choice(['svg', 'png']), help='输出格式')
@click.option('--article', type=click.Path(exists=True), help='从 Markdown 文件提取标题')
@click.pass_context
def generate_cover(ctx, title, subtitle, author, theme, output, fmt, article):
    """生成 Claude 风格封面图"""
    from .main import emit_json

    json_mode = ctx.obj.get("JSON", False)

    # 如果提供了 Markdown 文件，提取元数据
    if article:
        try:
            with open(article, encoding="utf-8") as f:
                content = f.read()
            import re
            match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if match:
                for line in match.group(1).split("\n"):
                    if ":" in line:
                        key, _, val = line.partition(":")
                        k = key.strip().lower()
                        if k == "title" and not title:
                            title = val.strip()
                        elif k == "author" and not author:
                            author = val.strip()
                        elif k in ("digest", "subtitle", "description") and not subtitle:
                            subtitle = val.strip()
        except Exception:
            pass

    if not title:
        title = "未命名文章"

    from ..engine.image_engine import ImageEngine
    engine = ImageEngine()

    if fmt == "svg":
        result = engine.generate_cover(
            title=title, subtitle=subtitle, author=author,
            theme=theme, output_path=output,
        )
    else:
        result = engine.generate_placeholder_png(
            title=title, theme=theme, output_path=output,
        )

    if not result.success:
        emit_json(False, code="COVER_FAILED", error=result.error)
        return

    if json_mode:
        emit_json(True, code="COVER_GENERATED", data={
            "file_path": result.file_path,
            "width": result.width,
            "height": result.height,
            "format": fmt,
        })
    else:
        click.echo(f"✅ 封面已生成: {result.file_path}")
        click.echo(f"   尺寸: {result.width}x{result.height}")
        click.echo(f"   格式: {fmt}")


@click.command("upload-image")
@click.argument('file', type=click.Path(exists=True))
@click.option('--type', 'image_type', default='thumb', type=click.Choice(['thumb', 'content']), help='图片类型')
@click.pass_context
def upload_image(ctx, file, image_type):
    """上传图片到微信素材库"""
    from .main import emit_json

    json_mode = ctx.obj.get("JSON", False)

    from ..wechat import WeChatClient
    client = WeChatClient()

    if not client.is_configured():
        emit_json(False, code="NOT_CONFIGURED", error="微信凭证未配置。运行 wechat-pub config init")
        return

    try:
        if image_type == "content":
            url = client.upload_content_image(file)
            if json_mode:
                emit_json(True, code="IMAGE_UPLOADED", data={
                    "file": file,
                    "type": "content",
                    "url": url,
                })
            else:
                click.echo(f"✅ 正文图片已上传: {url}")
        else:
            result = client.upload_image(file, "thumb")
            if json_mode:
                emit_json(True, code="IMAGE_UPLOADED", data={
                    "file": file,
                    "type": "thumb",
                    "media_id": result.media_id,
                    "url": result.url,
                })
            else:
                click.echo(f"✅ 封面图片已上传: media_id={result.media_id}")
                if result.url:
                    click.echo(f"   URL: {result.url}")
    except Exception as e:
        emit_json(False, code="UPLOAD_FAILED", error=str(e))
