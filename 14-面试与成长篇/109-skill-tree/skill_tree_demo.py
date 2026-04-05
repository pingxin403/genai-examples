"""AI工程师技能树演示：评估、学习路径"""


class AISkillTree:
    LEVELS = {
        "L1": ["Prompt编写", "API调用", "框架使用", "Python基础"],
        "L2": ["RAG搭建", "Agent开发", "性能优化", "测试评估"],
        "L3": ["系统架构", "成本优化", "安全设计", "评估体系"],
        "L4": ["技术选型", "团队建设", "业务对齐", "技术规划"],
    }

    def assess(self, skills: dict[str, float]) -> dict:
        level_scores = {}
        for level, items in self.LEVELS.items():
            scores = [skills.get(s, 0) for s in items]
            level_scores[level] = sum(scores) / len(scores)
        current = "L1"
        for lv, score in level_scores.items():
            if score >= 0.7:
                current = lv
        return {"current": current, "scores": {k: round(v, 2) for k, v in level_scores.items()}}


class LearningPathGenerator:
    PATHS = {
        "L1→L2": ["搭建RAG系统(2周)", "Agent开发实战(2周)", "性能优化(1周)"],
        "L2→L3": ["系统架构设计(3周)", "评估体系建设(2周)", "安全方案(2周)"],
        "L3→L4": ["技术选型实践(2周)", "团队指导(持续)", "业务对齐(持续)"],
    }

    def generate(self, current: str, target: str) -> list[str]:
        return self.PATHS.get(f"{current}→{target}", ["请咨询导师"])


def main():
    print("=" * 60)
    print("AI工程师技能树演示")
    print("=" * 60)

    tree = AISkillTree()
    skills = {
        "Prompt编写": 0.9, "API调用": 0.9, "框架使用": 0.8, "Python基础": 0.9,
        "RAG搭建": 0.7, "Agent开发": 0.6, "性能优化": 0.5, "测试评估": 0.4,
        "系统架构": 0.3, "成本优化": 0.2, "安全设计": 0.2, "评估体系": 0.1,
        "技术选型": 0.1, "团队建设": 0.0, "业务对齐": 0.1, "技术规划": 0.0,
    }

    result = tree.assess(skills)
    print(f"\n  当前等级: {result['current']}")
    for lv, score in result["scores"].items():
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"    {lv} {bar} {score:.0%}")

    print("\n--- 学习路径 ---")
    gen = LearningPathGenerator()
    path = gen.generate(result["current"], "L2")
    print(f"  {result['current']}→L2:")
    for step in path:
        print(f"    📚 {step}")

    print(f"\n{'=' * 60}")
    print("核心: 做完整的事>学更多技术, 边学边做>只看教程")
    print("=" * 60)


if __name__ == "__main__":
    main()
