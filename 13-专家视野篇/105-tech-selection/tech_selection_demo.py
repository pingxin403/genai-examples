"""技术选型框架演示：五维评估、锁定风险分析"""


class TechSelectionEvaluator:
    DIMS = {"maturity": 0.25, "ecosystem": 0.25, "lock_in": 0.20,
            "evolution": 0.15, "team_fit": 0.15}

    def evaluate(self, candidates: dict[str, dict]) -> list[dict]:
        results = []
        for name, scores in candidates.items():
            total = sum(scores.get(d, 0) * w for d, w in self.DIMS.items())
            results.append({"name": name, "total": round(total, 2), "scores": scores})
        return sorted(results, key=lambda x: x["total"], reverse=True)


class LockInAnalyzer:
    def analyze(self, tech: dict) -> dict:
        risk = 0
        factors = []
        if not tech.get("open_source"):
            risk += 3; factors.append("闭源")
        if not tech.get("standard_api"):
            risk += 2; factors.append("非标准API")
        if tech.get("alternatives", 0) < 2:
            risk += 2; factors.append("替代方案少")
        level = "低" if risk <= 3 else "中" if risk <= 5 else "高"
        return {"risk": risk, "level": level, "factors": factors}


def main():
    print("=" * 60)
    print("技术选型框架演示")
    print("=" * 60)

    print("\n--- 五维评估 ---")
    evaluator = TechSelectionEvaluator()
    results = evaluator.evaluate({
        "Milvus": {"maturity": 4, "ecosystem": 5, "lock_in": 4, "evolution": 4, "team_fit": 3},
        "Qdrant": {"maturity": 3, "ecosystem": 4, "lock_in": 5, "evolution": 4, "team_fit": 4},
        "Chroma": {"maturity": 3, "ecosystem": 3, "lock_in": 5, "evolution": 3, "team_fit": 5},
    })
    for i, r in enumerate(results):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else "  "
        print(f"  {medal} {r['name']:<10} 总分={r['total']}")

    print("\n--- 锁定风险分析 ---")
    analyzer = LockInAnalyzer()
    techs = [
        ("OpenAI API", {"open_source": False, "standard_api": True, "alternatives": 3}),
        ("Milvus", {"open_source": True, "standard_api": True, "alternatives": 5}),
        ("某闭源方案", {"open_source": False, "standard_api": False, "alternatives": 1}),
    ]
    for name, info in techs:
        r = analyzer.analyze(info)
        print(f"  {name:<15} 风险={r['level']} ({', '.join(r['factors']) or '无'})")

    print(f"\n{'=' * 60}")
    print("核心: 综合评估>单一指标, 主流>小众, 抽象层降低锁定")
    print("=" * 60)


if __name__ == "__main__":
    main()
