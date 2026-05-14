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
        """生成高端深色风格 PNG 封面（使用 Pillow 渲染）

        封面布局：
        - 深色渐变背景 + 暖金属装饰
        - 中心标题 + accent 下划线
        - 同心圆 + 菱形几何装饰
        - 四角 L 形角标
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            # Pillow 不可用时回退到纯像素 PNG（无文字）
            return self._generate_fallback_png(title, theme, output_path)

        try:
            import math
            w, h = self.WECHAT_COVER_W, self.WECHAT_COVER_H
            center_x = 450
            crop_l, crop_r = 259, 641

            if not output_path:
                output_dir = Path.cwd() / "output" / "images"
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / "cover.png")

            # ── 颜色定义 ──
            bg_main = (28, 25, 23)       # #1C1917
            bg_mid = (37, 34, 32)        # #252220
            bg_deep = (17, 15, 13)       # #110F0D
            accent = (201, 100, 66)      # #C96442
            gold = (212, 167, 106)       # #D4A76A
            gold_light = (232, 201, 138) # #E8C98A
            text_main = (245, 240, 235)  # #F5F0EB
            text_sub = (168, 159, 149)   # #A89F95

            # ── 创建画布 ──
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # ── 背景渐变 ──
            for y_px in range(h):
                t = y_px / h
                t2 = (y_px / h) * 0.3  # 水平方向偏移
                r = int(bg_main[0] * (1 - t) + bg_deep[0] * t + (bg_mid[0] - bg_main[0]) * t2)
                g = int(bg_main[1] * (1 - t) + bg_deep[1] * t + (bg_mid[1] - bg_main[1]) * t2)
                b = int(bg_main[2] * (1 - t) + bg_deep[2] * t + (bg_mid[2] - bg_main[2]) * t2)
                r = max(0, min(255, r))
                g = max(0, min(255, g))
                b = max(0, min(255, b))
                draw.line([(0, y_px), (w, y_px)], fill=(r, g, b))

            # ── 中央暖光晕 ──
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            glow_r = int(h * 0.9)
            for i in range(glow_r, 0, -2):
                t = i / glow_r
                alpha = int(46 * (1 - t) ** 2)  # accent ~18% opacity at center
                color = accent + (alpha,)
                od.ellipse([center_x - i, 170 - i, center_x + i, 170 + i], fill=color)

            # 右上金色光晕
            gr_cx, gr_cy = int(w * 0.78), int(h * 0.15)
            glow_r2 = int(h * 0.8)
            for i in range(glow_r2, 0, -2):
                t = i / glow_r2
                alpha = int(26 * (1 - t) ** 2)
                color = gold + (alpha,)
                od.ellipse([gr_cx - i, gr_cy - i, gr_cx + i, gr_cy + i], fill=color)

            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # ── 左下角暖色光晕 ──
            bl_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            bld = ImageDraw.Draw(bl_overlay)
            bl_cx, bl_cy = int(w * 0.22), int(h * 0.85)
            glow_r3 = int(h * 0.6)
            for i in range(glow_r3, 0, -2):
                t = i / glow_r3
                alpha = int(30 * (1 - t) ** 2)
                color = accent + (alpha,)
                bld.ellipse([bl_cx - i, bl_cy - i, bl_cx + i, bl_cy + i], fill=color)

            img = Image.alpha_composite(img, bl_overlay)
            draw = ImageDraw.Draw(img)

            # ── 左右竖向装饰线（裁剪区外） ──
            line_color_r = gold + (46,)  # ~18%
            line_color_l = accent + (38,)  # ~15%
            draw.line([(w - 60, 40), (w - 60, h - 40)], fill=line_color_r, width=1)
            draw.line([(w - 45, 60), (w - 45, h - 60)], fill=gold + (26,), width=1)
            draw.line([(60, 40), (60, h - 40)], fill=line_color_l, width=1)
            draw.line([(45, 60), (45, h - 60)], fill=accent + (20,), width=1)

            # ── 宇宙/哲学意象 ──

            # 倾斜轨道椭圆（用点阵近似）
            import math as _m
            orbit_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            od2 = ImageDraw.Draw(orbit_overlay)
            # 轨道 1：倾斜 -8°
            cx, cy = center_x, 175
            rx, ry = 170, 45
            angle1 = _m.radians(-8)
            for deg in range(0, 360, 2):
                rad = _m.radians(deg)
                px = rx * _m.cos(rad)
                py = ry * _m.sin(rad)
                x_rot = cx + px * _m.cos(angle1) - py * _m.sin(angle1)
                y_rot = cy + px * _m.sin(angle1) + py * _m.cos(angle1)
                od2.ellipse([x_rot - 0.8, y_rot - 0.8, x_rot + 0.8, y_rot + 0.8], fill=gold + (56,))
            # 轨道 2：倾斜 22°
            angle2 = _m.radians(22)
            for deg in range(0, 360, 3):
                rad = _m.radians(deg)
                px = rx * _m.cos(rad)
                py = ry * _m.sin(rad)
                x_rot = cx + px * _m.cos(angle2) - py * _m.sin(angle2)
                y_rot = cy + px * _m.sin(angle2) + py * _m.cos(angle2)
                od2.ellipse([x_rot - 0.5, y_rot - 0.5, x_rot + 0.5, y_rot + 0.5], fill=gold + (26,))

            img = Image.alpha_composite(img, orbit_overlay)
            draw = ImageDraw.Draw(img)

            # 微星点缀
            stars = [
                (center_x - 120, 60, 1.8, gold_light + (128,)),   # 50%
                (center_x + 95, 52, 1.2, gold + (89,)),           # 35%
                (center_x + 140, 310, 1.5, gold_light + (102,)),  # 40%
                (center_x - 80, 300, 1.0, gold + (77,)),          # 30%
                (center_x - 155, 180, 0.8, gold + (51,)),         # 20%
                (center_x + 60, 250, 1.3, gold_light + (77,)),    # 30%
                (center_x - 30, 340, 0.7, gold + (64,)),          # 25%
            ]
            for sx, sy, sr, sc in stars:
                draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=sc)

            # 右上小月牙
            moon_cx, moon_cy, moon_r = crop_r - 45, 52, 10
            draw.ellipse([moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r], fill=gold + (38,))
            # 用深色圆覆盖形成月牙
            offset = 4
            draw.ellipse([moon_cx + offset - moon_r, moon_cy - offset - moon_r + 1,
                          moon_cx + offset + moon_r, moon_cy - offset + moon_r + 1], fill=bg_main + (217,))

            # ── 四角 L 形角标 ──
            corner_len = 20
            corner_pad = 12
            corner_alpha = 115  # ~45%
            corner_color = gold + (corner_alpha,)
            # 左上
            draw.line([(crop_l + corner_pad, 8), (crop_l + corner_pad, 8 + corner_len)], fill=corner_color, width=2)
            draw.line([(crop_l + corner_pad, 8), (crop_l + corner_pad + corner_len, 8)], fill=corner_color, width=2)
            # 右上
            draw.line([(crop_r - corner_pad, 8), (crop_r - corner_pad, 8 + corner_len)], fill=corner_color, width=2)
            draw.line([(crop_r - corner_pad - corner_len, 8), (crop_r - corner_pad, 8)], fill=corner_color, width=2)
            # 左下
            draw.line([(crop_l + corner_pad, h - 8), (crop_l + corner_pad, h - 8 - corner_len)], fill=corner_color, width=2)
            draw.line([(crop_l + corner_pad, h - 8), (crop_l + corner_pad + corner_len, h - 8)], fill=corner_color, width=2)
            # 右下
            draw.line([(crop_r - corner_pad, h - 8), (crop_r - corner_pad, h - 8 - corner_len)], fill=corner_color, width=2)
            draw.line([(crop_r - corner_pad - corner_len, h - 8), (crop_r - corner_pad, h - 8)], fill=corner_color, width=2)

            # ── 顶部/底部金色渐变线 ──
            line_overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            ld = ImageDraw.Draw(line_overlay)
            for x_px in range(30, 870):
                t = (x_px - 30) / 840.0
                # bell curve: max at center
                bell = max(0, 1.0 - abs(t - 0.5) * 2.5)
                alpha = int(179 * bell)  # max ~70%
                ld.line([(x_px, 18), (x_px + 1, 18)], fill=gold + (alpha,), width=1)
                ld.line([(x_px, h - 18), (x_px + 1, h - 18)], fill=gold + (alpha,), width=1)
            img = Image.alpha_composite(img, line_overlay)
            draw = ImageDraw.Draw(img)

            # ── 标题下 accent 横线 ──
            draw.line([(center_x - 60, 148), (center_x + 60, 148)], fill=accent + (204,), width=3)

            # ── 文字 ──
            font_title = self._load_font(34, bold=True)
            font_author = self._load_font(13)
            font_sub = self._load_font(11)

            display_title = title[:28] + ("..." if len(title) > 28 else "")
            display_author = author[:20] + ("..." if len(author) > 20 else "")
            display_sub = subtitle[:50] + ("..." if len(subtitle) > 50 else "")

            if display_title:
                bbox = draw.textbbox((0, 0), display_title, font=font_title)
                tw = bbox[2] - bbox[0]
                draw.text((center_x - tw // 2, 105), display_title, fill=text_main, font=font_title)

            if display_author:
                bbox = draw.textbbox((0, 0), display_author, font=font_author)
                aw = bbox[2] - bbox[0]
                draw.text((center_x - aw // 2, 165), display_author, fill=text_sub, font=font_author)

            if display_sub:
                bbox = draw.textbbox((0, 0), display_sub, font=font_sub)
                sw_val = bbox[2] - bbox[0]
                draw.text((center_x - sw_val // 2, h - 45), display_sub, fill=text_sub + (153,), font=font_sub)

            img = img.convert("RGB")
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
                "bg": "#F2EBE4",
                "bg-mid": "#EDE3D8",
                "text": "#3D3A36",
                "heading": "#1F1D1A",
                "muted": "#8C8278",
                "warm": "#B8860B",
            },
            "claude-clean": {
                "accent": "#C96442",
                "accent-light": "#FBF4EF",
                "bg": "#FFFFFF",
                "bg-mid": "#FAFAF8",
                "text": "#37352F",
                "heading": "#1A1A1A",
                "muted": "#9B9B9B",
                "warm": "#8B7355",
            },
            "claude-dark": {
                "accent": "#D4896C",
                "accent-light": "#3D2E24",
                "bg": "#1A1816",
                "bg-mid": "#221F1C",
                "text": "#D4CFC8",
                "heading": "#F0EBE3",
                "muted": "#8C8278",
                "warm": "#D4A76A",
            },
        }
        return themes.get(theme, themes["claude-warm"])

    def _build_svg(self, title: str, subtitle: str, author: str, c: dict) -> str:
        """构建高端 SVG 封面（中心布局，微信方形裁剪友好）

        设计语言：
        - 深色背景 + 暖金属质感，杂志封面风格
        - 微信列表页从 900x383 中心裁出 383x383 方形 → 核心视觉元素必须在 x:259-641 范围内
        - 大面积抽象几何装饰，填充+描边混合，层次丰富
        - 高对比度排版，标题醒目
        - 多层渐变营造纵深感
        """
        display_title = title[:32] + ("..." if len(title) > 32 else "")
        display_sub = subtitle[:50] + ("..." if len(subtitle) > 50 else "")
        display_author = author[:20] + ("..." if len(author) > 20 else "")

        # 微信方形裁剪边界（近似）
        crop_l, crop_r = 259, 641
        center_x = (crop_l + crop_r) // 2  # 450
        W, H = self.WECHAT_COVER_W, self.WECHAT_COVER_H

        # 根据主题决定深色/浅色模式
        is_dark = c["bg"] in ("#1A1816", "#1C1917", "#1F1D1A")
        # 浅色主题自动转为深色方案以保证视觉冲击力
        bg_main = "#1C1917" if not is_dark else c["bg"]
        bg_deep = "#110F0D"
        bg_mid = "#252220"
        accent = c["accent"]  # #C96442
        gold = "#D4A76A"
        gold_light = "#E8C98A"
        text_main = "#F5F0EB"
        text_sub = "#A89F95"

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <!-- 主背景渐变：深暖色，从上到下微暗 -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="30%" y2="100%">
      <stop offset="0%" style="stop-color:{bg_main};stop-opacity:1" />
      <stop offset="50%" style="stop-color:{bg_mid};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{bg_deep};stop-opacity:1" />
    </linearGradient>

    <!-- 中央暖光晕 -->
    <radialGradient id="centerGlow" cx="50%" cy="42%" r="45%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0.18" />
      <stop offset="40%" style="stop-color:{accent};stop-opacity:0.08" />
      <stop offset="100%" style="stop-color:{accent};stop-opacity:0" />
    </radialGradient>

    <!-- 右上角冷色光晕 -->
    <radialGradient id="topRightGlow" cx="78%" cy="15%" r="35%">
      <stop offset="0%" style="stop-color:{gold};stop-opacity:0.10" />
      <stop offset="100%" style="stop-color:{gold};stop-opacity:0" />
    </radialGradient>

    <!-- 左下角暖色光晕 -->
    <radialGradient id="bottomLeftGlow" cx="22%" cy="85%" r="30%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0.12" />
      <stop offset="100%" style="stop-color:{accent};stop-opacity:0" />
    </radialGradient>

    <!-- 金色渐变（用于装饰线） -->
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{gold};stop-opacity:0" />
      <stop offset="20%" style="stop-color:{gold};stop-opacity:0.7" />
      <stop offset="50%" style="stop-color:{gold_light};stop-opacity:1" />
      <stop offset="80%" style="stop-color:{gold};stop-opacity:0.7" />
      <stop offset="100%" style="stop-color:{gold};stop-opacity:0" />
    </linearGradient>

    <!-- accent 渐变 -->
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:{accent};stop-opacity:0" />
      <stop offset="30%" style="stop-color:{accent};stop-opacity:0.8" />
      <stop offset="70%" style="stop-color:{accent};stop-opacity:0.8" />
      <stop offset="100%" style="stop-color:{accent};stop-opacity:0" />
    </linearGradient>

    <!-- 散点纹理 -->
    <pattern id="scatterDots" x="0" y="0" width="80" height="80" patternUnits="userSpaceOnUse">
      <circle cx="20" cy="15" r="1.2" fill="{gold}" opacity="0.15" />
      <circle cx="55" cy="40" r="0.8" fill="{gold}" opacity="0.10" />
      <circle cx="10" cy="60" r="1.0" fill="{gold}" opacity="0.12" />
      <circle cx="70" cy="72" r="0.6" fill="{accent}" opacity="0.08" />
      <circle cx="40" cy="8" r="0.7" fill="{accent}" opacity="0.10" />
    </pattern>
  </defs>

  <!-- ===== 背景层 ===== -->
  <rect width="100%" height="100%" fill="url(#bgGrad)" />
  <rect width="100%" height="100%" fill="url(#centerGlow)" />
  <rect width="100%" height="100%" fill="url(#topRightGlow)" />
  <rect width="100%" height="100%" fill="url(#bottomLeftGlow)" />
  <rect width="100%" height="100%" fill="url(#scatterDots)" />

  <!-- ===== 全尺寸专属装饰（方形裁剪区外） ===== -->

  <!-- 右侧大弧线（x>641 裁剪区外，全尺寸可见） -->
  <path d="M 660,-30 A 280,280 0 0,1 {W+50},250" fill="none" stroke="{gold}" stroke-width="1.5" opacity="0.25" />
  <path d="M 680,-20 A 300,300 0 0,1 {W+30},280" fill="none" stroke="{gold}" stroke-width="0.8" opacity="0.15" />

  <!-- 左侧大弧线（x<259 裁剪区外，全尺寸可见） -->
  <path d="M 240,{H+30} A 280,280 0 0,1 -50,120" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.20" />
  <path d="M 220,{H+20} A 300,300 0 0,1 -30,90" fill="none" stroke="{accent}" stroke-width="0.8" opacity="0.12" />

  <!-- 右侧竖向装饰线组（裁剪区外） -->
  <line x1="{W-60}" y1="40" x2="{W-60}" y2="{H-40}" stroke="{gold}" stroke-width="0.6" opacity="0.18" />
  <line x1="{W-45}" y1="60" x2="{W-45}" y2="{H-60}" stroke="{gold}" stroke-width="0.3" opacity="0.10" />

  <!-- 左侧竖向装饰线组（裁剪区外） -->
  <line x1="60" y1="40" x2="60" y2="{H-40}" stroke="{accent}" stroke-width="0.6" opacity="0.15" />
  <line x1="45" y1="60" x2="45" y2="{H-60}" stroke="{accent}" stroke-width="0.3" opacity="0.08" />

  <!-- ===== 中心区域：极简留白 + 宇宙/哲学意象 ===== -->

  <!-- 倾斜轨道椭圆（行星轨道，宇宙秩序） -->
  <ellipse cx="{center_x}" cy="175" rx="170" ry="45" fill="none" stroke="{gold}" stroke-width="0.8" opacity="0.22" transform="rotate(-8 {center_x} 175)" />
  <ellipse cx="{center_x}" cy="175" rx="170" ry="45" fill="none" stroke="{gold}" stroke-width="0.4" opacity="0.10" transform="rotate(22 {center_x} 175)" />

  <!-- 微星点缀（不同亮度，深空感） -->
  <circle cx="{center_x-120}" cy="60" r="1.8" fill="{gold_light}" opacity="0.50" />
  <circle cx="{center_x+95}" cy="52" r="1.2" fill="{gold}" opacity="0.35" />
  <circle cx="{center_x+140}" cy="310" r="1.5" fill="{gold_light}" opacity="0.40" />
  <circle cx="{center_x-80}" cy="300" r="1.0" fill="{gold}" opacity="0.30" />
  <circle cx="{center_x-155}" cy="180" r="0.8" fill="{gold}" opacity="0.20" />
  <circle cx="{center_x+60}" cy="250" r="1.3" fill="{gold_light}" opacity="0.30" />
  <circle cx="{center_x-30}" cy="340" r="0.7" fill="{gold}" opacity="0.25" />

  <!-- 右上小月牙（天体意象，阴晴圆缺） -->
  <circle cx="{crop_r-45}" cy="52" r="10" fill="{gold}" opacity="0.15" />
  <circle cx="{crop_r-41}" cy="49" r="9" fill="{bg_main}" opacity="0.85" />

  <!-- 四角 L 形角标（方形裁剪区框线） -->
  <polyline points="{crop_l+12},22 {crop_l+12},8 {crop_l+32},8" fill="none" stroke="{gold}" stroke-width="1.5" opacity="0.45" stroke-linecap="round" />
  <polyline points="{crop_r-32},8 {crop_r-12},8 {crop_r-12},22" fill="none" stroke="{gold}" stroke-width="1.5" opacity="0.45" stroke-linecap="round" />
  <polyline points="{crop_l+12},{H-22} {crop_l+12},{H-8} {crop_l+32},{H-8}" fill="none" stroke="{gold}" stroke-width="1.5" opacity="0.45" stroke-linecap="round" />
  <polyline points="{crop_r-32},{H-8} {crop_r-12},{H-8} {crop_r-12},{H-22}" fill="none" stroke="{gold}" stroke-width="1.5" opacity="0.45" stroke-linecap="round" />

  <!-- ===== 顶部/底部装饰线 ===== -->
  <line x1="30" y1="18" x2="870" y2="18" stroke="url(#goldGrad)" stroke-width="1" />
  <line x1="30" y1="{H-18}" x2="870" y2="{H-18}" stroke="url(#goldGrad)" stroke-width="1" />

  <!-- ===== 标题区域（中心留白区的视觉重心） ===== -->
  <text x="{center_x}" y="130"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="34" font-weight="700" fill="{text_main}" text-anchor="middle" letter-spacing="1">
    {display_title}
  </text>

  <!-- 标题下 accent 横线 -->
  <line x1="{center_x-60}" y1="148" x2="{center_x+60}" y2="148" stroke="{accent}" stroke-width="2.5" stroke-linecap="round" opacity="0.80" />

  <!-- 作者/来源 -->
  <text x="{center_x}" y="178"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="13" fill="{text_sub}" text-anchor="middle" letter-spacing="1.5" opacity="0.90">
    {display_author or "微信公众号"}
  </text>

  <!-- 底部副标题 -->
  <text x="{center_x}" y="{H-40}"
        font-family="-apple-system,BlinkMacSystemFont,PingFang SC,Noto Sans SC,Microsoft YaHei,sans-serif"
        font-size="11" fill="{text_sub}" text-anchor="middle" letter-spacing="0.8" opacity="0.60">
    {display_sub if display_sub else "READ MORE →"}
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
