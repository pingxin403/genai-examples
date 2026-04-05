"""评估偏差演示：偏差检测、测试集质量评估"""


class EvalBiasDetector:
    def __init__(self):
        self.offline: dict[str, float] = {}
        self.online: dict[str, float] = {}

    def set_offline(self, m: dict):
        self.offline = m

    def set_online(self, m: dict):
        self.online = m

    def detect(self) -> list[dict]:
        gaps = []
        for k in self.offline:
            if k in self.online:
                diff = abs(self.offline[k] - self.online[k])
                if diff > 0.1:
                    gaps.append({"metric": k, "offline": self.offline[k],
                                "online": self.online[k], "gap": round(diff, 2),
                                "severity": "high" if diff > 0.2 else "medium"})
        return gaps


class TestSetQualityChecker:
    def check(self, test_queries: list[str], real_queries: list[str]) -> dict:
        test_types = {self._classify(q) for q in test_queries}
        real_types = {self._classify(q) for q in real_queries}
        missing = real_types - test_types
        return {"test_types": len(test_types), "real_types": len(real_types),
                "missing": list(missing),
                "coverage": f"{(1 - len(missing)/max(len(real_types),1))*100:.0f}%"}

    @staticmethod
    def _classify(q: str) -> str:
        if "?" in q or "？" in q:
            return "question"
        if len(q) < 10:
            return "short"
        if any(w in q for w in ["怎么", "如何", "什么"]):
            return "how-to"
        return "statement"


def main():
    print("=" * 60)
    print("评估偏差演示")
    print("=" * 60)

    print("\n--- 离线-在线偏差检测 ---")
    detector = EvalBiasDetector()
    detector.set_offline({"recall": 0.88, "faithfulness": 0.92, "relevance": 0.85})
    detector.set_online({"recall": 0.62, "faithfulness": 0.78, "relevance": 0.70})

    gaps = detector.detect()
    for g in gaps:
        icon = "🔴" if g["severity"] == "high" else "🟡"
        print(f"  {icon} {g['metric']}: 离线={g['offline']} → 在线={g['online']} "
              f"(偏差={g['gap']})")

    print("\n--- 测试集质量评估 ---")
    checker = TestSetQualityChecker()
    result = checker.check(
        test_queries=["退货流程是什么？", "会员权益有哪些？"],
        real_queries=["退货流程是什么？", "买错了咋退", "不想要了", "退货扣运费吗？",
                      "怎么申请退款", "能退不"],
    )
    print(f"  测试集类型: {result['test_types']}")
    print(f"  真实查询类型: {result['real_types']}")
    print(f"  覆盖率: {result['coverage']}")
    if result["missing"]:
        print(f"  缺失类型: {result['missing']}")

    print(f"\n{'=' * 60}")
    print("核心: 从线上采样+包含拒答case+持续更新 = 真实评估")
    print("=" * 60)


if __name__ == "__main__":
    main()
