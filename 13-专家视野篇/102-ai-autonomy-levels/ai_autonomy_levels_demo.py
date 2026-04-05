"""AI自主化五个等级演示：评估、控制、渐进升级"""


class AutonomyAssessor:
    LEVELS = {1: "辅助", 2: "建议", 3: "协作", 4: "委托", 5: "自主"}

    def assess(self, risk: str, accuracy: float, reversible: bool) -> dict:
        if risk == "high" or accuracy < 0.8:
            level = 1 if accuracy < 0.6 else 2
        elif risk == "medium":
            level = 3 if reversible else 2
        else:
            level = 4 if accuracy > 0.95 else 3
        return {"level": level, "name": self.LEVELS[level],
                "reason": f"风险={risk}, 准确率={accuracy:.0%}, 可逆={reversible}"}


class AutonomyController:
    def __init__(self, level: int = 1):
        self.level = level

    def request(self, action: str, risk: str) -> dict:
        if self.level <= 2:
            return {"execute": False, "msg": f"建议: {action}"}
        if self.level == 3 or (self.level == 4 and risk == "high"):
            return {"execute": False, "msg": f"等待审批: {action}"}
        return {"execute": True, "msg": f"自动执行: {action}"}


def main():
    print("=" * 60)
    print("AI自主化五个等级演示")
    print("=" * 60)

    print("\n--- 自主度评估 ---")
    assessor = AutonomyAssessor()
    scenarios = [
        ("客服问答", "low", 0.92, True),
        ("邮件发送", "medium", 0.88, True),
        ("资金操作", "high", 0.95, False),
        ("日志分析", "low", 0.98, True),
    ]
    for name, risk, acc, rev in scenarios:
        r = assessor.assess(risk, acc, rev)
        print(f"  {name:<10} → L{r['level']} {r['name']} ({r['reason']})")

    print("\n--- 自主度控制 ---")
    for level in [2, 3, 4]:
        ctrl = AutonomyController(level)
        print(f"\n  Level {level}:")
        for action, risk in [("查询数据", "low"), ("发送邮件", "medium"), ("删除记录", "high")]:
            r = ctrl.request(action, risk)
            icon = "🤖" if r["execute"] else "👤"
            print(f"    {icon} {r['msg']}")

    print(f"\n{'=' * 60}")
    print("核心: 渐进升级+按风险分级+数据驱动 = 安全自主化")
    print("=" * 60)


if __name__ == "__main__":
    main()
