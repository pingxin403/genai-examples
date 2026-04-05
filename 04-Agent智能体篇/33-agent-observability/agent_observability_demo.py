"""Agent可观测性演示"""
from dataclasses import dataclass, field
from datetime import datetime
import time, random

@dataclass
class ThoughtStep:
    step_id: int
    thought: str
    action: str = ""
    action_input: str = ""
    observation: str = ""
    tokens_used: int = 0
    latency_ms: float = 0

class ThoughtChainLogger:
    def __init__(self):
        self.chains = {}
    def start(self, rid):
        self.chains[rid] = []
    def log(self, rid, step):
        self.chains.setdefault(rid, []).append(step)
    def print_chain(self, rid):
        for s in self.chains.get(rid, []):
            print(f"  Step {s.step_id}: {s.thought[:60]}")
            if s.action:
                print(f"    → {s.action}({s.action_input[:40]}) = {s.observation[:40]}")
            print(f"    tokens={s.tokens_used}, latency={s.latency_ms}ms")

class TokenTracker:
    def __init__(self):
        self.records = []
    def record(self, step, inp_tok, out_tok):
        cost = (inp_tok * 0.0025 + out_tok * 0.01) / 1000
        self.records.append({"step": step, "tokens": inp_tok+out_tok, "cost": round(cost, 6)})
    def summary(self):
        total = sum(r["cost"] for r in self.records)
        return {"total_cost": round(total, 6), "steps": self.records}

def main():
    print("=" * 50)
    print("🔁 Agent可观测性演示")
    print("=" * 50)

    logger = ThoughtChainLogger()
    tracker = TokenTracker()
    rid = "req_001"
    logger.start(rid)

    steps = [
        ThoughtStep(1, "用户问上个月销售额，需要查数据库", "query_db", "SELECT SUM(amount) FROM sales WHERE month='2024-03'", "总额: 1,250,000", 800, 150),
        ThoughtStep(2, "需要计算同比增长率", "python_exec", "growth = (1250000-1100000)/1100000", "增长率: 13.6%", 500, 80),
        ThoughtStep(3, "生成最终回答", "", "", "", 600, 200),
    ]

    for s in steps:
        logger.log(rid, s)
        tracker.record(f"step_{s.step_id}", s.tokens_used // 2, s.tokens_used // 2)

    print("\n--- 思考链日志 ---")
    logger.print_chain(rid)

    print("\n--- Token消耗归因 ---")
    summary = tracker.summary()
    for r in summary["steps"]:
        print(f"  {r['step']}: {r['tokens']} tokens, ${r['cost']}")
    print(f"  总成本: ${summary['total_cost']}")

    print("\n✅ 演示完成！")

if __name__ == "__main__":
    main()
