"""
AI知识库治理演示：Freshness监控 + 质量评估 + 治理工作流
对应文章：76-AI知识库治理文档过期质量评估更新流程
"""
from __future__ import annotations

import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum


class DocStatus(Enum):
    ACTIVE = "active"
    STALE = "stale"
    EXPIRED = "expired"
    ARCHIVED = "archived"


@dataclass
class KnowledgeDoc:
    doc_id: str
    title: str
    content: str
    owner: str
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: DocStatus = DocStatus.ACTIVE
    ttl_days: int = 90
    hit_count: int = 0
    helpful_count: int = 0
    unhelpful_count: int = 0
    quality_score: float = 1.0


class FreshnessMonitor:
    def __init__(self):
        self.docs: dict[str, KnowledgeDoc] = {}

    def add_doc(self, doc: KnowledgeDoc):
        self.docs[doc.doc_id] = doc

    def check(self) -> dict:
        now = time.time()
        result = {"active": [], "stale": [], "expired": []}
        for doc in self.docs.values():
            if doc.status == DocStatus.ARCHIVED:
                continue
            age = (now - doc.updated_at) / 86400
            remaining = doc.ttl_days - age
            info = {"doc_id": doc.doc_id, "title": doc.title, "owner": doc.owner}
            if remaining <= 0:
                doc.status = DocStatus.EXPIRED
                info["expired_days"] = round(-remaining, 1)
                result["expired"].append(info)
            elif remaining <= 14:
                doc.status = DocStatus.STALE
                info["remaining_days"] = round(remaining, 1)
                result["stale"].append(info)
            else:
                info["remaining_days"] = round(remaining, 1)
                result["active"].append(info)
        return result


class QualityEvaluator:
    def __init__(self, monitor: FreshnessMonitor):
        self.monitor = monitor

    def evaluate(self, doc_id) -> dict:
        doc = self.monitor.docs.get(doc_id)
        if not doc:
            return {"error": "not_found"}

        usage = min(doc.hit_count / 10, 1.0)
        total_fb = doc.helpful_count + doc.unhelpful_count
        feedback = doc.helpful_count / total_fb if total_fb > 0 else 0.5
        age = (time.time() - doc.updated_at) / 86400
        freshness = max(0, 1.0 - age / doc.ttl_days)
        content = min(len(doc.content) / 500, 1.0)

        overall = usage * 0.3 + feedback * 0.3 + freshness * 0.2 + content * 0.2
        doc.quality_score = round(overall, 2)

        if overall >= 0.8:
            rec = "优质，保持"
        elif overall >= 0.5:
            rec = "一般，建议优化"
        elif overall >= 0.3:
            rec = "较差，需要重写"
        else:
            rec = "极差，建议淘汰"

        return {
            "doc_id": doc_id, "title": doc.title,
            "usage": round(usage, 2), "feedback": round(feedback, 2),
            "freshness": round(freshness, 2), "content": round(content, 2),
            "overall": doc.quality_score, "recommendation": rec,
        }

    def batch_evaluate(self):
        results = [self.evaluate(did) for did in self.monitor.docs]
        results.sort(key=lambda x: x.get("overall", 0))
        return results


class GovernanceWorkflow:
    def __init__(self, monitor, evaluator):
        self.monitor = monitor
        self.evaluator = evaluator

    def run(self) -> dict:
        freshness = self.monitor.check()
        quality = self.evaluator.batch_evaluate()
        actions = []

        for d in freshness["expired"]:
            actions.append({
                "type": "🔴 需要更新", "doc": d["title"],
                "owner": d["owner"],
                "reason": f"已过期{d['expired_days']}天",
            })
        for d in freshness["stale"]:
            actions.append({
                "type": "🟡 即将过期", "doc": d["title"],
                "owner": d["owner"],
                "reason": f"将在{d['remaining_days']}天后过期",
            })
        for q in quality:
            if q.get("overall", 1) < 0.3:
                actions.append({
                    "type": "🔴 建议淘汰", "doc": q["title"],
                    "owner": "",
                    "reason": f"质量评分{q['overall']}",
                })
            elif q.get("overall", 1) < 0.5:
                actions.append({
                    "type": "🟡 需要优化", "doc": q["title"],
                    "owner": "",
                    "reason": f"质量评分{q['overall']}",
                })

        return {
            "freshness": {
                "active": len(freshness["active"]),
                "stale": len(freshness["stale"]),
                "expired": len(freshness["expired"]),
            },
            "quality": {
                "good": sum(1 for q in quality if q.get("overall", 0) >= 0.8),
                "fair": sum(1 for q in quality if 0.5 <= q.get("overall", 0) < 0.8),
                "poor": sum(1 for q in quality if q.get("overall", 0) < 0.5),
            },
            "actions": actions,
        }

    def archive(self, doc_id):
        doc = self.monitor.docs.get(doc_id)
        if doc:
            doc.status = DocStatus.ARCHIVED
            return True
        return False


def main():
    monitor = FreshnessMonitor()
    evaluator = QualityEvaluator(monitor)
    workflow = GovernanceWorkflow(monitor, evaluator)

    print("=" * 60)
    print("AI知识库治理演示")
    print("=" * 60)

    # 创建测试文档
    now = time.time()
    docs = [
        KnowledgeDoc("d1", "退货政策", "用户可以在收到商品后15天内申请退货" * 20,
                      "policy_team", now - 100 * 86400, now - 100 * 86400,
                      ttl_days=90, hit_count=15, helpful_count=12, unhelpful_count=3),
        KnowledgeDoc("d2", "配送说明", "标准配送3到5个工作日" * 15,
                      "logistics", now - 30 * 86400, now - 30 * 86400,
                      ttl_days=90, hit_count=20, helpful_count=18, unhelpful_count=2),
        KnowledgeDoc("d3", "旧版产品手册", "产品V1.0使用说明" * 5,
                      "product_team", now - 200 * 86400, now - 200 * 86400,
                      ttl_days=90, hit_count=2, helpful_count=0, unhelpful_count=5),
        KnowledgeDoc("d4", "公司简介", "我们是一家专注于AI技术的公司" * 30,
                      "hr", now - 50 * 86400, now - 50 * 86400,
                      ttl_days=365, hit_count=8, helpful_count=7, unhelpful_count=1),
        KnowledgeDoc("d5", "促销活动", "双十一活动规则" * 3,
                      "marketing", now - 85 * 86400, now - 85 * 86400,
                      ttl_days=90, hit_count=1, helpful_count=0, unhelpful_count=2),
    ]

    print("\n--- 1. 导入文档 ---")
    for doc in docs:
        monitor.add_doc(doc)
        age = round((now - doc.updated_at) / 86400)
        print(f"  [{doc.doc_id}] {doc.title} (TTL={doc.ttl_days}天, 已{age}天)")

    # Freshness检查
    print("\n--- 2. Freshness检查 ---")
    freshness = monitor.check()
    print(f"  活跃: {len(freshness['active'])}篇")
    for d in freshness["active"]:
        print(f"    ✅ {d['title']} (剩余{d['remaining_days']}天)")
    print(f"  即将过期: {len(freshness['stale'])}篇")
    for d in freshness["stale"]:
        print(f"    🟡 {d['title']} (剩余{d['remaining_days']}天)")
    print(f"  已过期: {len(freshness['expired'])}篇")
    for d in freshness["expired"]:
        print(f"    🔴 {d['title']} (过期{d['expired_days']}天)")

    # 质量评估
    print("\n--- 3. 质量评估 ---")
    for q in evaluator.batch_evaluate():
        print(f"  [{q['doc_id']}] {q['title']:10s} "
              f"overall={q['overall']} usage={q['usage']} "
              f"feedback={q['feedback']} -> {q['recommendation']}")

    # 治理工作流
    print("\n--- 4. 治理动作 ---")
    report = workflow.run()
    print(f"  Freshness: active={report['freshness']['active']} "
          f"stale={report['freshness']['stale']} "
          f"expired={report['freshness']['expired']}")
    print(f"  Quality: good={report['quality']['good']} "
          f"fair={report['quality']['fair']} "
          f"poor={report['quality']['poor']}")
    print(f"\n  待执行动作:")
    for a in report["actions"]:
        print(f"    {a['type']} | {a['doc']} | {a['reason']}")

    # 归档操作
    print("\n--- 5. 归档低质量文档 ---")
    if workflow.archive("d3"):
        print(f"  已归档: d3 (旧版产品手册)")
    print(f"  当前文档状态:")
    for did, doc in monitor.docs.items():
        print(f"    [{did}] {doc.title} -> {doc.status.value}")


if __name__ == "__main__":
    main()
