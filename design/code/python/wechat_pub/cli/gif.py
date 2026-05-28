"""Canvas 动画录制 GIF 命令"""
import click


@click.command("record-gif")
@click.argument('html_file', type=click.Path(exists=True))
@click.option('-o', '--output', default='', help='输出 GIF 文件路径')
@click.option('--width', default=600, type=int, help='浏览器视口宽度（默认600）')
@click.option('--height', default=400, type=int, help='浏览器视口高度（默认400）')
@click.option('--fps', default=10, type=int, help='帧率（4-15，默认10）')
@click.option('--duration', default=5.0, type=float, help='录制时长/秒（1-8，默认5）')
@click.option('--colors', default=128, type=int, help='GIF颜色数（32-256，默认128）')
@click.option('--selector', default='canvas', help='Canvas元素CSS选择器（默认canvas）')
@click.option('--wait', default=500, type=int, help='页面加载后等待时间/毫秒（默认500）')
@click.option('--scale', default=1.0, type=float, help='设备像素比（1.0或2.0，默认1.0）')
@click.pass_context
def record_gif(ctx, html_file, output, width, height, fps, duration, colors, selector, wait, scale):
    """将 Canvas 动画 HTML 录制为 GIF 动图

    使用 Playwright 打开 HTML 文件，逐帧截图 Canvas 元素，
    用 Pillow 合成 GIF。适用于将 Canvas 动画转为公众号可用的动图。

    示例：

    \b
      wechat-pub record-gif animation.html
      wechat-pub record-gif animation.html --fps 8 --duration 6 -o output/demo.gif
      wechat-pub record-gif animation.html --selector "#my-canvas" --scale 2.0
    """
    from .main import emit_json

    json_mode = ctx.obj.get("JSON", False)

    from ..engine.image_engine import ImageEngine
    engine = ImageEngine()

    result = engine.record_canvas_to_gif(
        html_path=html_file,
        output_path=output,
        width=width,
        height=height,
        fps=fps,
        duration_s=duration,
        colors=colors,
        selector=selector,
        wait_ms=wait,
        scale=scale,
    )

    if not result.success:
        emit_json(False, code="GIF_RECORD_FAILED", error=result.error)
        return

    if json_mode:
        emit_json(True, code="GIF_RECORDED", data={
            "file_path": result.file_path,
            "width": result.width,
            "height": result.height,
            "frame_count": result.frame_count,
            "duration_ms": result.duration_ms,
            "file_size_kb": result.file_size_kb,
        })
    else:
        click.echo(f"✅ GIF 已生成: {result.file_path}")
        click.echo(f"   尺寸: {result.width}x{result.height}")
        click.echo(f"   帧数: {result.frame_count}")
        click.echo(f"   时长: {result.duration_ms / 1000:.1f}s")
        click.echo(f"   大小: {result.file_size_kb:.0f}KB")
