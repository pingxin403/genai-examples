"""
向量数据库选型对比Demo：Chroma / PGVector / Milvus / Qdrant
配套文章：《向量数据库选型：Chroma/PGVector/Milvus/Qdrant对比》

演示内容：
1. 模拟四款向量数据库的基准测试
2. 五维评分对比（性能/成本/多租户/一致性/运维）
3. 不同数据量级下的选型建议
4. 多租户场景性能模拟
"""

import time
import random
import numpy as np
from dataclasses import dataclass


# ============================================================
# 第一部分：向量数据库模拟器
# ============================================================

@dataclass
class BenchmarkResult:
    """基准测试结果"""
    db_name: str
    insert_rate: float        # 条/秒
    search_latency_p50: float # ms
    search_latency_p99: float # ms
    recall_at_10: float       # 召回率
    memory_mb: float          # 内存占用MB
    multi_tenant_overhead: float  # 多租户额外延迟ms


class VectorDBSimulator:
    """向量数据库模拟器（模拟真实基准测试行为）"""

    # 基于公开基准测试数据的模拟参数
    DB_PROFILES = {
        "Chroma": {
            "insert_rate_base": 5000,
            "latency_p50_base": 8,
            "latency_p99_base": 45,
            "recall_base": 0.95,
            "memory_per_10k": 80,       # MB per 10k vectors
            "tenant_overhead": 30,
            "scale_factor": 2.5,        # 数据量增大时的性能衰减系数
        },
        "PGVector": {
            "insert_rate_base": 3000,
            "latency_p50_base": 15,
            "latency_p99_base": 60,
            "recall_base": 0.98,
            "memory_per_10k": 20,
            "tenant_overhead": 5,
            "scale_factor": 1.5,
        },
        "Milvus": {
            "insert_rate_base": 50000,
            "latency_p50_base": 4,
            "latency_p99_base": 12,
            "recall_base": 0.97,
            "memory_per_10k": 40,
            "tenant_overhead": 3,
            "scale_factor": 1.1,
        },
        "Qdrant": {
            "insert_rate_base": 40000,
            "latency_p50_base": 5,
            "latency_p99_base": 15,
            "recall_base": 0.97,
            "memory_per_10k": 30,
            "tenant_overhead": 2,
            "scale_factor": 1.15,
        },
    }

    @classmethod
    def benchmark(cls, db_name: str, num_vectors: int,
                  dimension: int = 1536) -> BenchmarkResult:
        """模拟指定数据库的基准测试"""
        profile = cls.DB_PROFILES[db_name]
        scale = (num_vectors / 100_000) ** (profile["scale_factor"] - 1)
        scale = max(scale, 1.0)

        # 添加随机波动（模拟真实测试的不确定性）
        jitter = lambda base: base * (1 + random.uniform(-0.05, 0.05))

        return BenchmarkResult(
            db_name=db_name,
            insert_rate=jitter(profile["insert_rate_base"] / max(scale * 0.3, 1)),
            search_latency_p50=jitter(profile["latency_p50_base"] * scale),
            search_latency_p99=jitter(profile["latency_p99_base"] * scale),
            recall_at_10=min(profile["recall_base"] + random.uniform(-0.01, 0.01), 1.0),
            memory_mb=profile["memory_per_10k"] * (num_vectors / 10_000),
            multi_tenant_overhead=jitter(profile["tenant_overhead"]),
        )


# ============================================================
# 第二部分：五维评分系统
# ============================================================

class FiveDimensionScorer:
    """五维评分：性能 / 运维成本 / 多租户 / 一致性 / 总拥有成本"""

    SCORES = {
        "Chroma":   {"性能": 3, "运维成本": 5, "多租户": 2, "一致性": 2, "总拥有成本": 5},
        "PGVector": {"性能": 3, "运维成本": 4, "多租户": 3, "一致性": 5, "总拥有成本": 4},
        "Milvus":   {"性能": 5, "运维成本": 2, "多租户": 4, "一致性": 4, "总拥有成本": 2},
        "Qdrant":   {"性能": 5, "运维成本": 3, "多租户": 5, "一致性": 4, "总拥有成本": 3},
    }

    @classmethod
    def print_radar(cls):
        """打印五维评分对比表"""
        dimensions = ["性能", "运维成本", "多租户", "一致性", "总拥有成本"]
        print("\n📊 五维评分对比（满分5分）")
        print("-" * 65)
        header = f"{'维度':<10}" + "".join(f"{db:<12}" for db in cls.SCORES)
        print(header)
        print("-" * 65)
        for dim in dimensions:
            row = f"{dim:<10}"
            for db in cls.SCORES:
                score = cls.SCORES[db][dim]
                stars = "⭐" * score + "  " * (5 - score)
                row += f"{stars:<12}"
            print(row)
        print("-" * 65)

        # 加权总分
        weights = {"性能": 0.3, "运维成本": 0.2, "多租户": 0.2, "一致性": 0.15, "总拥有成本": 0.15}
        print(f"\n{'加权总分':<10}", end="")
        for db in cls.SCORES:
            total = sum(cls.SCORES[db][d] * weights[d] for d in dimensions)
            print(f"{total:.1f}/5.0     ", end="")
        print()

    @classmethod
    def recommend(cls, scenario: str) -> str:
        """根据场景推荐数据库"""
        recommendations = {
            "poc": ("Chroma", "零配置、5行代码上手，适合快速验证想法"),
            "existing_pg": ("PGVector", "无需引入新基础设施，DBA可直接运维"),
            "large_scale": ("Milvus", "十亿级数据+分布式扩展，生产级首选"),
            "multi_tenant": ("Qdrant", "原生payload过滤，多租户几乎零额外开销"),
            "high_perf": ("Qdrant", "Rust实现，单机性能优异，部署简单"),
        }
        return recommendations.get(scenario, ("Qdrant", "综合表现均衡"))


# ============================================================
# 第三部分：多租户场景模拟
# ============================================================

def simulate_multi_tenant(num_tenants: int = 50, docs_per_tenant: int = 10000):
    """模拟多租户场景下的性能对比"""
    total_docs = num_tenants * docs_per_tenant

    print(f"\n🏢 多租户场景模拟：{num_tenants}个租户，每租户{docs_per_tenant:,}条数据")
    print(f"   总数据量：{total_docs:,}条")
    print("-" * 65)

    strategies = {
        "Chroma": "每租户独立Collection",
        "PGVector": "共享表 + tenant_id字段 + 分区",
        "Milvus": "共享Collection + partition_key",
        "Qdrant": "共享Collection + payload过滤",
    }

    for db_name, strategy in strategies.items():
        result = VectorDBSimulator.benchmark(db_name, total_docs)
        tenant_latency = result.search_latency_p50 + result.multi_tenant_overhead
        print(f"\n  {db_name}:")
        print(f"    隔离策略：{strategy}")
        print(f"    无过滤延迟：{result.search_latency_p50:.1f}ms")
        print(f"    租户过滤延迟：{tenant_latency:.1f}ms (+{result.multi_tenant_overhead:.1f}ms)")
        print(f"    管理复杂度：{'高（需管理' + str(num_tenants) + '个Collection）' if db_name == 'Chroma' else '低（单Collection）'}")


# ============================================================
# 第四部分：数据量级敏感性分析
# ============================================================

def scale_analysis():
    """不同数据量级下的性能对比"""
    scales = [10_000, 100_000, 1_000_000, 10_000_000]
    db_names = ["Chroma", "PGVector", "Milvus", "Qdrant"]

    print("\n📈 数据量级敏感性分析")
    print("=" * 75)

    # 表头
    header = f"{'数据量':<15}"
    for db in db_names:
        header += f"{db:<15}"
    print(header)
    print("-" * 75)

    for scale in scales:
        row = f"{scale:>10,}条   "
        for db in db_names:
            result = VectorDBSimulator.benchmark(db, scale)
            row += f"P50={result.search_latency_p50:>6.1f}ms   "
        print(row)

    # 选型建议
    print("\n💡 选型建议：")
    for scale in scales:
        if scale <= 100_000:
            print(f"  {scale:>10,}条 → Chroma / PGVector（轻量方案足够）")
        elif scale <= 1_000_000:
            print(f"  {scale:>10,}条 → PGVector / Qdrant（平衡性能与成本）")
        else:
            print(f"  {scale:>10,}条 → Milvus / Qdrant（需要专用向量数据库）")


# ============================================================
# 第五部分：选型决策引擎
# ============================================================

def selection_wizard():
    """交互式选型建议"""
    print("\n🧭 向量数据库选型决策")
    print("=" * 65)

    scenarios = [
        ("POC/个人项目", "poc",
         "数据量<10万，快速验证，不需要生产级可靠性"),
        ("已有PostgreSQL", "existing_pg",
         "团队已有PG运维能力，不想引入新基础设施"),
        ("大规模生产环境", "large_scale",
         "数据量>500万，需要分布式扩展和高可用"),
        ("多租户SaaS", "multi_tenant",
         "需要租户级数据隔离，租户数>10"),
        ("高性能低延迟", "high_perf",
         "P99延迟要求<20ms，单机部署优先"),
    ]

    for desc, key, detail in scenarios:
        db, reason = FiveDimensionScorer.recommend(key)
        print(f"\n  场景：{desc}")
        print(f"  说明：{detail}")
        print(f"  推荐：✅ {db} — {reason}")


# ============================================================
# 主程序
# ============================================================

def main():
    random.seed(42)

    print("=" * 70)
    print("📈 向量数据库选型对比：Chroma / PGVector / Milvus / Qdrant")
    print("=" * 70)

    # 1. 基准测试（100万条数据）
    print("\n🔬 基准测试（100万条 × 1536维向量）")
    print("-" * 70)
    print(f"{'数据库':<12}{'插入(条/秒)':<14}{'P50延迟':<10}{'P99延迟':<10}"
          f"{'召回率@10':<12}{'内存占用':<10}")
    print("-" * 70)

    for db_name in ["Chroma", "PGVector", "Milvus", "Qdrant"]:
        result = VectorDBSimulator.benchmark(db_name, 1_000_000)
        print(f"{result.db_name:<12}"
              f"{result.insert_rate:>8,.0f}     "
              f"{result.search_latency_p50:>6.1f}ms  "
              f"{result.search_latency_p99:>6.1f}ms  "
              f"{result.recall_at_10:>8.1%}    "
              f"{result.memory_mb:>6,.0f}MB")

    # 2. 五维评分
    FiveDimensionScorer.print_radar()

    # 3. 多租户场景
    simulate_multi_tenant(num_tenants=50, docs_per_tenant=10_000)

    # 4. 数据量级分析
    scale_analysis()

    # 5. 选型建议
    selection_wizard()

    print("\n" + "=" * 70)
    print("✅ Demo完成！选型核心原则：先用轻量方案验证，等瓶颈出现再迁移")
    print("=" * 70)


if __name__ == "__main__":
    main()
