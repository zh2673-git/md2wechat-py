"""主题管理器：Anthropic Claude 风格主题"""
from pathlib import Path
import yaml


class ThemeManager:
    """主题管理器，加载主题 YAML 并生成 CSS"""

    # ── Claude 真实设计语言 ──────────────────────────────────────
    # Anthropic 的品牌核心：温暖、有机、人文感
    # 主色赭石橙（terracotta），不是紫色
    # 大量留白，微妙阴影，克制装饰
    # ─────────────────────────────────────────────────────────────
    CLAUDE_THEMES = {
        "claude-warm": {
            "name": "Claude 暖阳",
            "description": "Anthropic 官方暖调风格，赭石橙+奶油白",
            "colors": {
                # 核心品牌色
                "accent": "#C96442",           # 赭石橙（Claude 标志色）
                "accent-light": "#F5E6DC",     # 淡赭石（极低饱和度背景）
                "accent-mid": "#D4896C",       # 中间色（hover/次级）
                # 暖色点缀
                "warm": "#B8860B",             # 暗金棕（强调用）
                "warm-light": "#FDF6EC",       # 浅麦色背景
                # 背景层级
                "bg": "#FAF7F2",               # 奶油白（文章底色）
                "card-bg": "#FEFCF9",          # 微暖白（卡片）
                "card-shadow": "rgba(180,160,140,0.08)",
                # 文字层级
                "text": "#3D3A36",             # 暖炭灰（正文）
                "heading": "#1F1D1A",          # 深炭灰（标题）
                "muted": "#8C8278",            # 暖灰（辅助文字）
                # 边框与分割
                "border": "#E8E2DA",           # 暖米色边框
                "border-light": "#F0EBE3",     # 更浅边框
                # 代码
                "code-bg": "#2D2A26",          # 暗暖棕（代码背景）
                "code-text": "#E8E2DA",        # 暖白（代码文字）
            },
            "typography": {
                "font-family": '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", "Helvetica Neue", sans-serif',
                "font-size-base": "16px",
                "font-size-h1": "22px",
                "font-size-h2": "19px",
                "font-size-h3": "17px",
                "line-height": "1.8",
                "letter-spacing": "0.01em",
            },
            "spacing": {
                "section": "36px",
                "paragraph": "16px",
                "block-gap": "28px",
            },
            "radius": {
                "card": "10px",
                "button": "8px",
                "image": "6px",
                "pill": "20px",
            },
        },
        "claude-clean": {
            "name": "Claude 极简",
            "description": "更克制的白底版本，适合正式场景",
            "colors": {
                "accent": "#C96442",
                "accent-light": "#FBF4EF",
                "accent-mid": "#D4896C",
                "warm": "#8B7355",
                "warm-light": "#FAF8F5",
                "bg": "#FFFFFF",
                "card-bg": "#FEFEFE",
                "card-shadow": "rgba(0,0,0,0.03)",
                "text": "#37352F",
                "heading": "#1A1A1A",
                "muted": "#9B9B9B",
                "border": "#ECECEC",
                "border-light": "#F5F5F5",
                "code-bg": "#1F1F1F",
                "code-text": "#E0E0E0",
            },
            "typography": {
                "font-family": '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", sans-serif',
                "font-size-base": "15px",
                "font-size-h1": "21px",
                "font-size-h2": "18px",
                "font-size-h3": "16px",
                "line-height": "1.8",
                "letter-spacing": "0",
            },
            "spacing": {
                "section": "32px",
                "paragraph": "14px",
                "block-gap": "24px",
            },
            "radius": {
                "card": "8px",
                "button": "6px",
                "image": "4px",
                "pill": "18px",
            },
        },
        "claude-dark": {
            "name": "Claude 暗夜",
            "description": "深色背景，暖棕调暗色主题",
            "colors": {
                "accent": "#D4896C",
                "accent-light": "#3D2E24",
                "accent-mid": "#C96442",
                "warm": "#D4A76A",
                "warm-light": "#2D2518",
                "bg": "#1A1816",
                "card-bg": "#242120",
                "card-shadow": "rgba(0,0,0,0.3)",
                "text": "#D4CFC8",
                "heading": "#F0EBE3",
                "muted": "#8C8278",
                "border": "#3D3A36",
                "border-light": "#2D2A26",
                "code-bg": "#0F0E0D",
                "code-text": "#D4CFC8",
            },
            "typography": {
                "font-family": '-apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", sans-serif',
                "font-size-base": "16px",
                "font-size-h1": "22px",
                "font-size-h2": "19px",
                "font-size-h3": "17px",
                "line-height": "1.8",
                "letter-spacing": "0.01em",
            },
            "spacing": {
                "section": "36px",
                "paragraph": "16px",
                "block-gap": "28px",
            },
            "radius": {
                "card": "10px",
                "button": "8px",
                "image": "6px",
                "pill": "20px",
            },
        },
    }

    def __init__(self, themes_dir: str = None):
        self._themes = dict(self.CLAUDE_THEMES)
        if themes_dir:
            self._load_from_dir(themes_dir)

    def _load_from_dir(self, themes_dir: str):
        p = Path(themes_dir)
        if not p.exists():
            return
        for yaml_file in p.glob("*.yaml"):
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and "name" in data:
                self._themes[data["name"]] = data

    def list_themes(self) -> list[dict]:
        return [
            {"name": k, "title": v["name"], "description": v.get("description", "")}
            for k, v in self._themes.items()
        ]

    def get_theme_data(self, theme_name: str = "claude-warm") -> dict:
        """获取主题数据字典"""
        return self._themes.get(theme_name, self._themes["claude-warm"])

    def get_theme_css(self, theme_name: str = "claude-warm") -> str:
        """生成主题 CSS（微信兼容：纯内联）"""
        theme = self._themes.get(theme_name, self._themes["claude-warm"])
        c = theme["colors"]
        t = theme["typography"]
        s = theme["spacing"]
        r = theme["radius"]

        return f"""
<style>
.wechat-pub-article {{
    font-family: {t['font-family']};
    font-size: {t['font-size-base']};
    line-height: {t['line-height']};
    letter-spacing: {t.get('letter-spacing', '0')};
    color: {c['text']};
}}
.wechat-pub-article h1 {{
    font-size: {t['font-size-h1']};
    font-weight: 700;
    color: {c['heading']};
    margin: {s['section']} 0 {s['paragraph']};
    line-height: 1.4;
}}
.wechat-pub-article h2 {{
    font-size: {t['font-size-h2']};
    font-weight: 600;
    color: {c['heading']};
    margin: {s['section']} 0 {s['paragraph']};
    line-height: 1.45;
}}
.wechat-pub-article h3 {{
    font-size: {t['font-size-h3']};
    font-weight: 600;
    color: {c['heading']};
    margin: 20px 0 12px;
}}
.wechat-pub-article p {{
    margin: 0 0 {s['paragraph']};
    color: {c['text']};
}}
.wechat-pub-article blockquote {{
    border-left: 3px solid {c['accent']};
    background: {c['card-bg']};
    margin: {s['block-gap']} 0;
    padding: 16px 20px;
    border-radius: 0 {r['card']} {r['card']} 0;
    color: {c['heading']};
    font-style: italic;
}}
.wechat-pub-article code {{
    background: {c['code-bg']};
    color: {c['code-text']};
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.9em;
}}
.wechat-pub-article pre {{
    background: {c['code-bg']};
    color: {c['code-text']};
    padding: 16px 20px;
    border-radius: {r['card']};
    overflow-x: auto;
    margin: {s['block-gap']} 0;
}}
.wechat-pub-article pre code {{
    background: none;
    padding: 0;
    color: inherit;
}}
.wechat-pub-article ul, .wechat-pub-article ol {{
    margin: {s['paragraph']} 0;
    padding-left: 24px;
    color: {c['text']};
}}
.wechat-pub-article li {{
    margin: 8px 0;
}}
.wechat-pub-article a {{
    color: {c['accent']};
    text-decoration: none;
    border-bottom: 1px solid {c['accent-light']};
}}
.wechat-pub-article hr {{
    border: none;
    border-top: 1px solid {c['border']};
    margin: {s['section']} 0;
}}

/* 卡片通用 — Claude 风格：微阴影+暖边框 */
.wechat-pub-card {{
    background: {c['card-bg']};
    border: 1px solid {c['border']};
    border-radius: {r['card']};
    padding: 24px;
    margin: {s['block-gap']} 0;
    box-shadow: 0 1px 3px {c['card-shadow']};
}}
</style>
"""
