"""AI架构师核心能力演示：决策框架、AI适用性判断"""


class ArchitectDecisionFramework:
    def evaluate(self, proposal: dict) -> dict:
        scores = {
            "business": self._biz(proposal),
            "technical": self._tech(proposal),
            "cost": self._cost(proposal),
            "risk": self._risk(proposal),
        }
        avg = sum(scores.values()) / len(scores)
        rec = "推荐" if avg > 0.7 else "需调整" if avg > 0.4 else "不推荐"
        concerns = [k for k, v in scores.items() if v < 0.5]
        return {"scores": {k: round(v, 2) for k, v in scores.items()},
                "overall": round(avg, 2), "recommendation": rec, "concerns": concerns}

    def _biz(self, p):
        return sum([bool(p.get("problem")), bool(p.get("metrics")),
                    p.get("user_validated", False)]) / 3

    def _tech(self, p):
        return sum([p.get("proven", False), p.get("poc", False),
                    p.get("team_ready", False)]) / 3

    def _cost(self, p):
        return sum([p.get("roi", 0) > 1.0, p.get("within_budget", False)]) / 2

    def _risk(self, p):
        return sum([p.get("fallback", False), p.get("monitoring", False),
                    p.get("reversible", False)]) / 3


class ShouldUseAI:
    def decide(self, scenario: dict) -> dict:
        if scenario.get("deterministic"):
            return {"use_ai": False, "reason": "确定性问题，用规则引擎"}
        if scenario.get("data", 0) < 100:
            return {"use_ai": False, "reason": "数据不足"}
        if not scenario.get("tolerates_errors", True):
            return {"use_ai": False, "reason": "零容错，不适合AI"}
        if scenario.get("roi", 0) < 1.5:
            return {"use_ai": False, "reason": "ROI不足"}
        return {"use_ai": True, "reason": "适合AI，建议POC验证"}


def main():
    print("=" * 60)
    print("AI架构师核心能力演示")
    print("=" * 60)

    print("\n--- 架构决策评估 ---")
    framework = ArchitectDecisionFramework()
    proposals = [
        {"name": "AI客服", "problem": "客服效率低", "metrics": ["满意度"],
         "user_validated": True, "proven": True, "poc": True, "team_ready": True,
         "roi": 2.5, "within_budget": True, "fallback": True,
         "monitoring": True, "reversible": True},
        {"name": "AI交易", "problem": "自动交易", "metrics": [],
         "user_validated": False, "proven": False, "poc": False, "team_ready": False,
         "roi": 0.8, "within_budget": False, "fallback": False,
         "monitoring": False, "reversible": False},
    ]
    for p in proposals:
        r = framework.evaluate(p)
        print(f"\n  {p['name']}: {r['recommendation']} (得分: {r['overall']})")
        for k, v in r["scores"].items():
            print(f"    {k:<12} {v:.0%}")
        if r["concerns"]:
            print(f"    ⚠️ 关注: {', '.join(r['concerns'])}")

    print("\n--- 该不该用AI ---")
    decider = ShouldUseAI()
    scenarios = [
        {"name": "表单查询", "deterministic": True, "data": 1000},
        {"name": "智能客服", "deterministic": False, "data": 5000,
         "tolerates_errors": True, "roi": 3.0},
        {"name": "医疗诊断", "deterministic": False, "data": 500,
         "tolerates_errors": False, "roi": 5.0},
    ]
    for s in scenarios:
        r = decider.decide(s)
        icon = "✅" if r["use_ai"] else "❌"
        print(f"  {icon} {s['name']:<10} → {r['reason']}")

    print(f"\n{'=' * 60}")
    print("核心: 判断力>技术力, 业务驱动>技术驱动")
    print("=" * 60)


if __name__ == "__main__":
    main()
