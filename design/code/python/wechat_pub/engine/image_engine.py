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
                output_path = str(Path.cwd() / f"cover_{safe_title}.svg")

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
        theme: str = "claude-warm",
        output_path: str = "",
    ) -> CoverResult:
        """生成纯色 PNG 占位封面（微信上传需要真实图片格式）

        使用纯 Python 生成最小有效 PNG，无需 Pillow。
        """
        try:
            colors = self._get_theme_colors(theme)
            bg_rgb = self._hex_to_rgb(colors["bg"])
            accent_rgb = self._hex_to_rgb(colors["accent"])
            text_rgb = self._hex_to_rgb(colors["heading"])

            if not output_path:
                output_path = str(Path.cwd() / "cover_placeholder.png")

            w, h = self.WECHAT_COVER_W, self.WECHAT_COVER_H
            png = self._create_png(w, h, bg_rgb, accent_rgb, text_rgb, title)
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
        """构建 Claude 风格 SVG 封面"""
        # 截断标题防止溢出
        display_title = title[:30] + ("..." if len(title) > 30 else "")
        display_sub = subtitle[:50] + ("..." if len(subtitle) > 50 else "")

        # 装饰元素：左侧赭石色条 + 几何圆
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{self.WECHAT_COVER_W}" height="{self.WECHAT_COVER_H}" viewBox="0 0 {self.WECHAT_COVER_W} {self.WECHAT_COVER_H}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c['bg']};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c['accent-light']};stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 背景 -->
  <rect width="100%" height="100%" fill="url(#bg)" />
  <!-- 左侧赭石色装饰条 -->
  <rect x="0" y="0" width="8" height="100%" fill="{c['accent']}" />
  <!-- 右下角装饰圆 -->
  <circle cx="820" cy="310" r="120" fill="{c['accent']}" opacity="0.06" />
  <circle cx="780" cy="280" r="60" fill="{c['warm']}" opacity="0.08" />
  <!-- 标题区域 -->
  <text x="60" y="155" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,sans-serif" font-size="32" font-weight="700" fill="{c['heading']}">{display_title}</text>
  <!-- 副标题 -->
  <text x="60" y="210" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,sans-serif" font-size="18" fill="{c['muted']}">{display_sub}</text>
  <!-- 底部分隔线 -->
  <line x1="60" y1="280" x2="300" y2="280" stroke="{c['accent']}" stroke-width="2" opacity="0.4" />
  <!-- 作者 -->
  <text x="60" y="330" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,sans-serif" font-size="14" fill="{c['muted']}">{author}</text>
</svg>'''

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """#RRGGBB → (R, G, B)"""
        h = hex_color.lstrip("#")
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

    def _create_png(
        self, w: int, h: int, bg: tuple, accent: tuple, text: tuple, title: str
    ) -> bytes:
        """创建最小有效 PNG（纯 Python，无需 Pillow）

        生成纯色背景 + 简单图案的封面。
        """
        import zlib

        def _make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)

        # IHDR
        ihdr_data = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # 8-bit RGB
        ihdr = _make_chunk(b"IHDR", ihdr_data)

        # IDAT — 生成像素数据
        raw_rows = bytearray()
        for y in range(h):
            raw_rows.append(0)  # filter byte: None
            for x in range(w):
                # 渐变背景：从 bg 到稍暗
                t = y / h
                r = int(bg[0] * (1 - t * 0.05))
                g = int(bg[1] * (1 - t * 0.05))
                b_val = int(bg[2] * (1 - t * 0.05))

                # 左边赭石色条 (0-8px)
                if x < 8:
                    r, g, b_val = accent

                # 底部区域装饰线 (y > h*0.85)
                if y > h * 0.85 and x < 240 and x > 60:
                    r, g, b_val = accent[0], accent[1], accent[2]
                    # 半透明效果：混合背景色
                    alpha = 0.3
                    r = int(accent[0] * alpha + bg[0] * (1 - alpha))
                    g = int(accent[1] * alpha + bg[1] * (1 - alpha))
                    b_val = int(accent[2] * alpha + bg[2] * (1 - alpha))

                raw_rows.extend([r & 0xFF, g & 0xFF, b_val & 0xFF])

        compressed = zlib.compress(bytes(raw_rows))
        idat = _make_chunk(b"IDAT", compressed)

        # IEND
        iend = _make_chunk(b"IEND", b"")

        # PNG signature
        signature = b"\x89PNG\r\n\x1a\n"

        return signature + ihdr + idat + iend
