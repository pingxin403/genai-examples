"""
工具调用（Tool Calling）的安全边界设计 - 完整演示
对应文章：GenAI/04-Agent智能体篇/31-工具调用Tool-Calling的安全边界设计.md

演示内容：
1. 工具注册与安全等级定义
2. 基于角色的权限校验 + 频率限制
3. 敏感操作人工确认机制
4. 全量审计日志（含参数脱敏）
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import time
import json


# ============================================================
# 第1层：工具注册
# ============================================================

class SecurityLevel(Enum):
    """工具安全等级"""
    L1_READ = "read_only"       # 只读查询
    L2_WRITE = "data_write"     # 数据写入
    L3_SENSITIVE = "sensitive"  # 敏感操作
    L4_DANGEROUS = "dangerous"  # 危险操作


@dataclass
class ToolDefinition:
    """工具定义，包含安全元数据"""
    name: str
    description: str
    function: Callable
    security_level: SecurityLevel
    required_permissions: list = field(default_factory=list)
    rate_limit: int = 100
    requires_confirmation: bool = False
    allowed_roles: list = field(default_factory=lambda: ["admin"])


class ToolRegistry:
    """安全工具注册表"""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        if tool.security_level in (SecurityLevel.L3_SENSITIVE, SecurityLevel.L4_DANGEROUS):
            tool.requires_confirmation = True
        self._tools[tool.name] = tool
        print(f"  ✅ 注册工具: {tool.name} (安全等级: {tool.security_level.value})")

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools_for_role(self, role: str) -> list[str]:
        return [
            name for name, tool in self._tools.items()
            if role in tool.allowed_roles
        ]
