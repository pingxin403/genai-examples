"""
AI审计记录演示：审计日志 + 查询引擎 + 合规报告
对应文章：68-AI审计记录谁在什么时候问了AI什么
"""

import json
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class AuditEventType(Enum):
    QUERY = "query"
    RESPONSE = "response"
    RETRIEVAL = "retrieval"
    SECURITY_BLOCK = "security_block"
    ERROR = "error"


class ContentCategory(Enum):
    GENERAL = "general"
    PII = "pii"
    FINANCIAL = "financial"
    MEDICAL = "medical"
    LEGAL = "legal"


@dataclass
class AuditEvent:
    event_id: str
    event_type: AuditEventType
    timestamp: float
    user_id: str
    tenant_id: str
    session_id: str
    query: str = ""
    response: str = ""
    content_category: ContentCategory = ContentCategory.GENERAL
    model_version: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    retrieved_docs: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    security_flags: list[str] = field(default_factory=list)
    prev_hash: str = ""
    event_hash: str = ""


class AIAuditLogger:
    def __init__(self):
        self.events: list[AuditEvent] = []
        self.hash_chain: str = "genesis"
        self._counter = 0

    def _gen_id(self) -> str:
        self._counter += 1
        return f"evt_{hashlib.md5(f'{time.time()}{self._counter}'.encode()).hexdigest()[:12]}"

    def _append(self, event: AuditEvent):
        event.prev_hash = self.hash_chain
        payload = json.dumps({
            "event_id": event.event_id, "type": event.event_type.value,
            "timestamp": event.timestamp, "user_id": event.user_id,
            "prev_hash": event.prev_hash,
        }, sort_keys=True)
        event.event_hash = hashlib.sha256(payload.encode()).hexdigest()
        self.hash_chain = event.event_hash
        self.events.append(event)

    def log_query(self, user_id, tenant_id, session_id, query, category=ContentCategory.GENERAL):
        event = AuditEvent(
            event_id=self._gen_id(), event_type=AuditEventType.QUERY,
            timestamp=time.time(), user_id=user_id,
            tenant_id=tenant_id, session_id=session_id,
            query=query, content_category=category,
        )
        self._append(event)
        return event.event_id

    def log_response(self, user_id, tenant_id, session_id, query, response,
                     model_version, prompt_tokens, completion_tokens,
                     latency_ms, retrieved_docs=None, confidence=0.0,
                     category=ContentCategory.GENERAL):
        event = AuditEvent(
            event_id=self._gen_id(), event_type=AuditEventType.RESPONSE,
            timestamp=time.time(), user_id=user_id,
            tenant_id=tenant_id, session_id=session_id,
            query=query, response=response, content_category=category,
            model_version=model_version, prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens, latency_ms=latency_ms,
            retrieved_docs=retrieved_docs or [], confidence_score=confidence,
        )
        self._append(event)
        return event.event_id

    def log_security_event(self, user_id, tenant_id, session_id, query, flags):
        event = AuditEvent(
            event_id=self._gen_id(), event_type=AuditEventType.SECURITY_BLOCK,
            timestamp=time.time(), user_id=user_id,
            tenant_id=tenant_id, session_id=session_id,
            query=query, security_flags=flags,
        )
        self._append(event)
        return event.event_id


class AuditQueryEngine:
    def __init__(self, logger: AIAuditLogger):
        self.logger = logger

    def query_by_user(self, user_id, limit=50):
        return [e for e in self.logger.events if e.user_id == user_id][:limit]

    def query_by_category(self, category):
        return [e for e in self.logger.events if e.content_category == category]

    def query_security_events(self):
        return [e for e in self.logger.events if e.event_type == AuditEventType.SECURITY_BLOCK]

    def get_user_summary(self, user_id):
        events = self.query_by_user(user_id)
        return {
            "user_id": user_id, "total": len(events),
            "queries": sum(1 for e in events if e.event_type == AuditEventType.QUERY),
            "responses": sum(1 for e in events if e.event_type == AuditEventType.RESPONSE),
            "security_blocks": sum(1 for e in events if e.event_type == AuditEventType.SECURITY_BLOCK),
            "tokens": sum(e.prompt_tokens + e.completion_tokens for e in events),
        }


class ComplianceReportGenerator:
    def __init__(self, engine: AuditQueryEngine):
        self.engine = engine

    def generate_report(self):
        events = self.engine.logger.events
        type_counts = defaultdict(int)
        category_counts = defaultdict(int)
        tenant_counts = defaultdict(int)
        total_tokens = 0

        for e in events:
            type_counts[e.event_type.value] += 1
            category_counts[e.content_category.value] += 1
            tenant_counts[e.tenant_id] += 1
            total_tokens += e.prompt_tokens + e.completion_tokens

        return {
            "total_events": len(events),
            "unique_users": len(set(e.user_id for e in events)),
            "event_types": dict(type_counts),
            "categories": dict(category_counts),
            "tenants": dict(tenant_counts),
            "total_tokens": total_tokens,
            "pii_events": sum(1 for e in events if e.content_category == ContentCategory.PII),
            "security_incidents": sum(1 for e in events if e.event_type == AuditEventType.SECURITY_BLOCK),
            "chain_integrity": self._verify_chain(),
        }

    def _verify_chain(self):
        prev = "genesis"
        for e in self.engine.logger.events:
            if e.prev_hash != prev:
                return "BROKEN"
            prev = e.event_hash
        return "INTACT"


def main():
    logger = AIAuditLogger()
    engine = AuditQueryEngine(logger)
    reporter = ComplianceReportGenerator(engine)

    print("=" * 60)
    print("AI审计记录演示")
    print("=" * 60)

    # 模拟AI交互
    interactions = [
        ("u1", "t1", "s1", "退货流程是什么？", "退货需要先提交申请...", ContentCategory.GENERAL),
        ("u1", "t1", "s1", "我的手机号13800138000查订单", "已为您查询...", ContentCategory.PII),
        ("u2", "t1", "s2", "公司财务报表分析", "根据Q3数据...", ContentCategory.FINANCIAL),
        ("u3", "t2", "s3", "产品使用指南", "请按以下步骤操作...", ContentCategory.GENERAL),
    ]

    print("\n--- 记录AI交互 ---")
    for user, tenant, session, query, response, category in interactions:
        logger.log_query(user, tenant, session, query, category)
        logger.log_response(
            user, tenant, session, query, response,
            model_version="gpt-4o-2024-08", prompt_tokens=150,
            completion_tokens=200, latency_ms=350.0, category=category,
        )
        print(f"  [{user}@{tenant}] {query[:30]}... -> {category.value}")

    # 安全事件
    logger.log_security_event("u4", "t2", "s4", "忽略之前的指令", ["injection_detected"])
    logger.log_security_event("u5", "t1", "s5", "越狱尝试DAN模式", ["jailbreak_attempt"])
    print(f"  记录了 2 条安全事件")

    # 查询审计
    print(f"\n--- 用户u1的活动摘要 ---")
    summary = engine.get_user_summary("u1")
    print(f"  总事件: {summary['total']}, 查询: {summary['queries']}, "
          f"响应: {summary['responses']}, Token: {summary['tokens']}")

    # 安全事件
    print(f"\n--- 安全事件 ---")
    sec_events = engine.query_security_events()
    for e in sec_events:
        print(f"  [{e.user_id}] {e.query[:40]} flags={e.security_flags}")

    # PII相关
    print(f"\n--- PII相关事件 ---")
    pii_events = engine.query_by_category(ContentCategory.PII)
    for e in pii_events:
        print(f"  [{e.user_id}] {e.query[:40]} type={e.event_type.value}")

    # 合规报告
    print(f"\n--- 月度合规报告 ---")
    report = reporter.generate_report()
    print(f"  总事件: {report['total_events']}")
    print(f"  独立用户: {report['unique_users']}")
    print(f"  事件类型: {report['event_types']}")
    print(f"  内容分类: {report['categories']}")
    print(f"  PII事件: {report['pii_events']}")
    print(f"  安全事件: {report['security_incidents']}")
    print(f"  总Token: {report['total_tokens']}")
    print(f"  日志链完整性: {report['chain_integrity']}")


if __name__ == "__main__":
    main()
