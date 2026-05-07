"""layout 命令 — 排版模块管理"""
import json
import click
from ..engine import LayoutRenderer


@click.group()
def layout():
    """管理高级排版模块（:::block 语法）"""
    pass


@layout.command()
@click.option('--serves', help='按目的筛选：attention/readability/memorability/conversion')
@click.option('--category', help='按类别筛选')
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
def list(serves, category, json_flag):
    """列出所有可用的排版模块"""
    renderer = LayoutRenderer()
    modules = renderer.list_modules(serves=serves, category=category)

    if json_flag:
        from .main import emit_json
        emit_json(True, data={"modules": modules, "total": len(modules)})
    else:
        click.echo(f"\n📦 排版模块 ({len(modules)} 个)")
        if serves:
            click.echo(f"   筛选: serves={serves}")
        for m in modules:
            click.echo(f"   {m['name']:15s} ({m['category']:12s}) {m['description']}")


@layout.command()
@click.argument('name')
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
def show(name, json_flag):
    """查看模块的完整规格"""
    renderer = LayoutRenderer()
    spec = renderer.show_module(name)

    if not spec:
        from .main import emit_json
        emit_json(False, code="LAYOUT_MODULE_NOT_FOUND", error=f"未知模块: {name}")
        return

    if json_flag:
        from .main import emit_json
        emit_json(True, data={"spec": spec})
    else:
        click.echo(f"\n📋 模块: {name}")
        click.echo(f"   类别: {spec['category']}")
        click.echo(f"   用途: {', '.join(spec.get('serves', []))}")
        click.echo(f"   说明: {spec.get('description', '')}")
        click.echo(f"   何时用: {spec.get('when_to_use', '')}")
        if spec.get("fields_required"):
            click.echo(f"\n   必填字段:")
            for f in spec["fields_required"]:
                click.echo(f"     - {f['name']}: {f.get('description', '')}")
        if spec.get("fields_optional"):
            click.echo(f"\n   可选字段:")
            for f in spec["fields_optional"]:
                click.echo(f"     - {f['name']}: {f.get('description', '')}")
        click.echo(f"\n   示例:")
        click.echo(f"     {spec.get('example', '')}")


@layout.command()
@click.option('--name', required=True, help='模块名')
@click.option('--var', 'vars', multiple=True, help='字段值 KEY=VALUE', default=[])
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
def render(name, vars, json_flag):
    """生成 :::block 语法块"""
    renderer = LayoutRenderer()
    kwargs = {}
    for v in vars:
        if "=" in v:
            k, _, val = v.partition("=")
            kwargs[k] = val
    syntax = renderer.render_syntax(name, **kwargs)

    if json_flag:
        from .main import emit_json
        emit_json(True, data={"syntax": syntax})
    else:
        click.echo(syntax)


@layout.command()
@click.option('--file', 'file_path', type=click.Path(exists=True), help='Markdown 文件')
@click.option('--json', 'json_flag', is_flag=True, help='JSON 输出')
def validate(file_path, json_flag):
    """验证 Markdown 中的 :::block 语法"""
    if not file_path:
        from .main import emit_json
        emit_json(False, code="LAYOUT_INVALID_FILTER", error="需要 --file 参数")
        return

    renderer = LayoutRenderer()
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    result = renderer.validate(content)

    if json_flag:
        code = "LAYOUT_VALIDATED" if result["valid"] else "LAYOUT_VALIDATE_HAS_ERRORS"
        from .main import emit_json
        emit_json(result["valid"], code=code, data=result)
    else:
        if result["valid"]:
            click.echo("✅ 排版语法验证通过")
        else:
            click.echo("❌ 排版语法有错误:")
            for e in result.get("errors", []):
                click.echo(f"   [{e['level']}] {e['message']}")
        for w in result.get("warnings", []):
            click.echo(f"   ⚠️  {w['message']}")
