"""
微调数据工程演示
对应文章：46-微调数据工程高质量指令数据的洗法
"""
from __future__ import annotations
import hashlib
import json
import random
from collections import Counter
from dataclasses import dataclass, field


class InstructionDataCleaner:
    """指令数据清洗器"""

    def __init__(self, min_instruction_len=2, min_response_len=3,
                 max_response_len=2000):
        self.min_instruction_len = min_instruction_len
        self.min_response_len = min_response_len
        self.max_response_len = max_response_len
        self.seen_hashes = set()
        self.stats = Counter()

    def clean_batch(self, samples, cleaned=None):
        if cleaned is None:
            cleaned = []
        for sample in samples:
            result = self._clean_one(sample)
            if result:
                cleaned.append(result)
        return cleaned

    def _clean_one(self, sample):
        self.stats["total"] += 1

        if not ("instruction" in sample and "response" in sample):
            self.stats["format_invalid"] += 1
            return None

        instruction = sample["instruction"].strip()
        response = sample["response"].strip()

        if len(instruction) < self.min_instruction_len:
            self.stats["instruction_too_short"] += 1
            return None
        if len(response) < self.min_response_len:
            self.stats["response_too_short"] += 1
            return None
        if len(response) > self.max_response_len:
            response = response[:self.max_response_len]
            self.stats["response_truncated"] += 1

        h = hashlib.md5(instruction.encode()).hexdigest()
        if h in self.seen_hashes:
            self.stats["duplicate"] += 1
            return None
        self.seen_hashes.add(h)

        words = response.split()
        if len(words) > 10 and len(set(words)) / len(words) < 0.3:
            self.stats["low_quality"] += 1
            return None

        self.stats["passed"] += 1
        return {"instruction": instruction, "response": response}

    def get_report(self) -> dict:
        return dict(self.stats)


class DiversityAnalyzer:
    """数据多样性分析器"""

    def __init__(self, categories: list[str]):
        self.categories = categories

    def analyze(self, samples: list[dict]) -> dict:
        dist = Counter()
        for s in samples:
            cat = self._classify(s["instruction"])
            dist[cat] += 1

        total = len(samples)
        report = {
            "total": total,
            "category_distribution": {},
            "underrepresented": [],
        }
        for cat in self.categories:
            count = dist.get(cat, 0)
            ratio = count / total if total > 0 else 0
            report["category_distribution"][cat] = {
                "count": count, "ratio": round(ratio, 3)
            }
            if count < 50:
                report["underrepresented"].append(cat)
        return report

    def _classify(self, instruction: str) -> str:
        """简单关键词分类（生产中用模型分类）"""
        for cat in self.categories:
            if cat in instruction:
                return cat
        return "其他"


def split_by_category(samples: list[dict], categories: list[str],
                      val_ratio: float = 0.15) -> dict:
    """按类型分组划分训练集/验证集，避免数据泄露"""
    analyzer = DiversityAnalyzer(categories)
    grouped = {cat: [] for cat in categories + ["其他"]}

    for s in samples:
        cat = analyzer._classify(s["instruction"])
        grouped[cat].append(s)

    train, val = [], []
    for cat, items in grouped.items():
        random.shuffle(items)
        split_idx = max(1, int(len(items) * val_ratio))
        val.extend(items[:split_idx])
        train.extend(items[split_idx:])

    return {"train": train, "val": val,
            "train_size": len(train), "val_size": len(val)}


if __name__ == "__main__":
    # 模拟原始数据
    raw_data = [
        {"instruction": "怎么查询我的订单状态？", "response": "您可以登录APP，在'我的订单'页面查看订单状态，包括待付款、已发货、已完成等状态。"},
        {"instruction": "退货流程是什么？", "response": "退货流程：1.在订单详情点击申请退货 2.选择退货原因 3.等待审核 4.寄回商品 5.确认退款。"},
        {"instruction": "怎么退货", "response": "退货流程：在订单中申请退货，审核通过后寄回商品即可。"},
        {"instruction": "你好", "response": "你好"},  # 太短
        {"instruction": "", "response": "这是回答"},  # instruction为空
        {"instruction": "查订单", "response": "好的好的好的好的好的好的好的好的好的好的好的"},  # 低质量
        {"instruction": "如何修改收货地址？", "response": "在订单详情页面，如果订单尚未发货，您可以点击'修改地址'按钮来更新收货地址信息。"},
        {"instruction": "支付方式有哪些？", "response": "我们支持微信支付、支付宝、银行卡、信用卡等多种支付方式，您可以在结算页面选择。"},
    ]

    # 清洗
    cleaner = InstructionDataCleaner()
    cleaned = cleaner.clean_batch(raw_data)

    print("=== 清洗报告 ===")
    report = cleaner.get_report()
    for k, v in report.items():
        print(f"  {k}: {v}")
    print(f"\n清洗后样本数: {len(cleaned)}")

    # 多样性分析
    categories = ["订单", "退货", "支付", "地址", "物流"]
    analyzer = DiversityAnalyzer(categories)
    diversity = analyzer.analyze(cleaned)
    print(f"\n=== 多样性分析 ===")
    for cat, info in diversity["category_distribution"].items():
        print(f"  {cat}: {info['count']}条 ({info['ratio']*100:.1f}%)")
    if diversity["underrepresented"]:
        print(f"  不足类型: {diversity['underrepresented']}")

    # 划分训练/验证集
    split = split_by_category(cleaned, categories)
    print(f"\n=== 数据划分 ===")
    print(f"  训练集: {split['train_size']}条")
    print(f"  验证集: {split['val_size']}条")
