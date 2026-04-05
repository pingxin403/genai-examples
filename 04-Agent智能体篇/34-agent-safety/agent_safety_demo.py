"""Agent防失控演示"""
import time

class LoopDetector:
    def __init__(self, max_iter=10, repeat_thresh=3):
        self.max_iter = max_iter
        self.repeat_thresh = repeat_thresh
        self.history = []
    def check(self, action, params):
        self.history.append(f"{action}:{str(params)[:30]}")
        if len(self.history) >= self.max_iter:
            return False, "最大迭代超限"
        recent = self.history[-self.repeat_thresh:]
        if len(recent) == self.repeat_thresh and len(set(recent)) == 1:
            return False, "检测到循环"
        return True, "正常"

class TokenBudget:
    def __init__(self, max_tokens=10000):
        self.max = max_tokens
        self.used = 0
    def consume(self, n):
        self.used += n
        return (self.used <= self.max, f"已用{self.used}/{self.max}")

class RateLimiter:
    def __init__(self, max_per_min=30):
        self.max = max_per_min
        self.times = []
    def check(self):
        now = time.time()
        self.times = [t for t in self.times if now - t < 60]
        if len(self.times) >= self.max:
            return False, "频率超限"
        self.times.append(now)
        return True, "正常"

def main():
    print("=" * 50)
    print("⚠️ Agent防失控演示")
    print("=" * 50)

    loop = LoopDetector(max_iter=8, repeat_thresh=3)
    budget = TokenBudget(max_tokens=5000)
    limiter = RateLimiter(max_per_min=50)

    actions = [
        ("query_db", {"sql": "SELECT *"}, 500),
        ("query_db", {"sql": "SELECT *"}, 500),
        ("query_db", {"sql": "SELECT *"}, 500),  # 第3次重复，应触发循环检测
        ("analyze", {"data": "report"}, 800),
        ("generate", {"type": "chart"}, 2000),
        ("generate", {"type": "chart"}, 2000),  # Token可能超限
    ]

    for action, params, tokens in actions:
        print(f"\n--- 执行: {action}({params}) ---")
        
        ok, msg = loop.check(action, params)
        if not ok:
            print(f"  🚫 循环检测: {msg}")
            continue
        
        ok, msg = budget.consume(tokens)
        if not ok:
            print(f"  🚫 Token预算: {msg}")
            continue
        
        ok, msg = limiter.check()
        if not ok:
            print(f"  🚫 频率限制: {msg}")
            continue
        
        print(f"  ✅ 执行成功 | {msg}")

    print(f"\n--- 统计 ---")
    print(f"  Token消耗: {budget.used}/{budget.max}")
    print(f"  迭代次数: {len(loop.history)}")
    print("\n✅ 演示完成！")

if __name__ == "__main__":
    main()
