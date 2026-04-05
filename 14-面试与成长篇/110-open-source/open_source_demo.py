"""开源AI项目贡献指南演示：路径规划、PR检查"""


class ContributionPlanner:
    PROJECTS = {
        "langchain": {"difficulty": "medium", "lang": "Python", "stars": "80K+"},
        "llamaindex": {"difficulty": "medium", "lang": "Python", "stars": "30K+"},
        "chromadb": {"difficulty": "easy", "lang": "Python", "stars": "12K+"},
        "vllm": {"difficulty": "hard", "lang": "Python", "stars": "20K+"},
    }

    def recommend(self, level: str) -> list[dict]:
        recs = []
        for name, info in self.PROJECTS.items():
            if level == "beginner" and info["difficulty"] in ("easy", "medium"):
                recs.append({"project": name, **info, "start": "文档修复/good first issue"})
            elif level in ("intermediate", "advanced"):
                recs.append({"project": name, **info, "start": "Bug修复/功能开发"})
        return recs


class PRChecker:
    ITEMS = ["代码通过测试", "添加测试用例", "更新文档", "PR描述完整",
             "遵循代码规范", "commit规范"]

    def check(self, done: list[bool]) -> dict:
        passed = sum(done[:len(self.ITEMS)])
        missing = [self.ITEMS[i] for i, d in enumerate(done) if not d]
        return {"ready": passed == len(self.ITEMS),
                "score": f"{passed}/{len(self.ITEMS)}", "missing": missing}


def main():
    print("=" * 60)
    print("开源AI项目贡献指南演示")
    print("=" * 60)

    print("\n--- 项目推荐 ---")
    planner = ContributionPlanner()
    for level in ["beginner", "intermediate"]:
        print(f"\n  {level}:")
        for r in planner.recommend(level):
            print(f"    ⭐ {r['project']} ({r['lang']}, {r['stars']}) → {r['start']}")

    print("\n--- PR质量检查 ---")
    checker = PRChecker()
    result = checker.check([True, True, False, True, True, False])
    print(f"  就绪: {'✅' if result['ready'] else '❌'} ({result['score']})")
    if result["missing"]:
        print(f"  缺失: {', '.join(result['missing'])}")

    print(f"\n{'=' * 60}")
    print("核心: 从文档修复开始, 先沟通再开发, 持续贡献")
    print("=" * 60)


if __name__ == "__main__":
    main()
