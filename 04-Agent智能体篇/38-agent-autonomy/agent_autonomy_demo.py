"""Agent自主度演示"""
from enum import IntEnum

class Level(IntEnum):
    L1=1; L2=2; L3=3; L4=4; L5=5

class AutonomyCtrl:
    def __init__(self, level=Level.L1):
        self.level = level
        self.ok = 0; self.fail = 0
    def should_auto(self, risk):
        if self.level <= Level.L2: return False
        if self.level == Level.L3: return risk == "low"
        if self.level == Level.L4: return risk in ("low","medium")
        return True
    def record(self, success):
        if success: self.ok += 1
        else: self.fail += 1
    def rate(self):
        t = self.ok + self.fail
        return self.ok/t if t>0 else 0
    def check_upgrade(self):
        r, t = self.rate(), self.ok+self.fail
        if self.level==Level.L1 and r>0.8 and t>=20: return True,"→L2"
        if self.level==Level.L2 and r>0.95 and t>=50: return True,"→L3"
        if self.level==Level.L3 and r>0.98 and t>=100: return True,"→L4"
        return False, f"成功率{r:.0%},样本{t}"

def main():
    print("🔄 Agent自主度演示\n")
    ctrl = AutonomyCtrl(Level.L1)
    
    # 模拟运行
    import random; random.seed(42)
    for i in range(60):
        ctrl.record(random.random() > 0.15)
    
    print(f"当前等级: L{ctrl.level}")
    print(f"成功率: {ctrl.rate():.0%} ({ctrl.ok}成功/{ctrl.fail}失败)")
    
    can, msg = ctrl.check_upgrade()
    print(f"升级检查: {'✅可升级' if can else '❌不满足'} {msg}")
    
    if can:
        ctrl.level = Level.L2
        print(f"已升级到L{ctrl.level}")
    
    # 测试自动执行决策
    for risk in ["low", "medium", "high"]:
        auto = ctrl.should_auto(risk)
        print(f"  风险={risk}: {'自动执行' if auto else '需人工确认'}")
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
