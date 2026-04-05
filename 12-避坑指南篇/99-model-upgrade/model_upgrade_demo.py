"""模型升级兼容性演示：兼容性测试、灰度发布"""


class ModelCompatibilityTester:
    def __init__(self):
        self.tests: list[dict] = []

    def add(self, name: str, prompt: str, validators: list):
        self.tests.append({"name": name, "prompt": prompt, "validators": validators})

    def run(self, old_model: str, new_model: str) -> dict:
        passed = failed = 0
        details = []
        for t in self.tests:
            old_out = f"[{old_model}] {t['prompt'][:30]}..."
            new_out = f"[{new_model}] {t['prompt'][:30]}..."
            ok = all(v(new_out) for v in t["validators"])
            if ok:
                passed += 1
            else:
                failed += 1
            details.append({"name": t["name"], "passed": ok})
        total = len(self.tests)
        return {"passed": passed, "failed": failed,
                "pass_rate": f"{passed/total*100:.0f}%" if total else "N/A",
                "details": details}


class ModelGrayRelease:
    def __init__(self, old: str, new: str):
        self.old = old
        self.new = new
        self.ratio = 0.0

    def route(self, user_id: str) -> str:
        return self.new if hash(user_id) % 100 < self.ratio * 100 else self.old

    def increase(self, step: float = 0.1):
        self.ratio = min(1.0, self.ratio + step)

    def rollback(self):
        self.ratio = 0.0


def main():
    print("=" * 60)
    print("模型升级兼容性演示")
    print("=" * 60)

    print("\n--- 兼容性测试 ---")
    tester = ModelCompatibilityTester()
    tester.add("JSON输出", "返回JSON格式", [lambda x: "gpt" in x.lower()])
    tester.add("分类任务", "对以下文本分类", [lambda x: len(x) > 10])
    tester.add("摘要任务", "总结以下内容", [lambda x: "gpt" in x.lower()])

    result = tester.run("gpt-4-turbo", "gpt-4o")
    print(f"  通过率: {result['pass_rate']}")
    for d in result["details"]:
        icon = "✅" if d["passed"] else "❌"
        print(f"    {icon} {d['name']}")

    print("\n--- 灰度发布 ---")
    gray = ModelGrayRelease("gpt-4-turbo", "gpt-4o")
    stages = [0.05, 0.2, 0.5, 1.0]
    for target in stages:
        gray.ratio = target
        sample = [gray.route(f"user_{i}") for i in range(100)]
        new_pct = sum(1 for s in sample if s == "gpt-4o")
        print(f"  比例={target:.0%}: 新模型实际流量={new_pct}%")

    print(f"\n{'=' * 60}")
    print("核心: 回归测试+灰度发布+快速回滚 = 安全升级")
    print("=" * 60)


if __name__ == "__main__":
    main()
