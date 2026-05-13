"""Markdown → 微信公众号 HTML 转换引擎"""
import hashlib
import re

from markdown_it import MarkdownIt
from markdown_it.token import Token

from ..models import ConvertRequest, ConvertResult, ImageRef
from .layout_renderer import LayoutRenderer
from .inline_styler import InlineStyler


class Converter:
    """Markdown → 微信公众号 HTML 转换器（Claude 风格）"""

    def __init__(self, layout_renderer: LayoutRenderer = None):
        self._md = MarkdownIt("default", {"html": True})
        self._layout = layout_renderer or LayoutRenderer()
        self._setup_custom_rules()

    def _setup_custom_rules(self):
        """自定义渲染规则"""
        # 图片渲染：记录引用
        default_image = self._md.renderer.rules.get("image")
        def _image_render(tokens, idx, options, env, *args, **kwargs):
            token = tokens[idx]
            src = token.attrGet("src") or ""
            alt = token.content or ""
            # 记录图片引用
            if "images" not in env:
                env["images"] = []
            env["images"].append({
                "src": src,
                "alt": alt,
                "placeholder": f"__IMG_{hashlib.md5(src.encode()).hexdigest()[:8]}__"
            })
            return f'<img src="{src}" alt="{alt}" style="max-width:100%;height:auto;border-radius:8px;margin:12px 0;" />'
        self._md.renderer.rules["image"] = _image_render

    # -----------------------------------------------------------
    # 主入口
    # -----------------------------------------------------------
    def convert(self, req: ConvertRequest) -> ConvertResult:
        """转换 Markdown → 微信兼容 HTML"""
        try:
            md_content = req.markdown
            if req.file_path:
                with open(req.file_path, encoding="utf-8") as f:
                    md_content = f.read()

            # 1. 提取 frontmatter
            md_content, metadata = self._extract_frontmatter(md_content)

            # 2. 渲染 :::block 为 HTML
            md_with_blocks = self._layout.render(md_content, theme=req.theme)

            # 3. 标准 Markdown → HTML
            env = {"images": []}
            body_html = self._md.render(md_with_blocks, env)

            # 4. 内联样式注入（微信兼容：不用 <style> 标签）
            styler = InlineStyler(theme=req.theme)
            styled_html = styler.apply(body_html)

            # 5. 压缩 HTML（移除注释、多余空白，控制体积在微信 20000 字符限制内）
            full_html = self._compress_html(styled_html)

            # 6. 包装
            full_html = self._wrap_html(full_html, metadata)

            # 7. 处理图片引用
            images = [
                ImageRef(index=i, original=img["src"])
                for i, img in enumerate(env.get("images", []))
            ]

            return ConvertResult(
                success=True,
                html=full_html,
                images=images,
                title=metadata.get("title", ""),
                author=metadata.get("author", ""),
                digest=metadata.get("digest", ""),
                theme=req.theme,
            )

        except Exception as e:
            return ConvertResult(success=False, error=str(e))

    # -----------------------------------------------------------
    # Frontmatter 解析
    # -----------------------------------------------------------
    _FM_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

    def _extract_frontmatter(self, md: str) -> tuple[str, dict]:
        """提取 YAML frontmatter"""
        match = self._FM_PATTERN.match(md)
        metadata = {"title": "", "author": "", "digest": ""}
        if not match:
            return md, metadata
        body = match.group(1)
        for line in body.split("\n"):
            if ":" in line:
                key, _, val = line.partition(":")
                metadata[key.strip().lower()] = val.strip()
        return md[match.end():], metadata

    # -----------------------------------------------------------
    # 包装完整 HTML
    # -----------------------------------------------------------
    def _wrap_html(self, body: str, metadata: dict) -> str:
        """包装为完整 HTML（微信兼容：纯内联样式）"""
        # InlineStyler 已注入所有样式，此处仅做最外层包装
        return f"""<section style="max-width:680px;margin:0 auto;padding:24px 16px;background:#FAF7F2;">
<article>
{body}
</article>
</section>"""

    # -----------------------------------------------------------
    # 检查
    # -----------------------------------------------------------
    def inspect(self, file_path: str) -> dict:
        """检查文章发布准备状态"""
        from ..models import InspectResult, CheckItem, Metadata as M

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # 提取元数据
        _, metadata = self._extract_frontmatter(content)
        title = metadata.get("title", "") or "未命名文章"
        author = metadata.get("author", "")
        digest = metadata.get("digest", "") or metadata.get("summary", "") or metadata.get("description", "")

        # 检查项
        checks = []
        if not title or title == "未命名文章":
            checks.append(CheckItem(level="warning", message="标题未设置，将使用首个 H1 或 '未命名文章'"))
        if len(title) > 64:
            checks.append(CheckItem(level="warning", message=f"标题超长 ({len(title)}/64)"))
        if not digest:
            checks.append(CheckItem(level="info", message="摘要未设置，将自动从正文生成"))

        # 检查 :::block 语法
        layout_result = self._layout.validate(content)
        for e in layout_result.get("errors", []):
            checks.append(CheckItem(level="error", message=e["message"]))
        for w in layout_result.get("warnings", []):
            checks.append(CheckItem(level="warning", message=w["message"]))

        # 计算 readiness
        has_error = any(c.level == "error" for c in checks)
        has_warning = any(c.level == "warning" for c in checks)
        readiness = "error" if has_error else ("warning" if has_warning else "ready")

        md = M(title=title, author=author, digest=digest)
        result = InspectResult(metadata=md, readiness=readiness, checks=checks)
        return result.to_dict()

    def preview(self, file_path: str, theme: str = "claude-warm") -> str:
        """生成本地预览 HTML"""
        req = ConvertRequest(file_path=file_path, theme=theme)
        result = self.convert(req)
        return result.html

    # -----------------------------------------------------------
    # HTML 压缩
    # -----------------------------------------------------------
    def _compress_html(self, html: str) -> str:
        """压缩 HTML：移除注释、多余空白、模板内缩进，控制体积在微信 20000 字符限制内"""
        # 1. 移除 HTML 注释
        html = re.sub(r'<!--[\s\S]*?-->', '', html)

        # 2. 压缩模板中的多行 style 属性为单行
        def _compact_style(m):
            val = m.group(1)
            val = re.sub(r'\s+', ' ', val).strip()
            return f'style="{val}"'
        html = re.sub(r'style="([\s\S]*?)"', _compact_style, html)

        # 3. 压缩连续空白为单个空格（保留换行结构）
        html = re.sub(r'[ \t]+', ' ', html)

        # 4. 移除标签间的空白行（保留必要的单个换行）
        html = re.sub(r'\n\s*\n', '\n', html)

        # 5. 移除标签内首尾空白
        html = re.sub(r'>\s+<', '><', html)

        return html.strip()
