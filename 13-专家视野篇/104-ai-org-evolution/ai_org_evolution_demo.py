"""AI组织演进演示：成熟度评估、能力复用分析"""


class AIOrgMaturityAssessor:
    STAGES = {1: "散点探索", 2: "项目组", 3: "平台团队", 4: "卓越中心"}

    def assess(self, scores: dict[str, int]) -> dict:
        avg = sum(scores.values()) / len(scores) if scores else 0
        stage = 4 if avg >= 4 else 3 if avg >= 3 else 2 if avg >= 2 else 1
        gaps = [d for d, s in scores.items() if s < 3]
        return {"stage": stage, "name": self.STAGES[stage],
                "avg": round(avg, 1), "gaps": gaps}


class CapabilityReuseAnalyzer:
    def __init__(self):
        self.caps: dict[str, dict] = {}

    def register(self, name: str, teams: list[str], shared: bool):
        self.caps[name] = {"teams": teams, "shared": shared}

    def analyze(self) -> dict:
        total = len(self.caps)
        shared = sum(1 for c in self.caps.values() if c["shared"])
        dup = sum(1 for c in self.caps.values() if len(c["teams"]) > 1 and not c["shared"])
        return {"total": total, "shared": shared, "duplicated": dup,
                "reuse_rate": f"{shared/total*100:.0f}%" if total else "0%"}


def main():
    print("=" * 60)
    print("AI组织演进演示")
    print("=" * 60)

    print("\n--- 组织成熟度评估 ---")
    assessor = AIOrgMaturityAssessor()
    result = assessor.assess({
        "team": 3, "platform": 2, "process": 2, "culture": 3, "governance": 1
    })
    print(f"  当前阶段: {result['stage']} - {result['name']} (均分: {result['avg']})")
    if result["gaps"]:
        print(f"  待提升: {', '.join(result['gaps'])}")

    print("\n--- 能力复用分析 ---")
    analyzer = CapabilityReuseAnalyzer()
    analyzer.register("RAG系统", ["客服", "销售", "HR"], shared=False)
    analyzer.register("Embedding服务", ["客服", "销售"], shared=True)
    analyzer.register("Prompt管理", ["客服"], shared=False)
    analyzer.register("模型网关", ["客服", "销售", "HR"], shared=True)

    r = analyzer.analyze()
    print(f"  总能力: {r['total']}, 共享: {r['shared']}, 重复建设: {r['duplicated']}")
    print(f"  复用率: {r['reuse_rate']}")

    print(f"\n{'=' * 60}")
    print("核心: 评估成熟度→识别重复→统一平台→持续演进")
    print("=" * 60)


if __name__ == "__main__":
    main()
