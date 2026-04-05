"""Skills工程化演示"""
from dataclasses import dataclass

@dataclass
class Skill:
    name: str; version: str; description: str; steps: list; status: str = "active"

class SkillRegistry:
    def __init__(self): self.skills = {}
    def register(self, s): self.skills[f"{s.name}@{s.version}"] = s
    def active(self): return [s for s in self.skills.values() if s.status == "active"]
    def execute(self, name, params):
        skill = next((s for s in self.skills.values() if s.name==name and s.status=="active"), None)
        if not skill: return {"error": "技能不存在"}
        results = []
        for step in skill.steps:
            results.append(f"{step}(params={params})")
        return {"skill": name, "version": skill.version, "steps": results}

def main():
    print("🧠 Skills工程化演示\n")
    reg = SkillRegistry()
    reg.register(Skill("退货", "2.0", "完整退货流程", ["查订单","查物流","申请退货","发通知"]))
    reg.register(Skill("查询", "1.0", "订单查询", ["查订单","格式化结果"]))

    print(f"活跃技能: {[s.name for s in reg.active()]}")
    print(f"\n执行退货技能: {reg.execute('退货', {'order_id': 'ORD-001'})}")
    print(f"执行查询技能: {reg.execute('查询', {'order_id': 'ORD-002'})}")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
