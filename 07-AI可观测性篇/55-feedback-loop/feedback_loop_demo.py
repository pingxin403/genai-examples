"""
用户反馈闭环演示
对应文章：55-用户反馈闭环点赞点踩数据如何变成评估集
"""
from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class FeedbackType(Enum):
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    EDIT = "edit"
    RETRY = "retry"
    COPY = "copy"


class IssueCategory(Enum):
    HALLUCINATION = "hallucination"
    IRRELEVANT = "irrelevant"
    INCOMPLETE = "incomplete"
    FORMAT_ERROR = "format_error"
    TONE_ISSUE = "tone_issue"
    OTHER = "other"


@dataclass
class FeedbackRecord:
    feedback_id: str
    conversation_id: str
    turn_id: str
    feedback_type: FeedbackType
    timestamp: float
    user_query: str = ""
    ai_response: str = ""
    retrieved_docs: list[str] = field(default_factory=list)
    model: str = ""
    issue_category: IssueCategory | None = None
    user_id: str = ""
    scenario: str = ""


class FeedbackCollector:
    def __init__(self):
        self.records: list[FeedbackRecord] = []

    def collect(self, conv_id: str, turn_id: str,
                fb_type: FeedbackType, context: dict) -> FeedbackRecord:
        record = FeedbackRecord(
            feedback_id=str(uuid.uuid4())[:8],
            conversation_id=conv_id,
            turn_id=turn_id,
            feedback_type=fb_type,
            timestamp=time.time(),
            user_query=context.get("query", ""),
            ai_response=context.get("response", ""),
            retrieved_docs=context.get("docs", []),
            model=context.get("model", ""),
            user_id=context.get("user_id", ""),
            scenario=context.get("scenario", ""),
        )
        self.records.append(record)
        return record

    def detect_retries(self, turns: list[dict]) -> list[FeedbackRecord]:
        retries = []
        for i in range(1, len(turns)):
            prev_q = turns[i - 1].get("query", "")
            curr_q = turns[i].get("query", "")
            if self._is_similar(prev_q, curr_q):
                r = FeedbackRecord(
                    feedback_id=str(uuid.uuid4())[:8],
                    conversation_id=turns[i - 1].get("conv_id", ""),
                    turn_id=turns[i - 1].get("turn_id", ""),
                    feedback_type=FeedbackType.RETRY,
                    timestamp=time.time(),
                    user_query=prev_q,
                    ai_response=turns[i - 1].get("response", ""),
                )
                retries.append(r)
                self.records.append(r)
        return retries

    @staticmethod
    def _is_similar(a: str, b: str) -> bool:
        if not a or not b or a == b:
            return False
        sa, sb = set(a), set(b)
        return len(sa & sb) / max(len(sa), 1) > 0.5


class EvalSetBuilder:
    def __init__(self, records: list[FeedbackRecord]):
        self.records = records

    def build(self) -> list[dict]:
        seen = set()
        result = []
        for r in self.records:
            if not r.user_query:
                continue
            key = (r.user_query, r.ai_response)
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "query": r.user_query,
                "response": r.ai_response,
                "feedback": r.feedback_type.value,
                "category": r.issue_category.value if r.issue_category else None,
                "docs": r.retrieved_docs,
            })
        return result

    def stats(self) -> dict:
        total = len(self.records)
        by_type: dict[str, int] = {}
        for r in self.records:
            by_type[r.feedback_type.value] = by_type.get(
                r.feedback_type.value, 0) + 1
        return {"total": total, "by_type": by_type}


def simulate_feedback(collector: FeedbackCollector, n: int = 50):
    """模拟用户反馈"""
    queries = ["退货流程怎么走", "产品保修多久", "如何修改订单",
               "配送费多少", "会员权益有哪些"]
    models = ["gpt-4o", "gpt-4o-mini"]
    categories = list(IssueCategory)

    for i in range(n):
        fb_type = random.choices(
            [FeedbackType.THUMBS_UP, FeedbackType.THUMBS_DOWN,
             FeedbackType.COPY, FeedbackType.EDIT],
            weights=[40, 15, 30, 15],
        )[0]
        query = random.choice(queries)
        record = collector.collect(
            conv_id=f"conv-{i:04d}",
            turn_id=f"turn-{i:04d}-1",
            fb_type=fb_type,
            context={
                "query": query,
                "response": f"关于{query}的回答...",
                "docs": [f"doc_{random.randint(1,100)}"],
                "model": random.choice(models),
                "user_id": f"user-{random.randint(1,20):03d}",
                "scenario": "customer_service",
            },
        )
        if fb_type == FeedbackType.THUMBS_DOWN:
            record.issue_category = random.choice(categories)


if __name__ == "__main__":
    collector = FeedbackCollector()

    print("=" * 60)
    print("用户反馈闭环演示")
    print("=" * 60)

    # 1. 模拟显式反馈
    simulate_feedback(collector, n=50)
    print(f"\n📥 采集到 {len(collector.records)} 条显式反馈")

    # 2. 模拟隐式反馈检测
    turns = [
        {"conv_id": "c1", "turn_id": "t1",
         "query": "退货流程怎么走", "response": "..."},
        {"conv_id": "c1", "turn_id": "t2",
         "query": "退货流程具体步骤", "response": "..."},
        {"conv_id": "c2", "turn_id": "t3",
         "query": "配送费多少", "response": "..."},
        {"conv_id": "c2", "turn_id": "t4",
         "query": "运费怎么算", "response": "..."},
    ]
    retries = collector.detect_retries(turns)
    print(f"🔄 检测到 {len(retries)} 条隐式重试反馈")

    # 3. 构建评估集
    builder = EvalSetBuilder(collector.records)
    eval_set = builder.build()
    stats = builder.stats()

    print(f"\n📊 反馈统计:")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print(f"\n📋 评估集大小: {len(eval_set)} 条 (去重后)")
    for entry in eval_set[:3]:
        print(f"  Q: {entry['query']}")
        print(f"  Feedback: {entry['feedback']}"
              f" | Category: {entry['category']}")
        print()
