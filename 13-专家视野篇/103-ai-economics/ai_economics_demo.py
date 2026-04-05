"""AI成本经济学演示：全成本计算、自建vs API分析"""


class AICostCalculator:
    def __init__(self):
        self.costs = {"compute": 0.0, "token": 0.0, "human": 0.0}

    def add_compute(self, gpu_hours: float, price: float):
        self.costs["compute"] += gpu_hours * price

    def add_token(self, input_t: int, output_t: int,
                  in_price: float = 0.03, out_price: float = 0.06):
        self.costs["token"] += input_t / 1000 * in_price + output_t / 1000 * out_price

    def add_human(self, people: int, salary: float, months: float):
        self.costs["human"] += people * salary * months

    def report(self) -> dict:
        total = sum(self.costs.values())
        pct = {k: f"{v/total*100:.1f}%" for k, v in self.costs.items()} if total else {}
        return {"breakdown": {k: round(v) for k, v in self.costs.items()},
                "total": round(total), "percentages": pct}


class BuildVsBuyAnalyzer:
    def analyze(self, monthly_calls: int, avg_tokens: int,
                api_price: float = 0.03, gpu_cost: float = 5000,
                setup: float = 50000) -> dict:
        api_monthly = monthly_calls * avg_tokens / 1000 * api_price
        self_monthly = gpu_cost + setup / 12
        return {
            "api_monthly": round(api_monthly),
            "self_monthly": round(self_monthly),
            "recommendation": "自建" if api_monthly > self_monthly else "API",
            "savings": round(abs(api_monthly - self_monthly)),
        }


def main():
    print("=" * 60)
    print("AI成本经济学演示")
    print("=" * 60)

    print("\n--- AI全成本计算 ---")
    calc = AICostCalculator()
    calc.add_token(5_000_000, 2_000_000)
    calc.add_compute(720, 10)
    calc.add_human(3, 40000, 1)
    r = calc.report()
    print(f"  总成本: ¥{r['total']:,}")
    for k, v in r["breakdown"].items():
        print(f"    {k:<10} ¥{v:>8,}  ({r['percentages'][k]})")

    print("\n--- 自建 vs API 盈亏分析 ---")
    analyzer = BuildVsBuyAnalyzer()
    for calls in [10_000, 100_000, 1_000_000]:
        r = analyzer.analyze(calls, 1000)
        print(f"  月调用{calls:>10,}次: API=¥{r['api_monthly']:,} vs "
              f"自建=¥{r['self_monthly']:,} → {r['recommendation']} "
              f"(省¥{r['savings']:,}/月)")

    print(f"\n{'=' * 60}")
    print("核心: 全成本视图+盈亏分析+模型路由 = 成本最优")
    print("=" * 60)


if __name__ == "__main__":
    main()
