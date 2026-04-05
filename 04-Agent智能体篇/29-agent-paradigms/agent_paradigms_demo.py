"""
Agent三大范式演示
配套文章：《Agent三大范式：ReAct、Plan-and-Execute、Multi-Agent》
"""

import random
import time


# ============================================================
# 模拟工具
# ============================================================

class Tool:
    def __init__(self, name, description, fn):
        self.name = name
        self.description = description
        self.fn = fn

    def execute(self, params):
        return self.fn(params)


def query_order(params):
    oid = params.get("order_id", "ORD-001")
    return {"order_id": oid, "status": "已发货", "amount": 299}


def query_logistics(params):
    return {"carrier": "顺丰", "status": "运输中", "days": 3}


def cancel_order(params):
    return {"success": True, "message": "退货申请已提交"}


TOOLS = [
    Tool("query_order", "查询订单状态", query_order),
    Tool("query_logistics", "查询物流信息", query_logistics),
    Tool("cancel_order", "申请退货", cancel_order),
]


# ============================================================
# 1. ReAct Agent
# ============================================================

class ReActAgent:
    def __init__(self, tools, max_iterations=5):
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations

    def run(self, query):
        print(f"\n[ReAct] 处理: {query}")
        history = []

        for i in range(self.max_iterations):
            # 模拟思考
            if "退货" in query and not any(h.get("action") == "query_order" for h in history):
                thought = {"tool": "query_order", "input": {"order_id": "ORD-001"}}
            elif "退货" in query and any(h.get("action") == "query_order" for h in history):
                thought = {"tool": "cancel_order", "input": {"order_id": "ORD-001"}}
            elif "物流" in query:
                thought = {"tool": "query_logistics", "input": {"order_id": "ORD-001"}}
            else:
                return f"回答: 关于'{query}'的处理结果"

            tool = self.tools.get(thought["tool"])
            if not tool:
                break

            result = tool.execute(thought["input"])
            history.append({"action": thought["tool"], "result": result})
            print(f"  Step {i+1}: {thought['tool']} → {result}")

            if thought["tool"] == "cancel_order":
                return f"完成: 已为您处理退货，{result['message']}"

        return "任务完成"


# ============================================================
# 2. Plan-and-Execute Agent
# ============================================================

class PlanAndExecuteAgent:
    def __init__(self, tools):
        self.tools = {t.name: t for t in tools}

    def run(self, query):
        print(f"\n[Plan-and-Execute] 处理: {query}")

        # 规划阶段
        plan = self._plan(query)
        print(f"  计划: {len(plan)}个步骤")
        for i, step in enumerate(plan):
            print(f"    Step {i+1}: {step['description']}")

        # 执行阶段
        results = []
        for i, step in enumerate(plan):
            tool = self.tools.get(step.get("tool"))
            if tool:
                result = tool.execute(step.get("input", {}))
                results.append(result)
                print(f"  执行Step {i+1}: {result}")

        return f"完成: 已按计划执行{len(plan)}个步骤"

    def _plan(self, query):
        if "退货" in query:
            return [
                {"description": "查询订单状态", "tool": "query_order", "input": {"order_id": "ORD-001"}},
                {"description": "查询物流信息", "tool": "query_logistics", "input": {}},
                {"description": "申请退货", "tool": "cancel_order", "input": {"order_id": "ORD-001"}},
            ]
        return [{"description": "直接回答", "tool": None}]


# ============================================================
# 3. Multi-Agent System
# ============================================================

class SpecialistAgent:
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain

    def execute(self, task):
        return f"[{self.name}] 已处理: {task}"


class MultiAgentSystem:
    def __init__(self):
        self.specialists = {}

    def register(self, domain, agent):
        self.specialists[domain] = agent

    def run(self, query):
        print(f"\n[Multi-Agent] 处理: {query}")

        # 主管分配
        assignments = self._assign(query)
        print(f"  分配了{len(assignments)}个子任务")

        # 专员执行
        results = {}
        for domain, task in assignments.items():
            agent = self.specialists.get(domain)
            if agent:
                results[domain] = agent.execute(task)
                print(f"  {domain}: {results[domain]}")

        # 质检
        print(f"  质检: 通过")
        return f"完成: {len(results)}个专员协作完成任务"

    def _assign(self, query):
        assignments = {}
        if "订单" in query or "退货" in query:
            assignments["order"] = "处理订单相关请求"
        if "物流" in query:
            assignments["logistics"] = "查询物流信息"
        if not assignments:
            assignments["general"] = query
        return assignments


# ============================================================
# 演示
# ============================================================

def main():
    print("=" * 60)
    print("🤖 Agent三大范式演示")
    print("=" * 60)

    # ReAct
    react = ReActAgent(TOOLS)
    react.run("帮我查一下订单然后申请退货")

    # Plan-and-Execute
    pae = PlanAndExecuteAgent(TOOLS)
    pae.run("帮我查订单、查物流、然后申请退货")

    # Multi-Agent
    mas = MultiAgentSystem()
    mas.register("order", SpecialistAgent("订单专员", "order"))
    mas.register("logistics", SpecialistAgent("物流专员", "logistics"))
    mas.register("general", SpecialistAgent("通用专员", "general"))
    mas.run("帮我查订单和物流信息")

    # 对比
    print("\n" + "=" * 60)
    print("📊 三种范式对比")
    print("=" * 60)
    print(f"{'范式':<20} {'适用场景':<20} {'复杂度':<10} {'可控性':<10}")
    print("-" * 60)
    print(f"{'ReAct':<20} {'简单工具调用':<20} {'低':<10} {'低':<10}")
    print(f"{'Plan-and-Execute':<20} {'复杂多步任务':<20} {'中':<10} {'高':<10}")
    print(f"{'Multi-Agent':<20} {'跨领域协作':<20} {'高':<10} {'高':<10}")

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
