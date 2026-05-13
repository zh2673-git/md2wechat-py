"""图片引擎：封面生成 + 占位图 + 微信上传集成"""
import hashlib
import struct
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CoverResult:
    """封面生成结果"""
    success: bool = True
    file_path: str = ""
    error: str = ""
    width: int = 900
    height: int = 383  # 微信公众号封面 2.35:1


class ImageEngine:
    """图片引擎

    功能：
    1. 生成 Claude 风格 SVG 封面（无需外部依赖）
    2. 生成 PNG 占位封面（纯 Python，无 Pillow 依赖）
    3. 如果 Agent 已生成图片，直接使用
    """

    # 微信公众号封面推荐尺寸：900 x 383 (2.35:1)
    WECHAT_COVER_W = 900
    WECHAT_COVER_H = 383

    def generate_cover(
        self,
        title: str = "",
        subtitle: str = "",
        theme: str = "claude-warm",
        output_path: str = "",
        author: str = "",
    ) -> CoverResult:
        """生成 SVG 封面

        Args:
            title: 文章标题
            subtitle: 副标题/描述
            theme: 主题名
            output_path: 输出路径（空则自动生成）
            author: 作者名

        Returns:
            CoverResult
        """
        try:
            colors = self._get_theme_colors(theme)

            if not output_path:
                safe_title = "".join(c for c in title[:20] if c.isalnum() or c in " _-") or "cover"
                output_dir = Path.cwd() / "output" / "images"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"cover_{safe_title}.svg")

            svg = self._build_svg(title, subtitle, author, colors)
            Path(output_path).write_text(svg, encoding="utf-8")

            return CoverResult(
                success=True,
                file_path=output_path,
            )
        except Exception as e:
            return CoverResult(success=False, error=str(e))

    def generate_placeholder_png(
        self,
        title: str = "",
        subtitle: str = "",
        theme: str = "claude-warm",
        output_path: str = "",
        author: str = "",
    ) -> CoverResult:
        """生成 Claude 风格 PNG 封面（使用 Pillow 渲染文字）

        封面布局：
        - 左上：标题 + 副标题
        - 正中央：品牌标识 zh2673 · 2026
        - 左下：作者信息
        - 右下角：几何装饰（三角 + 圆）
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # Pillow 不可用时回退到纯像素 PNG（无文字）
            return self._generate_fallback_png(title, theme, output_path)

        try:
            colors = self._get_theme_colors(theme)
            w, h = self.WECHAT_COVER_W, self.WECHAT_COVER_H

            if not output_path:
                output_dir = Path.cwd() / "output" / "images"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / "cover.png")

            # 创建画布
            img = Image.new("RGB", (w, h))
            draw = ImageDraw.Draw(img)

            # 绘制渐变背景
            bg_rgb = self._hex_to_rgb(colors["bg"])
            accent_light_rgb = self._hex_to_rgb(colors["accent-light"])
            for y_px in range(h):
                t = y_px / h
                r = int(bg_rgb[0] * (1 - t) + accent_light_rgb[0] * t)
                g = int(bg_rgb[1] * (1 - t) + accent_light_rgb[1] * t)
                b = int(bg_rgb[2] * (1 - t) + accent_light_rgb[2] * t)
                draw.line([(0, y_px), (w, y_px)], fill=(r, g, b))

            # 左侧 accent 竖条
            accent_rgb = self._hex_to_rgb(colors["accent"])
            draw.rectangle([0, 0, 5, h], fill=accent_rgb)

            # 右下角几何装饰
            accent_rgba = accent_rgb + (18,)  # ~7% opacity
            warm_rgb = self._hex_to_rgb(colors.get("warm", "#B8860B"))
            warm_rgba = warm_rgb + (15,)  # ~6% opacity

            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            od.polygon([(w, h), (w, int(h * 0.69)), (int(w * 0.867), h)], fill=accent_rgba)
            od.ellipse([int(w * 0.844 - h * 0.144), int(h * 0.797 - h * 0.144),
                        int(w * 0.844 + h * 0.144), int(h * 0.797 + h * 0.144)], fill=warm_rgba)
            od.ellipse([int(w * 0.911 - h * 0.052), int(h * 0.914 - h * 0.052),
                        int(w * 0.911 + h * 0.052), int(h * 0.914 + h * 0.052)], fill=accent_rgba[:3] + (13,))

            img_rgba = img.convert("RGBA")
            img_rgba = Image.alpha_composite(img_rgba, overlay)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)

            # 加载字体
            heading_rgb = self._hex_to_rgb(colors["heading"])
            muted_rgb = self._hex_to_rgb(colors["muted"])

            font_title = self._load_font(34, bold=True)
            font_sub = self._load_font(16)
            font_author = self._load_font(13)
            font_brand = self._load_font(20)

            # 标题（左上）
            display_title = title[:28] + ("..." if len(title) > 28 else "")
            if display_title:
                draw.text((52, 110), display_title, fill=heading_rgb, font=font_title)

            # 副标题
            display_sub = subtitle[:45] + ("..." if len(subtitle) > 45 else "")
            if display_sub:
                draw.text((54, 158), display_sub, fill=muted_rgb, font=font_sub)

            # accent 短横线
            draw.line([(52, 280), (110, 280)], fill=accent_rgb, width=2)

            # 底部作者
            display_author = author[:20] + ("..." if len(author) > 20 else "")
            if display_author:
                draw.text((54, 300), display_author, fill=muted_rgb, font=font_author)

            # 正中央品牌标识：zh2673 · 2026
            brand_text = "zh2673 · 2026"
            bbox = draw.textbbox((0, 0), brand_text, font=font_brand)
            brand_w = bbox[2] - bbox[0]
            brand_h = bbox[3] - bbox[1]
            brand_x = (w - brand_w) // 2
            brand_y = (h - brand_h) // 2 - 10
            # 品牌背景圆角矩形
            pad_x, pad_y = 20, 12
            draw.rounded_rectangle(
                [brand_x - pad_x, brand_y - pad_y, brand_x + brand_w + pad_x, brand_y + brand_h + pad_y],
                radius=8,
                fill=accent_rgb + (25,) if len(accent_rgb) == 3 else accent_rgb,
                outline=accent_rgb,
                width=1,
            )
            draw.text((brand_x, brand_y), brand_text, fill=heading_rgb, font=font_brand)

            img.save(output_path, "PNG")
            return CoverResult(success=True, file_path=output_path, width=w, height=h)
        except Exception as e:
            return CoverResult(success=False, error=str(e))

    @staticmethod
    def _load_font(size: int, bold: bool = False) -> "ImageFont.FreeTypeFont":
        """加载字体，尝试多个路径，回退到默认字体"""
        from PIL import ImageFont
        import os

        # 候选字体路径（Windows / macOS / Linux）
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
            "C:/Windows/Fonts/msyhbd.ttc",     # 微软雅黑粗体
            "C:/Windows/Fonts/simhei.ttf",     # 黑体
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",  # Linux
        ]

        for path in candidates:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, size, index=0)
                    if bold:
                        # 尝试加载粗体索引
                        try:
                            font = ImageFont.truetype(path, size, index=1)
                        except Exception:
                            pass
                    return font
                except Exception:
                    continue

        return ImageFont.load_default()

    def _generate_fallback_png(
        self, title: str, theme: str, output_path: str
    ) -> CoverResult:
        """Pillow 不可用时的回退方案：纯像素 PNG（无文字）"""
        try:
            colors = self._get_theme_colors(theme)
            bg_rgb = self._hex_to_rgb(colors["bg"])
            accent_rgb = self._hex_to_rgb(colors["accent"])
            text_rgb = self._hex_to_rgb(colors["heading"])

            if not output_path:
                output_dir = Path.cwd() / "output" / "images"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / "cover.png")


            w, h = self.WECHAT_COVER_W, self.WECHAT_COVER_H
            png = self._create_png_raw(w, h, bg_rgb, accent_rgb, text_rgb)
            Path(output_path).write_bytes(png)

            return CoverResult(success=True, file_path=output_path, width=w, height=h)
        except Exception as e:
            return CoverResult(success=False, error=str(e))

    # ── 私有方法 ────────────────────────────────────────────

    def _get_theme_colors(self, theme: str) -> dict:
        """获取主题配色"""
        themes = {
            "claude-warm": {
                "accent": "#C96442",
                "accent-light": "#F5E6DC",
                "bg": "#FAF7F2",
                "text": "#3D3A36",
                "heading": "#1F1D1A",
                "muted": "#8C8278",
                "warm": "#B8860B",
            },
            "claude-clean": {
                "accent": "#C96442",
                "accent-light": "#FBF4EF",
                "bg": "#FFFFFF",
                "text": "#37352F",
                "heading": "#1A1A1A",
                "muted": "#9B9B9B",
                "warm": "#8B7355",
            },
            "claude-dark": {
                "accent": "#D4896C",
                "accent-light": "#3D2E24",
                "bg": "#1A1816",
                "text": "#D4CFC8",
                "heading": "#F0EBE3",
                "muted": "#8C8278",
                "warm": "#D4A76A",
            },
        }
        return themes.get(theme, themes["claude-warm"])

    def _build_svg(self, title: str, subtitle: str, author: str, c: dict) -> str:
        """构建 Claude 风格 SVG 封面（美观版）

        设计语言：
        - 大面积留白，信息密度低，呼吸感强
        - 左侧 accent 色竖条作为视觉锚点（10px 宽）
        - 标题左对齐，大字号 + 粗字重，留白充足
        - 右下角几何装饰（三角+圆）提供视觉平衡
        - 底部信息区用细线分隔，保持层次清晰
        - 右上角带装饰性圆弧，增加结构感
        """
        display_title = title[:32] + ("..." if len(title) > 32 else "")
        display_sub = subtitle[:50] + ("..." if len(subtitle) > 50 else "")
        display_author = author[:20] + ("..." if len(author) > 20 else "")

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{self.WECHAT_COVER_W}" height="{self.WECHAT_COVER_H}" viewBox="0 0 {self.WECHAT_COVER_W} {self.WECHAT_COVER_H}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c['bg']};stop-opacity:1" />
      <stop offset="80%" style="stop-color:{c['bg']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c['accent-light']};stop-opacity:1" />
    </linearGradient>
    <linearGradient id="titleGrad" x1="0%" y1="0%" x2="80%" y2="0%">
      <stop offset="0%" style="stop-color:{c['heading']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c['heading']};stop-opacity:0.9" />
    </linearGradient>
    <linearGradient id="accGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:{c['accent']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c['accent']};stop-opacity:0.6" />
    </linearGradient>
  </defs>

  <!-- 主背景 -->
  <rect width="100%" height="100%" fill="url(#bgGrad)" />

  <!-- 左侧 accent 竖条（更宽，渐变） -->
  <rect x="0" y="0" width="10" height="100%" fill="url(#accGrad)" />

  <!-- 右上角装饰圆弧 -->
  <path d="M 680,-30 Q 780,80 900,200" fill="none" stroke="{c['accent']}" stroke-width="1.5" opacity="0.08" />
  <path d="M 530,-30 Q 680,100 900,300" fill="none" stroke="{c['accent']}" stroke-width="1" opacity="0.05" />

  <!-- 右下角几何装饰：三角 + 圆 -->
  <polygon points="900,383 900,230 750,383" fill="{c['accent']}" opacity="0.07" />
  <circle cx="740" cy="295" r="65" fill="{c['warm']}" opacity="0.06" />
  <circle cx="810" cy="340" r="25" fill="{c['accent']}" opacity="0.05" />
  <circle cx="860" cy="365" r="8" fill="{c['warm']}" opacity="0.08" />

  <!-- 顶部装饰线 -->
  <line x1="42" y1="38" x2="90" y2="38" stroke="{c['accent']}" stroke-width="3" stroke-linecap="round" />

  <!-- 主标题（加宽左间距，更大字号） -->
  <text x="42" y="142"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="36" font-weight="700" fill="url(#titleGrad)" letter-spacing="-0.5">
    {display_title}
  </text>

  <!-- 副标题 -->
  <text x="44" y="195"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="16" fill="{c['muted']}" letter-spacing="0.3" opacity="0.9">
    {display_sub}
  </text>

  <!-- accent 短横线 -->
  <line x1="42" y1="270" x2="120" y2="270" stroke="{c['accent']}" stroke-width="2.5" stroke-linecap="round" opacity="0.7" />

  <!-- 底部作者 + 品牌 -->
  <text x="44" y="340"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="13" fill="{c['muted']}" letter-spacing="0.4" opacity="0.8">
    {display_author or "微信公众号"}
  </text>
</svg>'''

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """#RRGGBB → (R, G, B)"""
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _create_png_raw(
        self, w: int, h: int, bg: tuple, accent: tuple, text: tuple, title: str
    ) -> bytes:
        """创建最小有效 PNG（纯 Python，无需 Pillow）

        生成 Claude 风格封面：渐变背景 + 左侧 accent 条 + 右下角三角/圆装饰
        """
        import zlib
        import math

        def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)

        # 预计算装饰图形的 alpha 遮罩
        # 右下角三角形：顶点 (w, h), (w, h*0.69), (w*0.867, h)
        def _in_triangle(px, py):
            x0, y0 = w, h
            x1, y1 = w, h * 0.69
            x2, y2 = w * 0.867, h
            d1 = (px - x2) * (y0 - y2) - (x0 - x2) * (py - y2)
            d2 = (px - x0) * (y1 - y0) - (x1 - x0) * (py - y0)
            d3 = (px - x1) * (y2 - y1) - (x2 - x1) * (py - y1)
            has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
            has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
            return not (has_neg and has_pos)

        # 右下角大圆：圆心 (w*0.844, h*0.797), 半径 h*0.144
        def _in_circle(px, py):
            cx, cy, r = w * 0.844, h * 0.797, h * 0.144
            return (px - cx) ** 2 + (py - cy) ** 2 <= r * r

        # 右下角小圆：圆心 (w*0.911, h*0.914), 半径 h*0.052
        def _in_small_circle(px, py):
            cx, cy, r = w * 0.911, h * 0.914, h * 0.052
            return (px - cx) ** 2 + (py - cy) ** 2 <= r * r

        # accent 短横线：y 在 [h*0.731, h*0.731+2.5], x 在 [52, 110]
        def _on_accent_line(px, py):
            return 52 <= px <= 110 and h * 0.731 <= py <= h * 0.731 + 2.5

        # IHDR
        ihdr_data = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
        ihdr = _make_chunk(b"IHDR", ihdr_data)

        # IDAT — 生成像素数据
        raw_rows = bytearray()
        for y_px in range(h):
            raw_rows.append(0)  # filter byte: None
            for x_px in range(w):
                # 渐变背景：从 bg 到稍暗（垂直方向 5% 变暗）
                t = y_px / h
                r = int(bg[0] * (1 - t * 0.05))
                g = int(bg[1] * (1 - t * 0.05))
                b_val = int(bg[2] * (1 - t * 0.05))

                # 左边 accent 色条 (0-6px)
                if x_px < 6:
                    r, g, b_val = accent

                # 右下角三角形装饰（7% 透明度 accent）
                if _in_triangle(x_px, y_px):
                    alpha = 0.07
                    r = int(accent[0] * alpha + r * (1 - alpha))
                    g = int(accent[1] * alpha + g * (1 - alpha))
                    b_val = int(accent[2] * alpha + b_val * (1 - alpha))

                # 大圆装饰（6% 透明度 warm 色，近似为 accent*0.9）
                if _in_circle(x_px, y_px):
                    warm_approx = (int(accent[0] * 0.9), int(accent[1] * 1.1), int(accent[2] * 0.7))
                    alpha = 0.06
                    r = int(warm_approx[0] * alpha + r * (1 - alpha))
                    g = int(warm_approx[1] * alpha + g * (1 - alpha))
                    b_val = int(warm_approx[2] * alpha + b_val * (1 - alpha))

                # 小圆装饰（5% 透明度 accent）
                if _in_small_circle(x_px, y_px):
                    alpha = 0.05
                    r = int(accent[0] * alpha + r * (1 - alpha))
                    g = int(accent[1] * alpha + g * (1 - alpha))
                    b_val = int(accent[2] * alpha + b_val * (1 - alpha))

                # accent 短横线
                if _on_accent_line(x_px, y_px):
                    r, g, b_val = accent

                raw_rows.extend([r & 0xFF, g & 0xFF, b_val & 0xFF])

        compressed = zlib.compress(bytes(raw_rows))
        idat = _make_chunk(b"IDAT", compressed)

        # IEND
        iend = _make_chunk(b"IEND", b"")

        # PNG signature
        signature = b"\x89PNG\r\n\x1a\n"

        return signature + ihdr + idat + iend
