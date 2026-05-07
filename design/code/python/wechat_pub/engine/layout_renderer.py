"""排版引擎：:::block 语法渲染器"""
import re
import json
import yaml as yaml_lib
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..models import ModuleSpec


class LayoutRenderer:
    """:::block 排版模块渲染引擎 (Claude 风格)"""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.base_dir = Path(base_dir)

        # 加载模块定义
        self._modules: dict[str, ModuleSpec] = {}
        self._load_modules()

        # Jinja2 模板环境
        self._template_dir = self.base_dir / "templates"
        self._template_dir.mkdir(parents=True, exist_ok=True)
        self._env = Environment(
            loader=FileSystemLoader(str(self._template_dir)),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 注册自定义过滤器
        self._env.filters["nl2br"] = lambda s: s.replace("\n", "<br>") if s else ""

    # -----------------------------------------------------------
    # 模块加载
    # -----------------------------------------------------------
    def _load_modules(self):
        """扫描 layout/ 目录加载所有 YAML 模块定义"""
        import yaml
        layout_dir = self.base_dir / "layout"
        if not layout_dir.exists():
            return
        for yaml_file in sorted(layout_dir.rglob("*.yaml")):
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data or "name" not in data:
                continue
            spec = ModuleSpec(
                name=data["name"],
                category=data.get("category", ""),
                serves=data.get("serves", []),
                description=data.get("description", ""),
                when_to_use=data.get("when_to_use", ""),
                when_not_to_use=data.get("when_not_to_use", ""),
                anti_pattern=data.get("anti_pattern", ""),
                fields_required=[
                    {"name": f["name"], "description": f.get("description", "")}
                    for f in data.get("fields", {}).get("required", [])
                ],
                fields_optional=[
                    {"name": f["name"], "description": f.get("description", "")}
                    for f in data.get("fields", {}).get("optional", [])
                ],
                example=data.get("example", ""),
            )
            self._modules[spec.name] = spec

    # -----------------------------------------------------------
    # 模块发现
    # -----------------------------------------------------------
    def list_modules(self, serves: str = None, category: str = None) -> list[dict]:
        """列出模块"""
        result = []
        for spec in self._modules.values():
            if serves and serves not in spec.serves:
                continue
            if category and spec.category != category:
                continue
            result.append({
                "name": spec.name,
                "category": spec.category,
                "serves": spec.serves,
                "description": spec.description,
            })
        return result

    def show_module(self, name: str) -> dict:
        """查看模块完整规格"""
        spec = self._modules.get(name)
        if not spec:
            return {}
        return {
            "name": spec.name,
            "category": spec.category,
            "serves": spec.serves,
            "description": spec.description,
            "when_to_use": spec.when_to_use,
            "when_not_to_use": spec.when_not_to_use,
            "anti_pattern": spec.anti_pattern,
            "fields_required": spec.fields_required,
            "fields_optional": spec.fields_optional,
            "example": spec.example,
        }

    def render_syntax(self, name: str, **vars) -> str:
        """生成 :::block 语法块"""
        spec = self._modules.get(name)
        if not spec:
            return ""
        lines = [f":::{name}"]
        required = [f["name"] for f in spec.fields_required]
        optional = [f["name"] for f in spec.fields_optional]
        all_fields = required + optional
        for field_name in all_fields:
            if field_name in vars:
                lines.append(f"{field_name}: {vars[field_name]}")
        if not any(f in vars for f in all_fields):
            return spec.example
        lines.append(":::")
        return "\n".join(lines)

    # -----------------------------------------------------------
    # :::block 解析
    # -----------------------------------------------------------
    # 匹配 :::block name 或 :::name，捕获 body（含换行）
    # 使用 MULTILINE 让 ^ 匹配行首，精准定位结束的 :::
    BLOCK_PATTERN = re.compile(
        r'^:::\s*(?:block\s+)?(\w+)\s*$\n'   # :::block name  (行首)
        r'([\s\S]*?)'                           # body（非贪婪）
        r'^\s*:::\s*$',                         # 结束 :::  (行首)
        re.MULTILINE
    )

    def _parse_block_body(self, body: str) -> dict:
        """
        解析 block body，支持三种格式：
        1. YAML 格式（推荐）：key: value，支持列表、嵌套
        2. 管道符列表：| item1  → 解析为列表
        3. 纯文本：整个 body 作为 _raw
        """
        body = body.rstrip()
        if not body:
            return {}

        # 预处理：收集管道符开头的行（| item 格式）
        lines = body.split("\n")
        pipe_items = []
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|"):
                pipe_items.append(stripped[1:].strip())
            else:
                cleaned_lines.append(line)

        cleaned_body = "\n".join(cleaned_lines).strip()

        # 如果整个 body 都是管道符列表（cleaned_body 为空）
        if not cleaned_body and pipe_items:
            return {"_items": pipe_items}

        # 尝试 YAML 解析（最健壮的方式）
        if cleaned_body:
            try:
                data = yaml_lib.safe_load(cleaned_body)
                if isinstance(data, dict):
                    # 如果之前有管道符列表，合并进去
                    if pipe_items:
                        # 找到第一个列表类型字段，或创建 _items
                        list_field = None
                        for k, v in data.items():
                            if isinstance(v, list):
                                list_field = k
                                break
                        if list_field:
                            data[list_field].extend(pipe_items)
                        else:
                            data["_items"] = pipe_items
                    return data
            except Exception:
                pass

        # 兜底：简单 key: value 解析（支持中英文冒号）
        fields = {}
        if cleaned_body:
            current_key = None
            current_val_lines = []
            for line in cleaned_body.split("\n"):
                stripped = line.strip()
                # 检测是否是新的 key: value
                has_colon = (":" in stripped and not stripped.startswith("http")) or "：" in stripped
                if has_colon:
                    # 保存上一个字段
                    if current_key is not None:
                        fields[current_key] = "\n".join(current_val_lines).strip()
                    sep = "：" if "：" in stripped else ":"
                    key, _, val = stripped.partition(sep)
                    current_key = key.strip()
                    current_val_lines = [val.strip()] if val.strip() else []
                elif current_key is not None:
                    # 续行
                    current_val_lines.append(stripped)
                else:
                    # 纯文本行
                    if "_raw" not in fields:
                        fields["_raw"] = stripped
                    else:
                        fields["_raw"] += "\n" + stripped

            # 保存最后一个字段
            if current_key is not None:
                fields[current_key] = "\n".join(current_val_lines).strip()

        # 合并管道符列表
        if pipe_items:
            if "items" in fields and isinstance(fields["items"], list):
                fields["items"].extend(pipe_items)
            else:
                fields["_items"] = pipe_items

        return fields if fields else {"_raw": body}

    # -----------------------------------------------------------
    # 验证
    # -----------------------------------------------------------
    def validate(self, markdown: str) -> dict:
        """验证 Markdown 中的 :::block 语法"""
        blocks = self.BLOCK_PATTERN.findall(markdown)
        errors = []
        warnings = []
        for name, body in blocks:
            spec = self._modules.get(name)
            if not spec:
                warnings.append({
                    "module": name,
                    "level": "warning",
                    "message": f"未知模块 '{name}'，将保持原样输出"
                })
                continue
            fields = self._parse_block_body(body)
            for req in spec.fields_required:
                if req["name"] not in fields:
                    errors.append({
                        "module": name,
                        "level": "error",
                        "message": f"缺少必填字段 '{req['name']}' （{req.get('description', '')}）"
                    })
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # -----------------------------------------------------------
    # 渲染（核心方法）
    # -----------------------------------------------------------
    def render(self, markdown: str, theme: str = "claude-warm") -> str:
        """将 Markdown 中的 :::block 渲染为 HTML"""

        def _replace(match):
            name = match.group(1)
            body = match.group(2) or ""
            spec = self._modules.get(name)
            if not spec:
                return match.group(0)  # 未知模块保持原样
            fields = self._parse_block_body(body)
            html = self._render_to_html(name, spec, fields, theme)
            # 确保前后有空行，让 markdown-it 能正确解析后续内容
            return f"\n\n{html}\n\n"

        return self.BLOCK_PATTERN.sub(_replace, markdown)

    def _render_to_html(self, name: str, spec: ModuleSpec, fields: dict, theme: str) -> str:
        """单个 block → HTML"""
        from .theme_manager import ThemeManager
        tm = ThemeManager()
        theme_data = tm.get_theme_data(theme)
        c = theme_data["colors"]

        # 构建模板上下文：展平字段 + 主题颜色 + 排版 + 圆角变量
        t = theme_data.get("typography", {})
        r = theme_data.get("radius", {})
        s = theme_data.get("spacing", {})

        ctx = dict(fields)
        ctx.update({
            # 颜色
            "c_accent": c["accent"],
            "c_accent_light": c.get("accent-light", c["accent"]),
            "c_accent_mid": c.get("accent-mid", c["accent"]),
            "c_warm": c["warm"],
            "c_warm_light": c.get("warm-light", c["warm"]),
            "c_bg": c["bg"],
            "c_text": c["text"],
            "c_heading": c["heading"],
            "c_muted": c["muted"],
            "c_border": c["border"],
            "c_border_light": c.get("border-light", c["border"]),
            "c_card_bg": c.get("card-bg", "#fff"),
            "c_card_shadow": c.get("card-shadow", "rgba(0,0,0,0.04)"),
            "c_code_bg": c.get("code-bg", "#2D2A26"),
            "c_code_text": c.get("code-text", "#E8E2DA"),
            # 排版
            "f_base": t.get("font-size-base", "16px"),
            "f_h1": t.get("font-size-h1", "22px"),
            "f_h2": t.get("font-size-h2", "19px"),
            "f_h3": t.get("font-size-h3", "17px"),
            "f_family": t.get("font-family", "sans-serif"),
            "f_lh": t.get("line-height", "1.8"),
            # 圆角
            "r_card": r.get("card", "10px"),
            "r_button": r.get("button", "8px"),
            "r_image": r.get("image", "6px"),
            "r_pill": r.get("pill", "20px"),
            # 间距
            "s_section": s.get("section", "36px"),
            "s_paragraph": s.get("paragraph", "16px"),
            "s_block_gap": s.get("block-gap", "28px"),
        })

        # 尝试加载 Jinja2 模板
        template_name = f"{spec.category}/{name}.html"
        try:
            tmpl = self._env.get_template(template_name)
            return tmpl.render(**ctx)
        except Exception:
            return self._render_generic(name, fields, ctx)

    def _render_generic(self, name: str, fields: dict, ctx: dict = None) -> str:
        """通用兜底渲染"""
        title = fields.get("_title", "")
        parts = [f'<div class="wechat-pub-card block-{name}" style="padding:16px 20px;">']
        if title:
            accent = (ctx or {}).get("c_accent", "#7C3AED")
            parts.append(f'<h4 style="color:{accent};margin:0 0 12px;font-size:16px;">{title}</h4>')
        for key, val in fields.items():
            if key.startswith("_"):
                continue
            parts.append(f'<p style="margin:8px 0;line-height:1.6;">{val}</p>')
        parts.append("</div>")
        return "\n".join(parts)
