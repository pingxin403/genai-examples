"""AI技术债演示：评估、模型抽象层、治理建议"""


class AITechDebtAssessor:
    CATEGORIES = {
        "prompt": {"weight": 0.2, "items": ["版本管理", "注释说明", "测试用例"]},
        "model_lock": {"weight": 0.25, "items": ["多模型支持", "抽象层", "Prompt无模型依赖"]},
        "data": {"weight": 0.25, "items": ["数据版本", "质量监控", "漂移检测"]},
        "eval": {"weight": 0.15, "items": ["评估基线", "自动评估", "线上监控"]},
        "arch": {"weight": 0.15, "items": ["组件独立", "接口抽象", "配置外部化"]},
    }

    def assess(self, checks: dict[str, list[bool]]) -> dict:
        scores = {}
        total = 0
        for cat, cfg in self.CATEGORIES.items():
            vals = checks.get(cat, [False] * len(cfg["items"]))
            s = sum(vals) / len(cfg["items"])
            scores[cat] = round(s, 2)
            total += s * cfg["weight"]
        level = "低" if total > 0.7 else "中" if total > 0.4 else "高"
        return {"scores": scores, "overall": round(total, 2), "debt_level": level}


class ModelAbstractionLayer:
    def __init__(self):
        self.providers: dict[str, str] = {}
        self.active: str = ""

    def register(self, name: str, endpoint: str):
        self.providers[name] = endpoint

    def switch(self, name: str):
        self.active = name

    def generate(self, prompt: str) -> str:
        ep = self.providers.get(self.active, "unknown")
        return f"[{self.active}@{ep}] Response to: {prompt[:30]}..."


def main():
    print("=" * 60)
    print("AI技术债演示")
    print("=" * 60)

    print("\n--- 技术债评估 ---")
    assessor = AITechDebtAssessor()
    result = assessor.assess({
        "prompt": [True, False, False],
        "model_lock": [False, False, True],
        "data": [True, False, False],
        "eval": [False, False, False],
        "arch": [True, True, False],
    })
    print(f"  技术债等级: {result['debt_level']} (得分: {result['overall']})")
    for cat, score in result["scores"].items():
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"    {cat:<12} {bar} {score:.0%}")

    print("\n--- 模型抽象层 ---")
    layer = ModelAbstractionLayer()
    layer.register("openai", "api.openai.com")
    layer.register("claude", "api.anthropic.com")
    layer.register("local", "localhost:8080")

    for model in ["openai", "claude", "local"]:
        layer.switch(model)
        out = layer.generate("总结这段文本")
        print(f"  {out}")

    print(f"\n{'=' * 60}")
    print("核心: Prompt注释+模型抽象+数据版本 = 技术债可控")
    print("=" * 60)


if __name__ == "__main__":
    main()
