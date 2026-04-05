"""
Agent失控实录演示：熔断器、权限控制、成本监控
"""


class AgentCircuitBreaker:
    """Agent熔断器"""

    def __init__(self, max_iter=10, max_tokens=50000):
        self.max_iter = max_iter
        self.max_tokens = max_tokens
        self.iterations = 0
        self.total_tokens = 0
        self.history: list[str] = []

    def check(self, action: str, tokens: int) -> dict:
        self.iterations += 1
        self.total_tokens += tokens
        self.history.append(action)
        if len(self.history) >= 3 and len(set(self.history[-3:])) == 1:
            return {"stop": True, "reason": "重复动作检测"}
        if self.iterations > self.max_iter:
            return {"stop": True, "reason": "超过最大迭代"}
        if self.total_tokens > self.max_tokens:
            return {"stop": True, "reason": "Token超限"}
        return {"stop": False, "reason": ""}


class ToolPermissionManager:
    """工具权限管理"""

    def __init__(self):
        self.tools: dict[str, dict] = {}

    def register(self, name: str, risk: str, needs_approval: bool = False):
        self.tools[name] = {"risk": risk, "needs_approval": needs_approval}

    def check(self, tool: str) -> dict:
        if tool not in self.tools:
            return {"allowed": False, "reason": "工具未注册"}
        if self.tools[tool]["needs_approval"]:
            return {"allowed": False, "reason": "需要人工审批"}
        return {"allowed": True, "reason": "允许调用"}


class CostMonitor:
    """成本监控"""

    def __init__(self, budget: float = 10.0):
        self.budget = budget
        self.spent = 0.0

    def record(self, tokens: int, price_per_1k: float = 0.03) -> dict:
        cost = tokens / 1000 * price_per_1k
        self.spent += cost
        return {
            "cost": round(cost, 4),
            "total_spent": round(self.spent, 4),
            "remaining": round(self.budget - self.spent, 4),
            "over_budget": self.spent > self.budget,
        }


def main():
    print("=" * 60)
    print("Agent失控实录演示")
    print("=" * 60)

    # --- 熔断器演示 ---
    print("\n--- 熔断器演示 ---")
    breaker = AgentCircuitBreaker(max_iter=5, max_tokens=10000)
    actions = ["search", "search", "search", "analyze", "search", "search", "search"]
    for action in actions:
        result = breaker.check(action, 1500)
        status = "🛑 熔断" if result["stop"] else "✅ 继续"
        print(f"  {status} | 动作={action} | 迭代={breaker.iterations} | "
              f"Token={breaker.total_tokens}")
        if result["stop"]:
            print(f"    原因: {result['reason']}")
            break

    # --- 权限控制演示 ---
    print("\n--- 工具权限控制 ---")
    perm = ToolPermissionManager()
    perm.register("search", "low")
    perm.register("send_email", "medium", needs_approval=True)
    perm.register("delete_data", "high", needs_approval=True)

    for tool in ["search", "send_email", "delete_data", "unknown_tool"]:
        r = perm.check(tool)
        icon = "✅" if r["allowed"] else "🚫"
        print(f"  {icon} {tool:<15} → {r['reason']}")

    # --- 成本监控演示 ---
    print("\n--- 成本监控 ---")
    monitor = CostMonitor(budget=0.5)
    calls = [2000, 3000, 5000, 8000, 4000]
    for tokens in calls:
        r = monitor.record(tokens)
        icon = "🔴" if r["over_budget"] else "🟢"
        print(f"  {icon} {tokens} tokens → ${r['cost']} | "
              f"累计=${r['total_spent']} | 剩余=${r['remaining']}")

    print("\n" + "=" * 60)
    print("防护总结: 熔断器+权限控制+成本监控 = 三层防御")
    print("=" * 60)


if __name__ == "__main__":
    main()
