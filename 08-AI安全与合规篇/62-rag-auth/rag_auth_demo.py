"""
RAG权限集成演示：文档级权限 + 片段级过滤 + Auth集成
对应文章：62-私有知识安全RAG系统的权限怎么和Auth集成
"""

import time
from dataclasses import dataclass, field
from enum import Enum


class SecurityLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class UserContext:
    user_id: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)
    departments: list[str] = field(default_factory=list)
    security_clearance: SecurityLevel = SecurityLevel.INTERNAL
    accessible_doc_ids: set[str] = field(default_factory=set)


@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    doc_id: str
    tenant_id: str
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    owner_departments: list[str] = field(default_factory=list)
    allowed_roles: list[str] = field(default_factory=list)
    score: float = 0.0


class PermissionFilter:
    def build_metadata_filter(self, user: UserContext) -> dict:
        return {
            "tenant_id": user.tenant_id,
            "security_level": {"$in": self._allowed_levels(user.security_clearance)},
        }

    def _allowed_levels(self, clearance: SecurityLevel) -> list[str]:
        hierarchy = [
            SecurityLevel.PUBLIC, SecurityLevel.INTERNAL,
            SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED,
        ]
        idx = hierarchy.index(clearance)
        return [l.value for l in hierarchy[:idx + 1]]

    def post_filter(self, chunks: list[DocumentChunk], user: UserContext) -> list[DocumentChunk]:
        filtered = []
        for chunk in chunks:
            if chunk.tenant_id != user.tenant_id:
                continue
            if not self._check_security_level(chunk, user):
                continue
            if chunk.allowed_roles and not set(chunk.allowed_roles) & set(user.roles):
                continue
            if chunk.owner_departments and not set(chunk.owner_departments) & set(user.departments):
                if "admin" not in user.roles:
                    continue
            filtered.append(chunk)
        return filtered

    def _check_security_level(self, chunk: DocumentChunk, user: UserContext) -> bool:
        level_order = {
            SecurityLevel.PUBLIC: 0, SecurityLevel.INTERNAL: 1,
            SecurityLevel.CONFIDENTIAL: 2, SecurityLevel.RESTRICTED: 3,
        }
        return level_order[chunk.security_level] <= level_order[user.security_clearance]


class SecureRAGPipeline:
    def __init__(self):
        self.permission_filter = PermissionFilter()
        self.chunks_store: list[DocumentChunk] = []
        self.audit_log: list[dict] = []

    def add_document(self, chunk: DocumentChunk):
        self.chunks_store.append(chunk)

    def query(self, question: str, user: UserContext) -> dict:
        meta_filter = self.permission_filter.build_metadata_filter(user)

        pre_filtered = [
            c for c in self.chunks_store
            if c.tenant_id == meta_filter["tenant_id"]
            and c.security_level.value in meta_filter["security_level"]["$in"]
        ]
        for c in pre_filtered:
            c.score = self._mock_similarity(question, c.content)
        pre_filtered.sort(key=lambda x: x.score, reverse=True)
        candidates = pre_filtered[:10]

        authorized = self.permission_filter.post_filter(candidates, user)

        context = "\n".join(c.content for c in authorized[:3])
        answer = f"基于授权文档回答：{context[:100]}..." if context else "未找到您有权限访问的相关文档。"

        self.audit_log.append({
            "user_id": user.user_id, "tenant_id": user.tenant_id,
            "question": question, "chunks_retrieved": len(candidates),
            "chunks_authorized": len(authorized),
            "timestamp": time.time(),
        })

        return {
            "answer": answer,
            "sources": [{"doc_id": c.doc_id, "security": c.security_level.value} for c in authorized[:3]],
            "total_retrieved": len(candidates),
            "authorized_count": len(authorized),
        }

    def _mock_similarity(self, query: str, content: str) -> float:
        common = set(query) & set(content)
        return len(common) / max(len(set(query)), 1)


def main():
    pipeline = SecureRAGPipeline()

    # 添加不同租户和安全等级的文档
    docs = [
        DocumentChunk("c1", "退货流程：用户提交申请后3天内处理", "doc1", "tenant_A",
                       SecurityLevel.PUBLIC, ["customer_service"], []),
        DocumentChunk("c2", "A公司定价策略：基础版99元/月", "doc2", "tenant_A",
                       SecurityLevel.CONFIDENTIAL, ["sales"], ["manager"]),
        DocumentChunk("c3", "B公司产品手册：使用指南", "doc3", "tenant_B",
                       SecurityLevel.INTERNAL, ["product"], []),
        DocumentChunk("c4", "A公司内部API文档：认证接口说明", "doc4", "tenant_A",
                       SecurityLevel.RESTRICTED, ["engineering"], ["admin"]),
        DocumentChunk("c5", "A公司工程部技术规范", "doc5", "tenant_A",
                       SecurityLevel.INTERNAL, ["engineering"], []),
    ]
    for doc in docs:
        pipeline.add_document(doc)

    # 用户场景
    users = [
        ("普通客服(A)", UserContext("u1", "tenant_A", ["agent"], ["customer_service"], SecurityLevel.INTERNAL)),
        ("销售经理(A)", UserContext("u2", "tenant_A", ["manager"], ["sales"], SecurityLevel.CONFIDENTIAL)),
        ("B公司用户", UserContext("u3", "tenant_B", ["agent"], ["product"], SecurityLevel.INTERNAL)),
        ("管理员(A)", UserContext("u4", "tenant_A", ["admin"], ["engineering"], SecurityLevel.RESTRICTED)),
    ]

    print("=" * 60)
    print("RAG权限集成演示")
    print("=" * 60)

    question = "退货流程和定价策略"
    for name, user in users:
        print(f"\n--- {name} 查询: '{question}' ---")
        result = pipeline.query(question, user)
        print(f"  检索到: {result['total_retrieved']} 条, 授权: {result['authorized_count']} 条")
        print(f"  回答: {result['answer'][:80]}...")
        if result["sources"]:
            print(f"  来源: {result['sources']}")

    print(f"\n--- 审计日志 ({len(pipeline.audit_log)} 条) ---")
    for log in pipeline.audit_log:
        print(f"  user={log['user_id']} tenant={log['tenant_id']} "
              f"retrieved={log['chunks_retrieved']} authorized={log['chunks_authorized']}")


if __name__ == "__main__":
    main()
