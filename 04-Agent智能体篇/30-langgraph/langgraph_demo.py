"""
LangGraph实战演示 - 把业务流程画成状态图
配套文章：《LangGraph实战：把业务流程画成状态图》
"""
from dataclasses import dataclass, field


@dataclass
class AgentState:
    user_query: str = ""
    intent: str = ""
    order_info: dict = field(default_factory=dict)
    logistics_info: dict = field(default_factory=dict)
    action_result: str = ""
    final_answer: str = ""


def intent_node(state):
    q = state.user_query.lower()
    state.intent = "refund" if "退" in q else "query"
    print(f"  [意图识别] {state.intent}")
    return state

def query_order_node(state):
    state.order_info = {"order_id": "ORD-001", "status": "已发货", "amount": 299}
    print(f"  [查询订单] {state.order_info}")
    return state

def query_logistics_node(state):
    state.logistics_info = {"carrier": "顺丰", "days": 8}
    print(f"  [查询物流] {state.logistics_info}")
    return state

def auto_refund_node(state):
    state.action_result = "退货申请已提交"
    print(f"  [自动退货] {state.action_result}")
    return state

def generate_answer_node(state):
    if state.action_result:
        state.final_answer = f"已处理：{state.action_result}"
    else:
        state.final_answer = f"订单状态：{state.order_info.get('status', '未知')}"
    print(f"  [生成回答] {state.final_answer}")
    return state


class SimpleGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.cond_edges = {}

    def add_node(self, name, fn):
        self.nodes[name] = fn

    def add_edge(self, src, dst):
        self.edges[src] = dst

    def add_conditional_edge(self, src, cond_fn, mapping):
        self.cond_edges[src] = (cond_fn, mapping)

    def run(self, start, state):
        current = start
        path = []
        while current and current != "END":
            if current in self.nodes:
                state = self.nodes[current](state)
                path.append(current)
            if current in self.cond_edges:
                fn, m = self.cond_edges[current]
                current = m.get(fn(state), "END")
            elif current in self.edges:
                current = self.edges[current]
            else:
                current = "END"
        return state, path


def main():
    print("=" * 50)
    print("🧠 LangGraph状态图演示")
    print("=" * 50)

    g = SimpleGraph()
    g.add_node("intent", intent_node)
    g.add_node("query_order", query_order_node)
    g.add_node("query_logistics", query_logistics_node)
    g.add_node("auto_refund", auto_refund_node)
    g.add_node("answer", generate_answer_node)

    g.add_conditional_edge("intent", lambda s: s.intent, {
        "refund": "query_order", "query": "query_order"
    })
    g.add_edge("query_order", "query_logistics")
    g.add_conditional_edge("query_logistics",
        lambda s: "timeout" if s.logistics_info.get("days", 0) > 7 else "ok",
        {"timeout": "auto_refund", "ok": "answer"})
    g.add_edge("auto_refund", "answer")

    # 测试1: 退货场景
    print("\n--- 场景1: 退货请求 ---")
    state1 = AgentState(user_query="帮我退货")
    result1, path1 = g.run("intent", state1)
    print(f"  路径: {' → '.join(path1)}")
    print(f"  结果: {result1.final_answer}")

    # 测试2: 查询场景
    print("\n--- 场景2: 查询请求 ---")
    state2 = AgentState(user_query="查一下订单状态")
    result2, path2 = g.run("intent", state2)
    print(f"  路径: {' → '.join(path2)}")
    print(f"  结果: {result2.final_answer}")

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    main()
