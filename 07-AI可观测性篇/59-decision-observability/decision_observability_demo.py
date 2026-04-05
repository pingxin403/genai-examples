"""
决策可观测性演示
对应文章：59-决策可观测性Agent的思考过程也能追踪
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class DecisionType(Enum):
    STRATEGY = "strategy"
    TOOL_SELECT = "tool_select"
    PARAMETER = "parameter"
    VALIDATION = "validation"


@dataclass
class DecisionNode:
    node_id: str
    decision_type: DecisionType
    description: str
    chosen: str
    alternatives: list[str] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0


@dataclass
class ToolCall:
    tool: str
    params: dict
    output: str
    duration_ms: float
    success: bool = True


@dataclass
class AgentTrace:
    trace_id: str
    user_input: str
    final_output: str = ""
    decisions: list[DecisionNode] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    thoughts: list[str] = field(default_factory=list)
    total_ms: float = 0.0


class DecisionTracer:
    def __init__(self):
        self.traces: list[AgentTrace] = []

    def start(self, user_input: str) -> AgentTrace:
        return AgentTrace(
            trace_id=str(uuid.uuid4())[:8],
            user_input=user_input,
        )

    def think(self, trace: AgentTrace, thought: str):
        trace.thoughts.append(thought)

    def decide(self, trace: AgentTrace, dtype: DecisionType,
               desc: str, chosen: str,
               alts: list[str] | None = None,
               reason: str = "", conf: float = 0.0):
        trace.decisions.append(DecisionNode(
            node_id=f"d{len(trace.decisions)+1}",
            decision_type=dtype,
            description=desc,
            chosen=chosen,
            alternatives=alts or [],
            reasoning=reason,
            confidence=conf,
            timestamp=time.time(),
        ))

    def tool_call(self, trace: AgentTrace, tool: str,
                  params: dict, output: str, ms: float,
                  success: bool = True):
        trace.tool_calls.append(ToolCall(
            tool=tool, params=params,
            output=output[:200], duration_ms=ms, success=success,
        ))

    def end(self, trace: AgentTrace, output: str):
        trace.final_output = output
        self.traces.append(trace)

    def replay(self, trace: AgentTrace) -> str:
        lines = [
            f"{'='*50}",
            f"🔍 决策回放: {trace.trace_id}",
            f"📥 输入: {trace.user_input}",
            "",
        ]
        for i, t in enumerate(trace.thoughts):
            lines.append(f"  💭 思考{i+1}: {t}")
        lines.append("")
        for d in trace.decisions:
            lines.append(f"  🔀 [{d.node_id}] {d.description}")
            lines.append(f"     → 选择: {d.chosen}")
            if d.alternatives:
                lines.append(f"     → 备选: {', '.join(d.alternatives)}")
            if d.reasoning:
                lines.append(f"     → 原因: {d.reasoning}")
            lines.append(f"     → 置信度: {d.confidence:.0%}")
        lines.append("")
        for tc in trace.tool_calls:
            s = "✅" if tc.success else "❌"
            lines.append(f"  🔧 {s} {tc.tool} ({tc.duration_ms}ms)")
            lines.append(f"     输出: {tc.output[:100]}")
        lines.extend([
            "",
            f"📤 输出: {trace.final_output}",
            f"{'='*50}",
        ])
        return "\n".join(lines)


def simulate_agent_execution(tracer: DecisionTracer):
    """模拟Agent处理数据查询请求"""
    trace = tracer.start("上个月的总销售额是多少？")

    # 思考
    tracer.think(trace, "用户在问销售数据，这是一个结构化数据查询")
    tracer.think(trace, "需要确定'上个月'的时间范围")

    # 决策1: 选择策略
    tracer.decide(trace, DecisionType.STRATEGY,
                  "选择处理策略",
                  chosen="SQL查询",
                  alts=["API调用", "知识库检索"],
                  reason="用户问的是结构化数据，SQL查询最直接",
                  conf=0.92)

    # 决策2: 选择工具
    tracer.decide(trace, DecisionType.TOOL_SELECT,
                  "选择数据库工具",
                  chosen="mysql_query",
                  alts=["postgres_query", "analytics_api"],
                  reason="销售数据存储在MySQL中",
                  conf=0.95)

    # 决策3: 确定参数
    tracer.decide(trace, DecisionType.PARAMETER,
                  "确定时间范围",
                  chosen="2024-12-01 ~ 2024-12-31",
                  alts=["最近30天", "2024年12月"],
                  reason="'上个月'解析为上一个自然月",
                  conf=0.88)

    # 工具调用
    tracer.tool_call(trace, "mysql_query",
                     {"sql": "SELECT SUM(amount) FROM orders "
                             "WHERE date BETWEEN '2024-12-01' AND '2024-12-31'"},
                     output="{'total': 1250000.00}",
                     ms=45.2)

    # 决策4: 验证结果
    tracer.decide(trace, DecisionType.VALIDATION,
                  "验证查询结果是否合理",
                  chosen="结果合理，直接返回",
                  alts=["结果异常，需要重试"],
                  reason="125万在历史月度销售额范围内(80万-200万)",
                  conf=0.90)

    tracer.end(trace, "上个月（2024年12月）的总销售额为 ¥1,250,000.00")
    return trace


def simulate_failed_execution(tracer: DecisionTracer):
    """模拟Agent决策出错的场景"""
    trace = tracer.start("退款进度查询")

    tracer.think(trace, "用户在查退款进度，需要调用订单系统")

    tracer.decide(trace, DecisionType.TOOL_SELECT,
                  "选择工具",
                  chosen="create_order",
                  alts=["query_refund", "query_order"],
                  reason="误判为创建订单请求",
                  conf=0.45)

    tracer.tool_call(trace, "create_order",
                     {"product": "unknown"},
                     output="Error: missing required fields",
                     ms=120.5, success=False)

    tracer.decide(trace, DecisionType.VALIDATION,
                  "工具调用失败，重新选择",
                  chosen="query_refund",
                  alts=["query_order"],
                  reason="create_order失败，重新理解意图为退款查询",
                  conf=0.85)

    tracer.tool_call(trace, "query_refund",
                     {"user_id": "u123"},
                     output="{'status': 'processing', 'eta': '3 days'}",
                     ms=35.0)

    tracer.end(trace, "您的退款正在处理中，预计3个工作日内到账。")
    return trace


if __name__ == "__main__":
    tracer = DecisionTracer()

    print("决策可观测性演示")
    print("=" * 50)

    # 场景1: 正常执行
    print("\n📗 场景1: 正常执行")
    t1 = simulate_agent_execution(tracer)
    print(tracer.replay(t1))

    # 场景2: 决策出错后修正
    print("\n📕 场景2: 决策出错后修正")
    t2 = simulate_failed_execution(tracer)
    print(tracer.replay(t2))

    # 统计
    print(f"\n📊 决策统计:")
    all_decisions = t1.decisions + t2.decisions
    low_conf = [d for d in all_decisions if d.confidence < 0.6]
    print(f"  总决策数: {len(all_decisions)}")
    print(f"  低置信度决策: {len(low_conf)}")
    for d in low_conf:
        print(f"    ⚠️ [{d.node_id}] {d.description}: "
              f"{d.confidence:.0%} → {d.chosen}")
