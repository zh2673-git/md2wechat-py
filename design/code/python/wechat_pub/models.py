"""统一数据模型"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# ============================================================
# CLI JSON Envelope（Agent-native 输出契约）
# ============================================================
@dataclass
class CLIResponse:
    success: bool = True
    code: str = "OK"
    message: str = ""
    schema_version: str = "v1"
    status: str = "completed"   # completed | action_required | failed
    retryable: bool = False
    data: dict = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 文章元数据
# ============================================================
@dataclass
class Metadata:
    title: str = ""
    author: str = ""
    digest: str = ""


# ============================================================
# 转换请求/结果
# ============================================================
@dataclass
class ConvertRequest:
    markdown: str = ""
    file_path: str = ""
    mode: str = "api"
    theme: str = "claude-warm"
    title: str = ""
    author: str = ""
    digest: str = ""
    output: str = ""


@dataclass
class ImageRef:
    index: int = 0
    original: str = ""
    placeholder: str = ""


@dataclass
class ConvertResult:
    success: bool = True
    html: str = ""
    error: str = ""
    images: list = field(default_factory=list)
    title: str = ""
    author: str = ""
    digest: str = ""
    theme: str = ""


# ============================================================
# 检查结果
# ============================================================
@dataclass
class CheckItem:
    level: str = "info"    # info | warning | error
    message: str = ""


@dataclass
class InspectResult:
    metadata: Metadata = field(default_factory=Metadata)
    readiness: str = "ready"   # ready | warning | error
    checks: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "metadata": asdict(self.metadata),
            "readiness": self.readiness,
            "checks": [asdict(c) for c in self.checks],
        }


# ============================================================
# 排版模块规格
# ============================================================
@dataclass
class ModuleField:
    name: str = ""
    description: str = ""
    required: bool = False
    example: str = ""


@dataclass
class ModuleSpec:
    name: str = ""
    category: str = ""
    serves: list = field(default_factory=list)
    description: str = ""
    when_to_use: str = ""
    when_not_to_use: str = ""
    anti_pattern: str = ""
    fields_required: list = field(default_factory=list)
    fields_optional: list = field(default_factory=list)
    example: str = ""
