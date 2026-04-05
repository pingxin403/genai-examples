"""
RLHF工程化演示
对应文章：51-RLHF工程化人类反馈如何变成模型能力
"""
from __future__ import annotations
import random
import time
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class FeedbackRecord:
    """用户反馈记录"""
    query: str
    response: str
    feedback: str  # thumbs_up / thumbs_down / skip
    user_id: str = ""
    timestamp: float = 0.0


@dataclass
class PreferencePair:
    """偏好对"""
    query: str
    chosen: str
    rejected: str
    confidence: float = 1.0


class FeedbackCollector:
    """反馈采集与清洗"""

    def __init__(self, min_response_len: int = 3):
        self.min_response_len = min_response_len
        self.stats = Counter()

    def clean(self, records: list[FeedbackRecord]) -> list[FeedbackRecord]:
        cleaned = []
        for r in records:
            self.stats["total"] += 1
            if r.feedback == "skip":
                self.stats["skipped"] += 1
                continue
            if len(r.response) < self.min_response_len:
                self.stats["too_short"] += 1
                continue
            cleaned.append(r)
            self.stats["valid"] += 1
        return cleaned

    def get_report(self) -> dict:
        return dict(self.stats)


class PreferenceBuilder:
    """偏好对构建器"""

    def build_from_feedback(
        self, records: list[FeedbackRecord]
    ) -> list[PreferencePair]:
        by_query: dict[str, dict] = {}
        for r in records:
            key = r.query.strip().lower()
            if key not in by_query:
                by_query[key] = {"up": [], "down": []}
            if r.feedback == "thumbs_up":
                by_query[key]["up"].append(r.response)
            elif r.feedback == "thumbs_down":
                by_query[key]["down"].append(r.response)

        pairs = []
        for query_key, responses in by_query.items():
            if responses["up"] and responses["down"]:
                pairs.append(PreferencePair(
                    query=query_key,
                    chosen=responses["up"][0],
                    rejected=responses["down"][0],
                    confidence=0.9,
                ))
        return pairs

    def build_from_ranking(
        self, query: str, ranked_responses: list[str]
    ) -> list[PreferencePair]:
        pairs = []
        for i in range(len(ranked_responses)):
            for j in range(i + 1, len(ranked_responses)):
                pairs.append(PreferencePair(
                    query=query,
                    chosen=ranked_responses[i],
                    rejected=ranked_responses[j],
                    confidence=max(0.5, 1.0 - (j - i) * 0.1),
                ))
        return pairs


class RewardModelEvaluator:
    """奖励模型评估器（模拟）"""

    def evaluate(self, pairs: list[PreferencePair]) -> dict:
        correct = 0
        for pair in pairs:
            score_chosen = self._mock_reward(pair.chosen)
            score_rejected = self._mock_reward(pair.rejected)
            if score_chosen > score_rejected:
                correct += 1
        accuracy = correct / len(pairs) if pairs else 0
        return {
            "total_pairs": len(pairs),
            "correct": correct,
            "accuracy": round(accuracy, 3),
        }

    def _mock_reward(self, text: str) -> float:
        score = len(text) * 0.01
        if "步骤" in text or "流程" in text:
            score += 0.5
        if "请" in text or "您" in text:
            score += 0.3
        score += random.gauss(0, 0.1)
        return score


if __name__ == "__main__":
    # 模拟用户反馈数据
    raw_feedback = [
        FeedbackRecord(
            query="怎么退货",
            response="退货流程：1.申请退货 2.审核通过 3.寄回商品 4.确认退款。请在订单详情页操作。",
            feedback="thumbs_up",
        ),
        FeedbackRecord(
            query="怎么退货",
            response="你去退吧",
            feedback="thumbs_down",
        ),
        FeedbackRecord(
            query="修改地址",
            response="请在订单详情页面，如果订单尚未发货，您可以点击修改地址按钮来更新收货信息。",
            feedback="thumbs_up",
        ),
        FeedbackRecord(
            query="修改地址",
            response="改不了",
            feedback="thumbs_down",
        ),
        FeedbackRecord(
            query="你好",
            response="嗨",
            feedback="skip",
        ),
        FeedbackRecord(
            query="支付问题",
            response="ok",
            feedback="thumbs_down",
        ),
    ]

    # 1. 清洗反馈
    collector = FeedbackCollector()
    cleaned = collector.clean(raw_feedback)
    print("=== 反馈清洗 ===")
    report = collector.get_report()
    for k, v in report.items():
        print(f"  {k}: {v}")

    # 2. 构建偏好对
    builder = PreferenceBuilder()
    pairs = builder.build_from_feedback(cleaned)
    print(f"\n=== 偏好对构建 ===")
    print(f"  生成偏好对: {len(pairs)}条")
    for p in pairs:
        print(f"  Query: {p.query}")
        print(f"    Chosen:   {p.chosen[:40]}...")
        print(f"    Rejected: {p.rejected[:40]}...")

    # 3. 排序标注构建偏好对
    ranking_pairs = builder.build_from_ranking(
        query="如何查询物流",
        ranked_responses=[
            "请登录APP，在订单详情页查看物流信息，支持实时追踪。",
            "在订单页面可以看到物流状态。",
            "查一下就知道了。",
        ],
    )
    print(f"\n  排序标注生成偏好对: {len(ranking_pairs)}条")

    # 4. 评估奖励模型
    all_pairs = pairs + ranking_pairs
    evaluator = RewardModelEvaluator()
    result = evaluator.evaluate(all_pairs)
    print(f"\n=== 奖励模型评估 ===")
    print(f"  总偏好对: {result['total_pairs']}")
    print(f"  判断正确: {result['correct']}")
    print(f"  准确率: {result['accuracy']*100:.1f}%")
