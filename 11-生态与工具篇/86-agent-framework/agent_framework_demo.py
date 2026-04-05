"""
Agent框架对比演示：LangGraph vs AutoGen vs CrewAI
演示三种Agent编排模式的核心差异
"""
from dataclasses import dataclass, field


# ============================================================
# LangGraph风格：状态图驱动
# ============================================================
class AgentState:
    def __init__(self):
        self.messages = []
        self.current_step = "start"
        self.result = None
        self.priority = "normal"


class LangGraphStyleAgent:
    """状态图驱动的Agent编排"""

    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, name: str, func):
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str, condition=None):
        self.edges.setdefault(from_node, []).append(
            {"to": to_node, "condition": condition}
        )

    def run(self, state: AgentState) -> AgentState:
        current = "start"
        visited = set()
        while current != "end" and current not in visited:
            visited.add(current)
            if current in self.nodes:
                state = self.nodes[current](state)
            current = self._get_next(current, state)
        return state

    def _get_next(self, current: str, state: AgentState) -> str:
        for edge in self.edges.get(current, []):
            if edge["condition"] is None or edge["condition"](state):
                return edge["to"]
        return "end"


# ============================================================
# AutoGen风格：对话驱动
# ============================================================
class ConversableAgent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.chat_history = []

    def generate_reply(self, message: str) -> str:
        self.chat_history.append({"from": "user", "content": message})
        reply = f"[{self.name}({self.role})] 分析: {message[:30]}... -> 建议执行下一步"
        self.chat_history.append({"from": self.name, "content": reply})
        return reply


class AutoGenStyleGroupChat:
    def __init__(self, agents: list[ConversableAgent], max_rounds: int = 5):
        self.agents = agents
        self.max_rounds = max_rounds

    def run(self, initial_message: str) -> list[str]:
        messages = []
        current_msg = initial_message
        for round_num in range(self.max_rounds):
            agent = self.agents[round_num % len(self.agents)]
            reply = agent.generate_reply(current_msg)
            messages.append(reply)
            if round_num >= 2:
                messages.append(f"[系统] 对话完成，共{round_num + 1}轮")
                break
            current_msg = reply
        return messages


# ============================================================
# CrewAI风格：角色驱动
# ============================================================
@dataclass
class CrewAgent:
    role: str
    goal: str
    backstory: str


@dataclass
class Task:
    description: str
    agent: CrewAgent
    expected_output: str
    result: str = ""


class CrewAIStyleCrew:
    def __init__(self, agents: list[CrewAgent]):
        self.agents = agents
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def kickoff(self) -> list[dict]:
        results = []
        for task in self.tasks:
            output = f"[{task.agent.role}] 完成: {task.description}"
            task.result = output
            results.append(
                {"agent": task.agent.role, "task": task.description, "output": output}
            )
        return results


# ============================================================
# 对比演示
# ============================================================
def demo_langgraph():
    print("\n--- LangGraph风格：状态图驱动 ---")
    agent = LangGraphStyleAgent()

    def analyze(state):
        state.messages.append("分析告警信息...")
        state.priority = "high"
        return state

    def urgent_fix(state):
        state.messages.append("执行紧急修复流程")
        state.result = "紧急修复完成"
        return state

    def normal_fix(state):
        state.messages.append("执行常规修复流程")
        state.result = "常规修复完成"
        return state

    agent.add_node("start", analyze)
    agent.add_node("urgent", urgent_fix)
    agent.add_node("normal", normal_fix)
    agent.add_edge("start", "urgent", lambda s: s.priority == "high")
    agent.add_edge("start", "normal", lambda s: s.priority != "high")
    agent.add_edge("urgent", "end")
    agent.add_edge("normal", "end")

    state = AgentState()
    result = agent.run(state)
    for msg in result.messages:
        print(f"  {msg}")
    print(f"  结果: {result.result}")


def demo_autogen():
    print("\n--- AutoGen风格：对话驱动 ---")
    agents = [
        ConversableAgent("分析师", "告警分析"),
        ConversableAgent("运维", "执行修复"),
        ConversableAgent("审核", "结果验证"),
    ]
    chat = AutoGenStyleGroupChat(agents, max_rounds=5)
    messages = chat.run("服务器CPU使用率超过90%，需要分析和处理")
    for msg in messages:
        print(f"  {msg}")


def demo_crewai():
    print("\n--- CrewAI风格：角色驱动 ---")
    analyst = CrewAgent("告警分析师", "分析告警根因", "资深SRE")
    operator = CrewAgent("运维工程师", "执行修复操作", "运维专家")
    reviewer = CrewAgent("质量审核员", "验证修复结果", "质量保障")

    crew = CrewAIStyleCrew([analyst, operator, reviewer])
    crew.add_task(Task("分析CPU告警的根因", analyst, "根因分析报告"))
    crew.add_task(Task("执行扩容操作", operator, "扩容完成确认"))
    crew.add_task(Task("验证服务恢复正常", reviewer, "验证报告"))

    results = crew.kickoff()
    for r in results:
        print(f"  {r['output']}")


def main():
    print("=" * 60)
    print("Agent框架对比演示")
    print("=" * 60)

    demo_langgraph()
    demo_autogen()
    demo_crewai()

    print("\n" + "=" * 60)
    print("框架对比总结")
    print("=" * 60)
    rows = [
        ("LangGraph", "状态图驱动", "高", "复杂工作流"),
        ("AutoGen", "对话驱动", "中", "研究探索"),
        ("CrewAI", "角色驱动", "低", "简单团队任务"),
    ]
    print(f"{'框架':<15} {'编排模式':<15} {'控制力':<10} {'适用场景'}")
    print("-" * 55)
    for name, mode, control, scene in rows:
        print(f"{name:<15} {mode:<15} {control:<10} {scene}")


if __name__ == "__main__":
    main()
