"""
Prompt管理混乱演示：版本管理、变更检测、单一数据源
"""
from datetime import datetime


class PromptVersionManager:
    def __init__(self):
        self.prompts: dict[str, list[dict]] = {}

    def create(self, name: str, content: str, author: str) -> dict:
        self.prompts.setdefault(name, [])
        version = len(self.prompts[name]) + 1
        record = {"version": version, "content": content, "author": author,
                  "status": "draft", "created_at": datetime.now().isoformat()}
        self.prompts[name].append(record)
        return record

    def publish(self, name: str, version: int) -> dict:
        for v in self.prompts.get(name, []):
            if v["version"] == version:
                v["status"] = "published"
                return v
        return {"error": "版本不存在"}

    def rollback(self, name: str, target: int) -> dict:
        for v in self.prompts.get(name, []):
            if v["version"] == target:
                new = self.create(name, v["content"], "rollback")
                new["status"] = "rollback"
                return new
        return {"error": "目标版本不存在"}

    def history(self, name: str) -> list[dict]:
        return [{"v": v["version"], "status": v["status"], "author": v["author"]}
                for v in self.prompts.get(name, [])]


class PromptChangeDetector:
    def __init__(self):
        self.tests: list[dict] = []

    def add_test(self, query: str, must_contain: list[str]):
        self.tests.append({"query": query, "must_contain": must_contain})

    def compare(self, old_prompt: str, new_prompt: str) -> dict:
        old_pass = sum(1 for t in self.tests if self._check(old_prompt, t))
        new_pass = sum(1 for t in self.tests if self._check(new_prompt, t))
        total = len(self.tests)
        return {
            "old_pass_rate": f"{old_pass}/{total}",
            "new_pass_rate": f"{new_pass}/{total}",
            "regression": new_pass < old_pass,
        }

    @staticmethod
    def _check(prompt: str, test: dict) -> bool:
        return any(kw in prompt for kw in test["must_contain"])


def main():
    print("=" * 60)
    print("Prompt管理混乱演示")
    print("=" * 60)

    # --- 版本管理 ---
    print("\n--- Prompt版本管理 ---")
    mgr = PromptVersionManager()
    mgr.create("customer_service", "你是客服助手，回答要详细准确。", "张三")
    mgr.create("customer_service", "你是客服助手，回答要简短。", "李四")
    mgr.publish("customer_service", 1)

    print("  版本历史:")
    for h in mgr.history("customer_service"):
        print(f"    v{h['v']} | {h['status']:<10} | {h['author']}")

    # 回滚
    mgr.rollback("customer_service", 1)
    print("\n  回滚到v1后:")
    for h in mgr.history("customer_service"):
        print(f"    v{h['v']} | {h['status']:<10} | {h['author']}")

    # --- 变更检测 ---
    print("\n--- Prompt变更检测 ---")
    detector = PromptChangeDetector()
    detector.add_test("退货流程", ["详细", "准确"])
    detector.add_test("会员权益", ["详细"])
    detector.add_test("价格查询", ["准确"])

    old = "你是客服助手，回答要详细准确。不确定就说不知道。"
    new = "你是客服助手，回答要简短。"
    result = detector.compare(old, new)
    print(f"  旧Prompt通过: {result['old_pass_rate']}")
    print(f"  新Prompt通过: {result['new_pass_rate']}")
    print(f"  存在回归: {'⚠️ 是' if result['regression'] else '✅ 否'}")

    print("\n" + "=" * 60)
    print("核心原则: Prompt即代码，版本管理+回归测试+灰度发布")
    print("=" * 60)


if __name__ == "__main__":
    main()
