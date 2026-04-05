"""
Prompt性能分析演示：Token计数、成本归因与预算预警

配套文章：《Prompt性能分析：一个Prompt吃掉多少Token？》
仓库地址：https://github.com/pingxin403/genai-examples/tree/main/02-Prompt工程篇/16-prompt-performance/
"""

import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from collections import defaultdict

try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    print("提示：安装 tiktoken 可获得精确Token计数 (pip install tiktoken)")


# ============================================================
# 1. 模型价格配置（美元/1M tokens）
# ============================================================

MODEL_PRICING = {
    "gpt-4o":              {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":         {"input": 0.15,  "output": 0.60},
    "claude-3.5-sonnet":   {"input": 3.00,  "output": 15.00},
    "deepseek-v3":         {"input": 0.27,  "output": 1.10},
}


# ============================================================
# 2. Token计数工具
# ============================================================

def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """精确计算文本的Token数量"""
    if HAS_TIKTOKEN:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    else:
        # 粗略估算：中文约1.5字/token，英文约4字符/token
        return max(len(text) // 2, 1)


# ============================================================
# 3. Token消耗记录
# ============================================================

@dataclass
class TokenUsage:
    """单次请求的Token消耗记录"""
    request_id: str
    user_id: str
    scenario: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    timestamp: datetime = field(default_factory=datetime.now)
    prompt_version: str = "v1"

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        pricing = MODEL_PRICING.get(self.model, {"input": 0, "output": 0})
        input_cost = self.prompt_tokens * pricing["input"] / 1_000_000
        output_cost = self.completion_tokens * pricing["output"] / 1_000_000
        return round(input_cost + output_cost, 6)


# ============================================================
# 4. 成本归因引擎
# ============================================================

class CostAttributionEngine:
    """按多维度聚合Token消耗与成本"""

    def __init__(self):
        self.records: list[TokenUsage] = []
        self._by_user = defaultdict(list)
        self._by_scenario = defaultdict(list)
        self._by_model = defaultdict(list)

    def record(self, user_id: str, scenario: str, model: str,
               prompt_tokens: int, completion_tokens: int,
               prompt_version: str = "v1") -> TokenUsage:
        usage = TokenUsage(
            request_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            scenario=scenario,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_version=prompt_version,
        )
        self.records.append(usage)
        self._by_user[user_id].append(usage)
        self._by_scenario[scenario].append(usage)
        self._by_model[model].append(usage)
        return usage

    def cost_by_scenario(self) -> dict:
        result = {}
        for scenario, usages in self._by_scenario.items():
            total_cost = sum(u.cost_usd for u in usages)
            total_tokens = sum(u.total_tokens for u in usages)
            result[scenario] = {
                "total_cost_usd": round(total_cost, 4),
                "total_tokens": total_tokens,
                "request_count": len(usages),
                "avg_tokens_per_request": total_tokens // max(len(usages), 1),
            }
        return result

    def cost_by_user(self) -> dict:
        result = {}
        for user_id, usages in self._by_user.items():
            total_cost = sum(u.cost_usd for u in usages)
            result[user_id] = {
                "total_cost_usd": round(total_cost, 4),
                "request_count": len(usages),
                "avg_cost_per_request": round(
                    total_cost / max(len(usages), 1), 6
                ),
            }
        return result

    def top_expensive_requests(self, n: int = 5) -> list:
        sorted_records = sorted(
            self.records, key=lambda r: r.cost_usd, reverse=True
        )
        return [
            {
                "request_id": r.request_id,
                "user_id": r.user_id,
                "scenario": r.scenario,
                "model": r.model,
                "prompt_tokens": r.prompt_tokens,
                "completion_tokens": r.completion_tokens,
                "total_tokens": r.total_tokens,
                "cost_usd": r.cost_usd,
            }
            for r in sorted_records[:n]
        ]


# ============================================================
# 5. 预算预警系统
# ============================================================

class BudgetAlert:
    """预算预警：日/月预算检查 + 单用户异常检测"""

    def __init__(self, daily_budget_usd: float, monthly_budget_usd: float):
        self.daily_budget = daily_budget_usd
        self.monthly_budget = monthly_budget_usd

    def check(self, engine: CostAttributionEngine) -> list:
        alerts = []
        today = datetime.now().date()

        # 日预算检查
        daily_cost = sum(
            r.cost_usd for r in engine.records
            if r.timestamp.date() == today
        )
        if self.daily_budget > 0:
            daily_ratio = daily_cost / self.daily_budget
            if daily_ratio >= 1.0:
                alerts.append({
                    "level": "CRITICAL",
                    "message": (
                        f"日预算已超支！已消耗 ${daily_cost:.4f}，"
                        f"预算 ${self.daily_budget:.2f}"
                    ),
                })
            elif daily_ratio >= 0.8:
                alerts.append({
                    "level": "WARNING",
                    "message": (
                        f"日预算已使用 {daily_ratio:.0%}，"
                        f"已消耗 ${daily_cost:.4f}"
                    ),
                })

        # 单用户异常检测
        user_costs = engine.cost_by_user()
        for uid, info in user_costs.items():
            if self.daily_budget > 0 and info["total_cost_usd"] > self.daily_budget * 0.3:
                alerts.append({
                    "level": "WARNING",
                    "message": (
                        f"用户 {uid} 消耗异常，"
                        f"占日预算 "
                        f"{info['total_cost_usd']/self.daily_budget:.0%}"
                    ),
                })

        return alerts


# ============================================================
# 6. 演示主流程
# ============================================================

def demo_token_counting():
    """演示Token计数"""
    print("=" * 60)
    print("📏 Token计数演示")
    print("=" * 60)

    samples = [
        ("Hello, how are you?", "英文短句"),
        ("请帮我写一份项目周报，包含本周完成的任务和下周计划。", "中文短句"),
        ("You are a helpful customer service assistant. " * 20, "长系统提示词"),
    ]

    for text, label in samples:
        tokens = count_tokens(text)
        print(f"  [{label}] {tokens} tokens — \"{text[:40]}...\"")

    # 输入输出成本差异演示
    print("\n💰 输入vs输出成本差异（1000 tokens）：")
    for model, pricing in MODEL_PRICING.items():
        input_cost = 1000 * pricing["input"] / 1_000_000
        output_cost = 1000 * pricing["output"] / 1_000_000
        ratio = pricing["output"] / pricing["input"]
        print(
            f"  {model:25s} 输入=${input_cost:.6f}  "
            f"输出=${output_cost:.6f}  "
            f"输出/输入={ratio:.1f}x"
        )


def demo_cost_attribution():
    """演示多维度成本归因"""
    print("\n" + "=" * 60)
    print("📊 成本归因演示")
    print("=" * 60)

    engine = CostAttributionEngine()

    # 模拟多场景、多用户的API调用
    test_data = [
        ("user_001", "customer_service", "gpt-4o",      1200, 350),
        ("user_001", "customer_service", "gpt-4o",      1500, 420),
        ("user_002", "search",           "gpt-4o-mini",  800, 150),
        ("user_002", "search",           "gpt-4o-mini",  600, 120),
        ("user_003", "summary",          "gpt-4o",      3500, 800),
        ("user_003", "summary",          "gpt-4o",      4200, 950),
        ("user_004", "customer_service", "gpt-4o-mini",  900, 200),
        ("test_bot", "load_test",        "gpt-4o",      8000, 2000),
        ("test_bot", "load_test",        "gpt-4o",      8500, 2200),
        ("test_bot", "load_test",        "gpt-4o",      7800, 1900),
    ]

    for user_id, scenario, model, pt, ct in test_data:
        engine.record(user_id, scenario, model, pt, ct)

    # 按场景汇总
    print("\n🏷️  按场景汇总：")
    for scenario, info in engine.cost_by_scenario().items():
        print(f"  {scenario:20s} | "
              f"${info['total_cost_usd']:.4f} | "
              f"{info['request_count']}次 | "
              f"平均{info['avg_tokens_per_request']} tokens/次")

    # 按用户汇总
    print("\n👤 按用户汇总：")
    for user_id, info in engine.cost_by_user().items():
        print(f"  {user_id:15s} | "
              f"${info['total_cost_usd']:.4f} | "
              f"{info['request_count']}次 | "
              f"平均${info['avg_cost_per_request']:.6f}/次")

    # 最贵请求
    print("\n🔥 最贵的3个请求：")
    for i, req in enumerate(engine.top_expensive_requests(3), 1):
        print(f"  #{i} [{req['user_id']}] {req['scenario']} — "
              f"{req['total_tokens']} tokens — ${req['cost_usd']:.6f}")

    return engine


def demo_budget_alert(engine: CostAttributionEngine):
    """演示预算预警"""
    print("\n" + "=" * 60)
    print("🚨 预算预警演示")
    print("=" * 60)

    alert = BudgetAlert(daily_budget_usd=0.50, monthly_budget_usd=15.00)
    alerts = alert.check(engine)

    if alerts:
        for a in alerts:
            icon = "🔴" if a["level"] == "CRITICAL" else "🟡"
            print(f"  {icon} [{a['level']}] {a['message']}")
    else:
        print("  ✅ 预算正常，无告警")


# ============================================================
# 主入口
# ============================================================

if __name__ == "__main__":
    print("📊 Prompt性能分析 — Token计数、成本归因与预算预警\n")

    demo_token_counting()
    engine = demo_cost_attribution()
    demo_budget_alert(engine)

    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print("完整代码：https://github.com/pingxin403/genai-examples/"
          "tree/main/02-Prompt工程篇/16-prompt-performance/")
