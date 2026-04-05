"""大厂AI面试实录演示：问题分析、回答框架"""


class InterviewAnalyzer:
    def analyze(self, question: str, dimensions: list[str]) -> dict:
        frameworks = {
            "security": "识别威胁→分层防护→监控检测",
            "cost": "成本拆解→优化策略→效果保障",
            "business": "定义指标→对照实验→数据证明",
        }
        mistakes = {
            "security": "只考虑技术，忽略流程",
            "cost": "只想到Token，忽略人力",
            "business": "用技术指标代替业务指标",
        }
        return {
            "question": question,
            "dimensions": dimensions,
            "frameworks": [frameworks.get(d, "分析→方案→验证") for d in dimensions],
            "common_mistakes": [mistakes.get(d, "回答过于理论化") for d in dimensions],
        }


def main():
    print("=" * 60)
    print("大厂AI面试实录演示")
    print("=" * 60)

    analyzer = InterviewAnalyzer()
    questions = [
        ("RAG系统被恶意提取数据怎么防？", ["security"]),
        ("AI成本降50%不降效果怎么做？", ["cost"]),
        ("怎么证明AI比非AI方案更好？", ["business"]),
    ]

    for i, (q, dims) in enumerate(questions, 1):
        r = analyzer.analyze(q, dims)
        print(f"\n--- 灵魂问题{i} ---")
        print(f"  问题: {r['question']}")
        print(f"  考察: {', '.join(r['dimensions'])}")
        print(f"  框架: {'; '.join(r['frameworks'])}")
        print(f"  常见错误: {'; '.join(r['common_mistakes'])}")

    print(f"\n{'=' * 60}")
    print("核心: 权衡过程>直接结论, 业务指标>技术指标")
    print("=" * 60)


if __name__ == "__main__":
    main()
