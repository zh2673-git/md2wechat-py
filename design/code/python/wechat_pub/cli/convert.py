"""convert 命令 — 支持 --draft 推送微信草稿箱"""
import click
from ..engine import Converter
from ..models import ConvertRequest


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--theme', default='claude-warm', help='主题 (claude-warm/claude-clean/claude-dark)')
@click.option('-o', '--output', default='', help='输出 HTML 文件路径')
@click.option('--preview', is_flag=True, help='只本地预览不上传')
@click.option('--draft', is_flag=True, help='推送微信草稿箱')
@click.option('--cover', type=click.Path(exists=True), help='封面图片路径')
@click.option('--title', default='', help='覆盖标题')
@click.option('--author', default='', help='覆盖作者')
@click.option('--digest', default='', help='覆盖摘要')
@click.pass_context
def convert(ctx, file, theme, output, preview, draft, cover, title, author, digest):
    """转换 Markdown 为微信公众号 HTML，可选推送草稿箱"""
    from .main import emit_json

    json_mode = ctx.obj.get("JSON", False)

    # 1. Markdown → HTML
    converter = Converter()
    req = ConvertRequest(
        file_path=file,
        theme=theme,
        title=title,
        author=author,
        digest=digest,
        output=output,
    )
    result = converter.convert(req)

    if not result.success:
        emit_json(False, code="CONVERT_FAILED", error=result.error)
        return

    html = result.html
    article_title = result.title or title or ""
    article_author = result.author or author or ""
    article_digest = result.digest or digest or ""

    # 2. 输出 HTML 文件
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(html)

    # 3. 推送微信草稿箱
    draft_media_id = ""
    if draft:
        try:
            from ..wechat import WeChatClient
            client = WeChatClient()

            if not client.is_configured():
                click.echo("⚠️ 微信凭证未配置，跳过草稿推送。", err=True)
                click.echo("   运行 wechat-pub config init 配置 app_id 和 app_secret", err=True)
            else:
                # 3a. 上传封面
                thumb_media_id = ""
                if cover:
                    click.echo("📤 上传封面图片...", err=True)
                    upload = client.upload_image(cover, "thumb")
                    thumb_media_id = upload.media_id
                    click.echo(f"   封面 media_id: {thumb_media_id}", err=True)

                # 3b. 创建草稿
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

    # 4. 输出结果
    if json_mode:
        emit_json(True, code="DRAFT_CREATED" if draft_media_id else "CONVERT_COMPLETED", data={
            "html_length": len(html),
            "output_file": output or "",
            "images_count": len(result.images),
            "draft_created": bool(draft_media_id),
            "draft_media_id": draft_media_id,
        })
    else:
        if output:
            click.echo(f"✅ 已保存到: {output} ({len(html)} 字符)")
        if draft_media_id:
            click.echo(f"✅ 已推送到微信草稿箱 (media_id: {draft_media_id})")
        elif not output and not draft:
            click.echo(html)
