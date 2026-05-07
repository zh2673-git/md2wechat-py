"""inspect & preview 命令"""
import click
from ..engine import Converter


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
@click.pass_context
def inspect(ctx, file, json_flag):
    """检查文章的发布准备状态"""
    json_mode = json_flag or ctx.obj.get("JSON", False)
    converter = Converter()
    result = converter.inspect(file)

    if json_mode:
        from .main import emit_json
        emit_json(True, code="INSPECT_COMPLETED", data=result)
    else:
        meta = result["metadata"]
        click.echo(f"\n📄 文章检查: {file}")
        click.echo(f"   标题: {meta['title'] or '未设置'}")
        click.echo(f"   作者: {meta['author'] or '未设置'}")
        click.echo(f"   摘要: {meta['digest'] or '未设置'}")
        click.echo(f"   状态: {result['readiness']}")
        for c in result.get("checks", []):
            icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(c["level"], "•")
            click.echo(f"   {icon} {c['message']}")


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--theme', default='claude-warm', help='主题')
@click.option('-o', '--output', default='preview.html', help='输出 HTML 文件')
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
@click.pass_context
def preview(ctx, file, theme, output, json_flag):
    """生成本地预览 HTML（不上传）"""
    json_mode = json_flag or ctx.obj.get("JSON", False)
    converter = Converter()
    html = converter.preview(file, theme=theme)

    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    if json_mode:
        from .main import emit_json
        emit_json(True, code="PREVIEW_READY", data={"file": output, "size": len(html)})
    else:
        click.echo(f"✅ 预览已生成: {output}")
