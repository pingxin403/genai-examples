"""ReAct模式演示"""

class ReActEngine:
    def __init__(self, tools, max_iter=5):
        self.tools = tools
        self.max_iter = max_iter

    def run(self, query):
        print(f"Query: {query}")
        history = []
        for i in range(self.max_iter):
            # 模拟思考
            if not history:
                thought = "需要查询订单"
                action, params = "query_order", {"id": "ORD-001"}
            elif any("已发货" in str(h) for h in history):
                print(f"  Step {i+1}: Thought=已有足够信息")
                return f"订单ORD-001已发货，预计3天送达"
            else:
                thought = "信息不足"
                return "抱歉，无法获取信息"

            # 执行
            tool = self.tools.get(action)
            obs = tool(params) if tool else "工具不存在"
            history.append(obs)
            print(f"  Step {i+1}: Thought={thought} → Action={action} → Obs={obs}")

        return "达到最大迭代"

def main():
    print("🧠 ReAct模式演示\n")
    tools = {
        "query_order": lambda p: {"order": p.get("id"), "status": "已发货", "eta": "3天"},
        "query_logistics": lambda p: {"carrier": "顺丰", "status": "运输中"},
    }
    engine = ReActEngine(tools, max_iter=5)
    result = engine.run("帮我查一下订单ORD-001的状态")
    print(f"\n结果: {result}")
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
