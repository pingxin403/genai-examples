"""AI转型之路演示：路径规划、技能差距分析"""


class TransitionPlanner:
    PATHS = {
        "backend": {
            "advantages": ["系统设计", "性能优化", "运维经验"],
            "gaps": ["ML基础", "Prompt工程", "向量检索", "评估方法"],
            "plan": [
                {"month": 1, "focus": "AI基础+第一个RAG Demo"},
                {"month": 2, "focus": "Prompt工程+Agent开发"},
                {"month": 3, "focus": "RAG深度优化+评估体系"},
                {"month": 4, "focus": "完整项目实战"},
            ],
        },
        "frontend": {
            "advantages": ["用户体验", "交互设计"],
            "gaps": ["后端架构", "数据处理", "ML基础", "系统设计"],
            "plan": [
                {"month": 1, "focus": "Python+API调用"},
                {"month": 2, "focus": "RAG基础+Prompt工程"},
                {"month": 3, "focus": "全栈AI应用"},
                {"month": 4, "focus": "完整项目实战"},
            ],
        },
    }

    def plan(self, bg: str) -> dict:
        cfg = self.PATHS.get(bg, self.PATHS["backend"])
        return {"background": bg, **cfg}


class SkillGapAnalyzer:
    REQUIRED = {"python": 0.9, "prompt": 0.8, "rag": 0.8, "agent": 0.7,
                "evaluation": 0.7, "system_design": 0.8}

    def analyze(self, current: dict[str, float]) -> dict:
        gaps = {s: {"current": current.get(s, 0), "required": r}
                for s, r in self.REQUIRED.items() if current.get(s, 0) < r}
        priority = sorted(gaps, key=lambda s: self.REQUIRED[s] - current.get(s, 0), reverse=True)
        return {"gaps": len(gaps), "priority": priority[:3],
                "readiness": f"{(1 - len(gaps)/len(self.REQUIRED))*100:.0f}%"}


def main():
    print("=" * 60)
    print("AI转型之路演示")
    print("=" * 60)

    print("\n--- 转型路径规划 ---")
    planner = TransitionPlanner()
    for bg in ["backend", "frontend"]:
        r = planner.plan(bg)
        print(f"\n  {bg}转型:")
        print(f"    优势: {', '.join(r['advantages'])}")
        print(f"    待补: {', '.join(r['gaps'])}")
        for step in r["plan"]:
            print(f"    第{step['month']}月: {step['focus']}")

    print("\n--- 技能差距分析 ---")
    analyzer = SkillGapAnalyzer()
    result = analyzer.analyze({
        "python": 0.9, "prompt": 0.3, "rag": 0.2,
        "agent": 0.1, "evaluation": 0.1, "system_design": 0.8,
    })
    print(f"  就绪度: {result['readiness']}")
    print(f"  差距数: {result['gaps']}")
    print(f"  优先学: {', '.join(result['priority'])}")

    print(f"\n{'=' * 60}")
    print("核心: 聚焦核心+边学边做+后端经验是优势")
    print("=" * 60)


if __name__ == "__main__":
    main()
