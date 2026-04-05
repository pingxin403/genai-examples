"""
工具调用安全边界演示
配套文章：《工具调用（Tool Calling）的安全边界设计》
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ToolDef:
    name: str
    risk_level: RiskLevel
    permissions: list[str] = field(default_factory=list)


class ToolRegistry:
    def __init__(self):
        self.tools = {}
    def register(self, tool_def, handler):
        self.tools[tool_def.name] = {"def": tool_def, "handler": handler}
    def get(self, name):
        return self.tools.get(name)


class PermissionChecker:
    def __init__(self):
        self.user_perms = {}
    def grant(self, uid, perms):
        self.user_perms[uid] = set(perms)
    def check(self, uid, tool_def):
        perms = self.user_perms.get(uid, set())
        missing = set(tool_def.permissions) - perms
        return (not missing, f"缺少: {missing}" if missing else "通过")


class AuditLogger:
    def __init__(self):
        self.logs = []
    def log(self, uid, tool, params, status):
        self.logs.append({"ts": datetime.now().isoformat(), "uid": uid,
                          "tool": tool, "params": str(params)[:100], "status": status})
        print(f"  [审计] {uid} → {tool} → {status}")


class SecureToolExecutor:
    def __init__(self, registry, checker, logger):
        self.registry = registry
        self.checker = checker
        self.logger = logger

    def execute(self, uid, tool_name, params):
        # 1. 注册检查
        entry = self.registry.get(tool_name)
        if not entry:
            self.logger.log(uid, tool_name, params, "REJECTED:未注册")
            return {"error": f"工具{tool_name}未注册"}

        tool_def = entry["def"]

        # 2. 权限校验
        ok, msg = self.checker.check(uid, tool_def)
        if not ok:
            self.logger.log(uid, tool_name, params, f"REJECTED:{msg}")
            return {"error": msg}

        # 3. 敏感操作确认
        if tool_def.risk_level == RiskLevel.HIGH:
            print(f"  ⚠️ 高风险操作'{tool_name}'需要确认")
            self.logger.log(uid, tool_name, params, "PENDING_CONFIRM")
            return {"status": "pending_confirmation", "tool": tool_name}

        # 4. 执行
        result = entry["handler"](params)
        self.logger.log(uid, tool_name, params, "SUCCESS")
        return result


def main():
    print("=" * 50)
    print("🛠️ 工具调用安全边界演示")
    print("=" * 50)

    registry = ToolRegistry()
    checker = PermissionChecker()
    logger = AuditLogger()

    # 注册工具
    registry.register(ToolDef("query_order", RiskLevel.LOW, ["read"]),
                      lambda p: {"order": "ORD-001", "status": "已发货"})
    registry.register(ToolDef("cancel_order", RiskLevel.HIGH, ["read", "write"]),
                      lambda p: {"cancelled": True})

    # 授权
    checker.grant("user_001", ["read"])
    checker.grant("admin_001", ["read", "write"])

    executor = SecureToolExecutor(registry, checker, logger)

    # 测试场景
    tests = [
        ("user_001", "query_order", {}, "普通用户查询(应通过)"),
        ("user_001", "cancel_order", {}, "普通用户取消(应拒绝-权限不足)"),
        ("admin_001", "cancel_order", {}, "管理员取消(应需确认)"),
        ("user_001", "unknown_tool", {}, "调用未注册工具(应拒绝)"),
    ]

    for uid, tool, params, desc in tests:
        print(f"\n--- {desc} ---")
        result = executor.execute(uid, tool, params)
        print(f"  结果: {result}")

    print(f"\n--- 审计日志({len(logger.logs)}条) ---")
    for log in logger.logs:
        print(f"  {log['uid']} | {log['tool']} | {log['status']}")

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
