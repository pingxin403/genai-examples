"""
内部知识问答演示：多源数据融合 + 权限过滤 + 引用溯源
对应文章：79-内部知识问答多源数据融合加权限过滤加引用溯源
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    source: str
    access_level: str  # public / department / role / personal
    department: str = ""
    allowed_roles: list[str] = field(default_factory=list)
    owner: str = ""
    section: str = ""


@dataclass
class UserContext:
    user_id: str
    name: str
    department: str
    roles: list[str] = field(default_factory=list)


class MultiSourceConnector:
    """多源数据连接器"""

    def __init__(self):
        self.documents: list[Document] = []

    def ingest(self, source: str, docs: list[Document]):
        for doc in docs:
            doc.source = source
            self.documents.append(doc)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        results = []
        q_chars = set(query)
        for doc in self.documents:
            doc_chars = set(doc.title) | set(doc.content[:100])
            overlap = len(q_chars & doc_chars)
            total = len(q_chars | doc_chars)
            score = overlap / total if total > 0 else 0
            if score > 0.05:
                results.append({"doc": doc, "score": round(score, 3)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


class PermissionFilter:
    """权限过滤器"""

    def filter(self, results: list[dict], user: UserContext) -> list[dict]:
        filtered = []
        for r in results:
            doc = r["doc"]
            if self._has_access(doc, user):
                r["access_granted"] = True
                filtered.append(r)
        return filtered

    def _has_access(self, doc: Document, user: UserContext) -> bool:
        if doc.access_level == "public":
            return True
        if doc.access_level == "department":
            return doc.department == user.department
        if doc.access_level == "role":
            return bool(set(doc.allowed_roles) & set(user.roles))
        if doc.access_level == "personal":
            return doc.owner == user.user_id
        return False


class CitationTracker:
    """引用溯源"""

    def annotate(self, answer: str, sources: list[dict]) -> dict:
        citations = []
        for i, src in enumerate(sources, 1):
            doc = src["doc"]
            citations.append({
                "index": i,
                "title": doc.title,
                "source": doc.source,
                "section": doc.section or "全文",
                "access_level": doc.access_level,
                "doc_id": doc.doc_id,
            })
        annotated = answer
        for c in citations:
            annotated += f"\n  [{c['index']}] {c['title']} ({c['source']}, {c['section']})"
        return {
            "answer": answer,
            "annotated_answer": annotated,
            "citations": citations,
        }


class KnowledgeQASystem:
    """知识问答系统主控"""

    def __init__(self):
        self.connector = MultiSourceConnector()
        self.permission = PermissionFilter()
        self.citation = CitationTracker()

    def query(self, question: str, user: UserContext) -> dict:
        # 1. 多源检索
        raw_results = self.connector.search(question)

        # 2. 权限过滤
        filtered = self.permission.filter(raw_results, user)

        if not filtered:
            return {
                "answer": "抱歉，未找到您有权限访问的相关信息。",
                "citations": [],
                "filtered_count": len(raw_results) - len(filtered),
            }

        # 3. 生成回答（模拟）
        best = filtered[0]["doc"]
        answer = f"根据{best.title}：{best.content[:100]}"

        # 4. 引用溯源
        result = self.citation.annotate(answer, filtered[:3])
        result["filtered_count"] = len(raw_results) - len(filtered)
        result["total_searched"] = len(raw_results)
        return result


def build_test_data() -> list[Document]:
    return [
        Document("d1", "年假政策", "员工入职满一年享有5天年假，满三年10天，满十年15天。",
                 "", "public", section="第三章 休假制度"),
        Document("d2", "高管薪资方案", "VP级别年薪范围80-150万，含股票期权。",
                 "", "role", allowed_roles=["hr_admin", "cfo"],
                 section="薪酬体系"),
        Document("d3", "研发部OKR", "Q4目标：完成AI平台2.0上线，DAU提升30%。",
                 "", "department", department="研发部",
                 section="2024 Q4 OKR"),
        Document("d4", "产品使用手册", "登录后点击左侧菜单进入工作台，可查看待办事项。",
                 "", "public", section="快速入门"),
        Document("d5", "张三绩效评估", "2024年度绩效评级：A，晋升建议：高级工程师。",
                 "", "personal", owner="zhangsan",
                 section="年度绩效"),
        Document("d6", "财务报表Q3", "Q3营收1.2亿，同比增长25%，净利润率18%。",
                 "", "role", allowed_roles=["cfo", "ceo"],
                 section="季度财报"),
        Document("d7", "新员工入职指南", "入职第一天请到HR部门领取工牌和电脑。",
                 "", "public", section="入职流程"),
    ]


def main():
    system = KnowledgeQASystem()

    print("=" * 60)
    print("内部知识问答系统演示")
    print("=" * 60)

    # 1. 导入多源数据
    print("\n--- 1. 多源数据导入 ---")
    docs = build_test_data()
    confluence_docs = [d for d in docs if d.doc_id in ("d1", "d2", "d3")]
    feishu_docs = [d for d in docs if d.doc_id in ("d4", "d5")]
    db_docs = [d for d in docs if d.doc_id in ("d6", "d7")]

    system.connector.ingest("confluence", confluence_docs)
    system.connector.ingest("feishu", feishu_docs)
    system.connector.ingest("database", db_docs)
    print(f"  Confluence: {len(confluence_docs)}篇")
    print(f"  飞书文档: {len(feishu_docs)}篇")
    print(f"  数据库: {len(db_docs)}篇")
    print(f"  总计: {len(docs)}篇")

    # 2. 定义用户
    users = [
        UserContext("intern01", "实习生小王", "研发部", ["intern"]),
        UserContext("zhangsan", "张三", "研发部", ["engineer"]),
        UserContext("hr_admin", "HR李姐", "人力资源部", ["hr_admin"]),
        UserContext("cfo", "CFO王总", "财务部", ["cfo", "executive"]),
    ]

    # 3. 权限过滤对比
    print("\n--- 2. 权限过滤对比 ---")
    question = "年假政策"
    print(f"  问题: {question}")
    for user in users:
        result = system.query(question, user)
        citations = result.get("citations", [])
        filtered = result.get("filtered_count", 0)
        print(f"  [{user.name}] 可见{len(citations)}条, 被过滤{filtered}条")

    # 4. 敏感信息防护
    print("\n--- 3. 敏感信息防护 ---")
    sensitive_queries = [
        ("高管薪资", users[0]),  # 实习生查薪资
        ("高管薪资", users[2]),  # HR查薪资
        ("绩效评估", users[0]),  # 实习生查别人绩效
        ("绩效评估", users[1]),  # 张三查自己绩效
        ("财务报表", users[0]),  # 实习生查财报
        ("财务报表", users[3]),  # CFO查财报
    ]

    for query, user in sensitive_queries:
        result = system.query(query, user)
        has_result = len(result.get("citations", [])) > 0
        icon = "✅" if has_result else "🔒"
        print(f"  {icon} [{user.name}] 查询'{query}' -> "
              f"{'有结果' if has_result else '无权限'}")

    # 5. 带引用的完整问答
    print("\n--- 4. 带引用溯源的问答 ---")
    qa_cases = [
        ("入职流程", users[0]),
        ("研发部目标", users[1]),
    ]

    for question, user in qa_cases:
        print(f"\n  [{user.name}] 问: {question}")
        result = system.query(question, user)
        print(f"  答: {result.get('answer', '无结果')[:80]}")
        for c in result.get("citations", []):
            print(f"    [{c['index']}] {c['title']} "
                  f"({c['source']}, {c['section']}, {c['access_level']})")


if __name__ == "__main__":
    main()
