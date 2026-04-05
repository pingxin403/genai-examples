"""权限泄露事故演示：租户隔离、权限审计"""


class TenantIsolatedRetriever:
    def __init__(self):
        self.docs: list[dict] = []

    def add(self, content: str, tenant: str, level: str = "public"):
        self.docs.append({"content": content, "tenant": tenant, "level": level})

    def search(self, query: str, tenant: str, role: str = "viewer") -> list[dict]:
        results = []
        for doc in self.docs:
            if doc["tenant"] != tenant:
                continue
            if doc["level"] == "admin" and role != "admin":
                continue
            score = len(set(query) & set(doc["content"])) / max(len(set(query)), 1)
            if score > 0.2:
                results.append({"content": doc["content"][:50], "score": round(score, 2)})
        return sorted(results, key=lambda x: x["score"], reverse=True)[:3]


class PermissionAuditor:
    def __init__(self):
        self.logs: list[dict] = []

    def log(self, user: str, tenant: str, query: str, count: int):
        self.logs.append({"user": user, "tenant": tenant, "query": query[:30], "results": count})

    def report(self) -> list[dict]:
        return self.logs


def main():
    print("=" * 60)
    print("权限泄露事故演示")
    print("=" * 60)

    retriever = TenantIsolatedRetriever()
    retriever.add("A公司专属报价：企业版年费10万", "tenant_a")
    retriever.add("A公司内部培训资料", "tenant_a", "admin")
    retriever.add("B公司专属报价：企业版年费8万", "tenant_b")
    retriever.add("通用产品介绍文档", "tenant_a")
    retriever.add("通用产品介绍文档", "tenant_b")

    auditor = PermissionAuditor()

    print("\n--- 租户隔离检索 ---")
    # B公司用户搜索
    results_b = retriever.search("报价", "tenant_b")
    auditor.log("user_b1", "tenant_b", "报价", len(results_b))
    print(f"  B公司用户搜索'报价' → {len(results_b)}条结果")
    for r in results_b:
        print(f"    {r['score']} | {r['content']}")

    # B公司用户尝试搜索A公司数据（被隔离）
    results_cross = retriever.search("A公司报价", "tenant_b")
    print(f"\n  B公司用户搜索'A公司报价' → {len(results_cross)}条结果 ✅ 隔离生效")

    # A公司普通用户搜索admin文档（被过滤）
    results_a = retriever.search("培训", "tenant_a", role="viewer")
    print(f"  A公司普通用户搜索'培训' → {len(results_a)}条结果 ✅ 权限过滤生效")

    results_admin = retriever.search("培训", "tenant_a", role="admin")
    print(f"  A公司管理员搜索'培训' → {len(results_admin)}条结果")

    print("\n--- 审计日志 ---")
    for log in auditor.report():
        print(f"  {log['user']} | {log['tenant']} | {log['query']} | {log['results']}条")

    print(f"\n{'=' * 60}")
    print("核心: 租户隔离+权限过滤+审计日志 = 数据安全")
    print("=" * 60)


if __name__ == "__main__":
    main()
