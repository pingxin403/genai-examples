"""
数据主权合规演示：多区域部署 + 联邦检索 + 数据路由
对应文章：66-数据主权跨境知识检索的合规方案
"""

import time
from dataclasses import dataclass, field
from enum import Enum


class Region(Enum):
    EU = "eu"
    APAC = "apac"
    NA = "na"


class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    SOVEREIGN = "sovereign"


@dataclass
class SovereigntyPolicy:
    region: Region
    allowed_destinations: list[Region] = field(default_factory=list)
    requires_anonymization: bool = False


@dataclass
class RegionalDocument:
    doc_id: str
    content: str
    region: Region
    classification: DataClassification


@dataclass
class CrossRegionRequest:
    query: str
    user_region: Region
    target_regions: list[Region]
    user_id: str


class RegionRouter:
    def __init__(self):
        self.policies = {
            Region.EU: SovereigntyPolicy(Region.EU, [Region.EU], requires_anonymization=True),
            Region.APAC: SovereigntyPolicy(Region.APAC, [Region.APAC, Region.NA]),
            Region.NA: SovereigntyPolicy(Region.NA, [Region.NA, Region.APAC]),
        }

    def can_transfer(self, source: Region, destination: Region) -> dict:
        policy = self.policies.get(source)
        if not policy:
            return {"allowed": False, "reason": "unknown_region"}
        allowed = destination in policy.allowed_destinations
        return {
            "allowed": allowed,
            "requires_anonymization": policy.requires_anonymization,
            "reason": "policy_allowed" if allowed else "sovereignty_restriction",
        }


class RegionalVectorStore:
    def __init__(self, region: Region):
        self.region = region
        self.documents: list[RegionalDocument] = []

    def add(self, doc: RegionalDocument):
        self.documents.append(doc)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        scored = []
        for doc in self.documents:
            score = len(set(query) & set(doc.content)) / max(len(set(query)), 1)
            scored.append({
                "doc_id": doc.doc_id, "content": doc.content,
                "score": round(score, 3), "region": self.region.value,
                "classification": doc.classification.value,
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class DataSovereigntySystem:
    def __init__(self):
        self.router = RegionRouter()
        self.stores = {r: RegionalVectorStore(r) for r in Region}
        self.audit_log: list[dict] = []

    def add_document(self, doc: RegionalDocument):
        self.stores[doc.region].add(doc)

    def query(self, request: CrossRegionRequest) -> dict:
        results = {"local": [], "cross_region": [], "blocked": []}

        results["local"] = self.stores[request.user_region].search(request.query)

        for target in request.target_regions:
            if target == request.user_region:
                continue
            check = self.router.can_transfer(target, request.user_region)
            if check["allowed"]:
                remote = self.stores[target].search(request.query)
                if check["requires_anonymization"]:
                    remote = [
                        {**r, "content": f"[摘要] {r['content'][:20]}...", "anonymized": True}
                        for r in remote
                    ]
                results["cross_region"].extend(remote)
            else:
                results["blocked"].append({"region": target.value, "reason": check["reason"]})

        self.audit_log.append({
            "user_id": request.user_id, "user_region": request.user_region.value,
            "local": len(results["local"]), "cross": len(results["cross_region"]),
            "blocked": len(results["blocked"]), "timestamp": time.time(),
        })
        return results


def main():
    system = DataSovereigntySystem()

    # 添加各区域文档
    docs = [
        RegionalDocument("eu1", "欧洲客户隐私政策GDPR合规要求", Region.EU, DataClassification.RESTRICTED),
        RegionalDocument("eu2", "欧洲产品定价策略", Region.EU, DataClassification.INTERNAL),
        RegionalDocument("ap1", "亚太市场分析报告", Region.APAC, DataClassification.INTERNAL),
        RegionalDocument("ap2", "新加坡数据中心运维手册", Region.APAC, DataClassification.PUBLIC),
        RegionalDocument("na1", "北美销售流程文档", Region.NA, DataClassification.INTERNAL),
        RegionalDocument("na2", "美国合规审计报告", Region.NA, DataClassification.RESTRICTED),
    ]
    for doc in docs:
        system.add_document(doc)

    print("=" * 60)
    print("数据主权合规演示")
    print("=" * 60)

    # 场景1：欧洲用户本地检索
    print("\n--- 场景1: 欧洲用户本地检索 ---")
    req1 = CrossRegionRequest("隐私政策合规", Region.EU, [Region.EU], "eu_user_1")
    r1 = system.query(req1)
    print(f"  本地结果: {len(r1['local'])} 条")
    for r in r1["local"][:2]:
        print(f"    [{r['region']}] {r['content'][:40]} (score={r['score']})")

    # 场景2：北美用户跨区域检索（含EU）
    print("\n--- 场景2: 北美用户检索EU+APAC数据 ---")
    req2 = CrossRegionRequest("市场分析政策", Region.NA, [Region.NA, Region.EU, Region.APAC], "na_user_1")
    r2 = system.query(req2)
    print(f"  本地: {len(r2['local'])} 条, 跨区域: {len(r2['cross_region'])} 条, 拦截: {len(r2['blocked'])} 条")
    for r in r2["cross_region"]:
        anon = " [已匿名]" if r.get("anonymized") else ""
        print(f"    [{r['region']}] {r['content'][:40]}{anon}")
    for b in r2["blocked"]:
        print(f"    ❌ {b['region']}: {b['reason']}")

    # 场景3：亚太用户跨区域检索
    print("\n--- 场景3: 亚太用户检索NA+EU数据 ---")
    req3 = CrossRegionRequest("销售流程运维", Region.APAC, [Region.APAC, Region.NA, Region.EU], "ap_user_1")
    r3 = system.query(req3)
    print(f"  本地: {len(r3['local'])} 条, 跨区域: {len(r3['cross_region'])} 条, 拦截: {len(r3['blocked'])} 条")
    for b in r3["blocked"]:
        print(f"    ❌ {b['region']}: {b['reason']}")

    print(f"\n--- 审计日志 ({len(system.audit_log)} 条) ---")
    for log in system.audit_log:
        print(f"  user={log['user_id']} region={log['user_region']} "
              f"local={log['local']} cross={log['cross']} blocked={log['blocked']}")


if __name__ == "__main__":
    main()
