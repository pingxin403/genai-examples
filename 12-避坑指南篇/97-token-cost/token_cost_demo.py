"""Token成本失控演示：预算管理、上下文压缩、模型路由"""


class TokenBudgetManager:
    def __init__(self, daily_limit=100000, price_per_1k=0.03):
        self.daily_limit = daily_limit
        self.price = price_per_1k
        self.usage = 0

    def request(self, tokens: int) -> dict:
        if self.usage + tokens > self.daily_limit:
            return {"allowed": False, "reason": "日预算超限"}
        self.usage += tokens
        cost = self.usage / 1000 * self.price
        return {"allowed": True, "usage": self.usage, "cost_usd": round(cost, 4)}


class ContextCompressor:
    def compress(self, messages: list[dict], max_msgs: int = 6) -> list[dict]:
        system = [m for m in messages if m["role"] == "system"]
        others = [m for m in messages if m["role"] != "system"]
        if len(others) <= max_msgs:
            return messages
        summary = f"[历史摘要: {len(others) - max_msgs}条消息已压缩]"
        return system + [{"role": "system", "content": summary}] + others[-max_msgs:]


class ModelRouter:
    MODELS = {"simple": ("gpt-3.5", 0.002), "complex": ("gpt-4", 0.03)}

    def route(self, task_type: str) -> dict:
        model, price = self.MODELS.get(task_type, self.MODELS["simple"])
        return {"model": model, "price_per_1k": price}


def main():
    print("=" * 60)
    print("Token成本失控演示")
    print("=" * 60)

    print("\n--- Token预算管理 ---")
    mgr = TokenBudgetManager(daily_limit=10000)
    for tokens in [3000, 4000, 2000, 3000]:
        r = mgr.request(tokens)
        icon = "✅" if r["allowed"] else "🚫"
        print(f"  {icon} 请求{tokens} tokens → {r}")

    print("\n--- 上下文压缩 ---")
    comp = ContextCompressor()
    msgs = [{"role": "system", "content": "你是助手"}] + [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"消息{i}"}
        for i in range(10)
    ]
    compressed = comp.compress(msgs, max_msgs=4)
    print(f"  压缩前: {len(msgs)}条 → 压缩后: {len(compressed)}条")

    print("\n--- 模型路由 ---")
    router = ModelRouter()
    for task in ["simple", "complex", "simple"]:
        r = router.route(task)
        print(f"  {task:<10} → {r['model']} (${r['price_per_1k']}/1K)")

    print(f"\n{'=' * 60}")
    print("核心: 预算管理+上下文压缩+模型路由 = 成本可控")
    print("=" * 60)


if __name__ == "__main__":
    main()
