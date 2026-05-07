"""内联样式注入器：将 Claude 风格以 inline style 写入每个 HTML 元素

微信公众号会删除 <style> 标签和 class 属性，
所以所有样式必须以 inline style 方式逐元素注入。

关键原则：只给【没有 style 属性】的裸标签注入样式，
不触碰 :::block 模板已渲染好的带样式元素。
"""
import re


class InlineStyler:
    """给标准 Markdown 渲染的裸 HTML 元素注入 Claude 风格内联样式"""

    STYLES = {
        "claude-warm": {
            "_root": (
                "max-width:680px;margin:0 auto;padding:24px 16px;"
                "background:#FAF7F2;"
                "font-family:-apple-system,BlinkMacSystemFont,"
                '"PingFang SC","Noto Sans SC","Helvetica Neue",sans-serif;'
                "font-size:16px;line-height:1.8;letter-spacing:0.01em;color:#3D3A36;"
            ),
            "h1": "font-size:22px;font-weight:700;color:#1F1D1A;margin:36px 0 16px;line-height:1.4;",
            "h2": "font-size:19px;font-weight:600;color:#1F1D1A;margin:36px 0 16px;line-height:1.45;padding-bottom:8px;border-bottom:1px solid #E8E2DA;",
            "h3": "font-size:17px;font-weight:600;color:#1F1D1A;margin:20px 0 12px;line-height:1.5;",
            "h4": "font-size:16px;font-weight:600;color:#1F1D1A;margin:16px 0 8px;",
            "p": "margin:0 0 16px;color:#3D3A36;line-height:1.8;",
            "blockquote": "border-left:3px solid #C96442;background:#FEFCF9;margin:28px 0;padding:16px 20px;border-radius:0 10px 10px 0;color:#1F1D1A;",
            "ul": "margin:16px 0;padding-left:24px;color:#3D3A36;",
            "ol": "margin:16px 0;padding-left:24px;color:#3D3A36;",
            "li": "margin:8px 0;line-height:1.8;",
            "strong": "font-weight:600;color:#1F1D1A;",
            "em": "font-style:italic;color:#8C8278;",
            "a": "color:#C96442;text-decoration:none;border-bottom:1px solid #F5E6DC;",
            "hr": "border:none;border-top:1px solid #E8E2DA;margin:36px 0;",
            "code": "background:#2D2A26;color:#E8E2DA;padding:2px 6px;border-radius:4px;font-size:0.9em;",
            "pre": "background:#2D2A26;color:#E8E2DA;padding:16px 20px;border-radius:10px;overflow-x:auto;margin:28px 0;",
            "img": "max-width:100%;height:auto;border-radius:6px;margin:12px 0;",
            "table": "width:100%;border-collapse:collapse;margin:20px 0;font-size:15px;",
            "th": "background:#F5E6DC;color:#1F1D1A;font-weight:600;padding:10px 14px;border:1px solid #E8E2DA;text-align:left;",
            "td": "padding:10px 14px;border:1px solid #E8E2DA;color:#3D3A36;",
        },
        "claude-clean": {
            "_root": (
                "max-width:680px;margin:0 auto;padding:24px 16px;"
                "background:#FFFFFF;"
                "font-family:-apple-system,BlinkMacSystemFont,"
                '"PingFang SC","Noto Sans SC",sans-serif;'
                "font-size:15px;line-height:1.8;color:#37352F;"
            ),
            "h1": "font-size:21px;font-weight:700;color:#1A1A1A;margin:32px 0 14px;line-height:1.4;",
            "h2": "font-size:18px;font-weight:600;color:#1A1A1A;margin:32px 0 14px;line-height:1.45;padding-bottom:8px;border-bottom:1px solid #ECECEC;",
            "h3": "font-size:16px;font-weight:600;color:#1A1A1A;margin:20px 0 10px;",
            "h4": "font-size:15px;font-weight:600;color:#1A1A1A;margin:14px 0 8px;",
            "p": "margin:0 0 14px;color:#37352F;line-height:1.8;",
            "blockquote": "border-left:3px solid #C96442;background:#FEFEFE;margin:24px 0;padding:16px 20px;border-radius:0 8px 8px 0;color:#1A1A1A;",
            "ul": "margin:14px 0;padding-left:24px;color:#37352F;",
            "ol": "margin:14px 0;padding-left:24px;color:#37352F;",
            "li": "margin:6px 0;line-height:1.8;",
            "strong": "font-weight:600;color:#1A1A1A;",
            "em": "font-style:italic;color:#9B9B9B;",
            "a": "color:#C96442;text-decoration:none;border-bottom:1px solid #FBF4EF;",
            "hr": "border:none;border-top:1px solid #ECECEC;margin:32px 0;",
            "code": "background:#1F1F1F;color:#E0E0E0;padding:2px 6px;border-radius:4px;font-size:0.9em;",
            "pre": "background:#1F1F1F;color:#E0E0E0;padding:16px 20px;border-radius:8px;overflow-x:auto;margin:24px 0;",
            "img": "max-width:100%;height:auto;border-radius:4px;margin:10px 0;",
            "table": "width:100%;border-collapse:collapse;margin:18px 0;font-size:14px;",
            "th": "background:#FBF4EF;color:#1A1A1A;font-weight:600;padding:8px 12px;border:1px solid #ECECEC;text-align:left;",
            "td": "padding:8px 12px;border:1px solid #ECECEC;color:#37352F;",
        },
        "claude-dark": {
            "_root": (
                "max-width:680px;margin:0 auto;padding:24px 16px;"
                "background:#1A1816;"
                "font-family:-apple-system,BlinkMacSystemFont,"
                '"PingFang SC","Noto Sans SC",sans-serif;'
                "font-size:16px;line-height:1.8;letter-spacing:0.01em;color:#D4CFC8;"
            ),
            "h1": "font-size:22px;font-weight:700;color:#F0EBE3;margin:36px 0 16px;line-height:1.4;",
            "h2": "font-size:19px;font-weight:600;color:#F0EBE3;margin:36px 0 16px;line-height:1.45;padding-bottom:8px;border-bottom:1px solid #3D3A36;",
            "h3": "font-size:17px;font-weight:600;color:#F0EBE3;margin:20px 0 12px;",
            "h4": "font-size:16px;font-weight:600;color:#F0EBE3;margin:16px 0 8px;",
            "p": "margin:0 0 16px;color:#D4CFC8;line-height:1.8;",
            "blockquote": "border-left:3px solid #D4896C;background:#242120;margin:28px 0;padding:16px 20px;border-radius:0 10px 10px 0;color:#F0EBE3;",
            "ul": "margin:16px 0;padding-left:24px;color:#D4CFC8;",
            "ol": "margin:16px 0;padding-left:24px;color:#D4CFC8;",
            "li": "margin:8px 0;line-height:1.8;",
            "strong": "font-weight:600;color:#F0EBE3;",
            "em": "font-style:italic;color:#8C8278;",
            "a": "color:#D4896C;text-decoration:none;border-bottom:1px solid #3D2E24;",
            "hr": "border:none;border-top:1px solid #3D3A36;margin:36px 0;",
            "code": "background:#0F0E0D;color:#D4CFC8;padding:2px 6px;border-radius:4px;font-size:0.9em;",
            "pre": "background:#0F0E0D;color:#D4CFC8;padding:16px 20px;border-radius:10px;overflow-x:auto;margin:28px 0;",
            "img": "max-width:100%;height:auto;border-radius:6px;margin:12px 0;",
            "table": "width:100%;border-collapse:collapse;margin:20px 0;font-size:15px;",
            "th": "background:#3D2E24;color:#F0EBE3;font-weight:600;padding:10px 14px;border:1px solid #3D3A36;text-align:left;",
            "td": "padding:10px 14px;border:1px solid #3D3A36;color:#D4CFC8;",
        },
    }

    def __init__(self, theme: str = "claude-warm"):
        self.theme = theme
        self.styles = self.STYLES.get(theme, self.STYLES["claude-warm"])

    def apply(self, html: str) -> str:
        """对 HTML 注入内联样式（只给裸标签注入，不触碰已有 style 的元素）"""
        # 1. 移除 <style>...</style> 标签块（微信会删，留着也无用）
        html = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", html, flags=re.IGNORECASE)

        # 2. 移除 class 属性（微信不支持，留着白占字符）
        html = re.sub(r'\s+class="[^"]*"', "", html)

        # 3. 逐标签注入样式
        for tag, style in self.styles.items():
            if tag.startswith("_"):
                continue
            html = self._inject_bare_tags(html, tag, style)

        # 4. 特殊处理：blockquote 内的 <p> 也加样式
        html = self._style_blockquote_paras(html)

        # 5. 特殊处理：pre 内的 <code> 去掉独立样式
        html = self._style_pre_code(html)

        return html

    def _inject_bare_tags(self, html: str, tag: str, style: str) -> str:
        """只给【没有 style 属性】的 <tag> 注入样式"""
        # 匹配没有 style= 属性的开标签
        # 模式: <tag空格...> 但不含 style=（允许有其他属性如 id, class）
        # 注意：需要避免匹配自闭合标签如 <br/> <img/> <hr/>
        if tag in ("hr", "img", "br"):
            # 自闭合标签
            pattern = re.compile(
                rf'<{tag}(\s[^>]*?)?/?>',
                re.IGNORECASE,
            )
        else:
            # 普通开标签
            pattern = re.compile(
                rf'<{tag}(\s[^>]*?)?>',
                re.IGNORECASE,
            )

        def replacer(m):
            full = m.group(0)
            attrs = m.group(1) or ""

            # 如果已有 style 属性，跳过（由 :::block 模板控制的）
            if re.search(r'\bstyle\s*=', attrs, re.IGNORECASE):
                return full

            # 注入 style
            attrs = attrs.rstrip()
            if attrs:
                return f"<{tag}{attrs} style=\"{style}\">"
            else:
                return f"<{tag} style=\"{style}\">"

        return pattern.sub(replacer, html)

    def _style_blockquote_paras(self, html: str) -> str:
        """给 blockquote 内的 <p> 加样式（覆盖外层的 p 样式）"""
        bq_p_style = "margin:0 0 8px;color:#3D3A36;line-height:1.8;"

        # 简单方式：找到 <blockquote>...</blockquote> 内的裸 <p> 并替换
        # 由于 blockquote 可嵌套，这里用逐段替换
        result = []
        i = 0
        while i < len(html):
            bq_start = html.find("<blockquote", i)
            if bq_start == -1:
                result.append(html[i:])
                break

            result.append(html[i:bq_start])

            # 找到对应的 </blockquote>
            depth = 1
            j = html.find(">", bq_start) + 1  # 跳过开标签
            while depth > 0 and j < len(html):
                next_open = html.find("<blockquote", j)
                next_close = html.find("</blockquote>", j)
                if next_close == -1:
                    break
                if next_open != -1 and next_open < next_close:
                    depth += 1
                    j = next_open + 12
                else:
                    depth -= 1
                    if depth == 0:
                        inner = html[bq_start:next_close + 13]
                        # 对内部裸 <p> 注入样式
                        inner = self._inject_bare_tags(inner, "p", bq_p_style)
                        result.append(inner)
                        i = next_close + 13
                        break
                    j = next_close + 13

            if depth > 0:
                result.append(html[bq_start:])
                break

        return "".join(result)

    def _style_pre_code(self, html: str) -> str:
        """给 <pre> 内的 <code> 去掉背景色（继承 pre 的背景）"""
        pre_code_style = "background:none;padding:0;color:inherit;font-size:inherit;"

        result = []
        i = 0
        while i < len(html):
            pre_start = html.find("<pre", i)
            if pre_start == -1:
                result.append(html[i:])
                break

            result.append(html[i:pre_start])

            # 找对应的 </pre>
            pre_open_end = html.find(">", pre_start) + 1
            pre_close = html.find("</pre>", pre_open_end)
            if pre_close == -1:
                result.append(html[pre_start:])
                break

            inner = html[pre_open_end:pre_close]
            # 对 <pre> 内的裸 <code> 注入样式
            inner = self._inject_bare_tags(inner, "code", pre_code_style)

            result.append(html[pre_start:pre_open_end])
            result.append(inner)
            result.append(html[pre_close:pre_close + 6])
            i = pre_close + 6

        return "".join(result)
