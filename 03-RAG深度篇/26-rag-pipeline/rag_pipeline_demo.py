"""
生产级RAG Pipeline演示
======================
配套文章：生产级RAG Pipeline：从知识摄入到推理的全链路

演示内容：
1. 异步索引管道（队列 + 重试 + 死信）
2. 数据版本管理（快照 + 回滚 + diff）
3. 监控告警与成本分析
4. 完整Pipeline编排

运行方式：python rag_pipeline_demo.py
依赖：Python 3.10+，无外部依赖
"""

import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque


# ============================================================
# 第一部分：异步索引管道
# ============================================================

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class IndexTask:
    """索引任务"""
    doc_id: str
    content: str
    source: str
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()


class AsyncIndexPipeline:
    """异步索引管道：队列 + 批量处理 + 重试 + 死信"""

    def __init__(self, batch_size: int = 10, failure_rate: float = 0.1):
        self.task_queue: deque[IndexTask] = deque()
        self.dead_letter_queue: list[IndexTask] = []
        self.completed: list[IndexTask] = []
        self.batch_size = batch_size
        self.failure_rate = failure_rate

    def submit(self, doc_id: str, content: str, source: str) -> IndexTask:
        """提交索引任务到队列"""
        task = IndexTask(doc_id=doc_id, content=content, source=source)
        self.task_queue.append(task)
        return task

    def process_batch(self) -> dict:
        """批量处理队列中的任务"""
        batch = []
        while self.task_queue and len(batch) < self.batch_size:
            batch.append(self.task_queue.popleft())

        results = {"success": 0, "failed": 0, "dead_letter": 0}
        for task in batch:
            task.status = TaskStatus.PROCESSING
            success = self._process_single(task)
            if success:
                task.status = TaskStatus.COMPLETED
                self.completed.append(task)
                results["success"] += 1
            else:
                task.retry_count += 1
                if task.retry_count >= task.max_retries:
                    task.status = TaskStatus.DEAD_LETTER
                    self.dead_letter_queue.append(task)
                    results["dead_letter"] += 1
                else:
                    task.status = TaskStatus.PENDING
                    self.task_queue.append(task)
                    results["failed"] += 1
        return results

    def _process_single(self, task: IndexTask) -> bool:
        """处理单个任务（模拟解析+向量化+写入）"""
        return random.random() >= self.failure_rate

    def get_stats(self) -> dict:
        return {
            "queue_depth": len(self.task_queue),
            "completed": len(self.completed),
            "dead_letter": len(self.dead_letter_queue),
        }


# ============================================================
# 第二部分：数据版本管理
# ============================================================

@dataclass
class VersionSnapshot:
    """版本快照"""
    version_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    doc_count: int = 0
    doc_hashes: dict = field(default_factory=dict)
    status: str = "active"


class VersionManager:
    """向量库版本管理器：快照 + 回滚 + diff"""

    def __init__(self):
        self.versions: list[VersionSnapshot] = []
        self.current_version: VersionSnapshot | None = None

    def create_snapshot(self, doc_hashes: dict) -> VersionSnapshot:
        """创建新版本快照"""
        version_id = f"v{len(self.versions) + 1}_{datetime.now().strftime('%Y%m%d%H%M')}"
        snapshot = VersionSnapshot(
            version_id=version_id,
            doc_count=len(doc_hashes),
            doc_hashes=dict(doc_hashes),
        )
        if self.current_version:
            self.current_version.status = "archived"
        self.versions.append(snapshot)
        self.current_version = snapshot
        return snapshot

    def rollback(self, target_version_id: str) -> bool:
        """回滚到指定版本"""
        target = None
        for v in self.versions:
            if v.version_id == target_version_id:
                target = v
                break
        if not target:
            return False
        if self.current_version:
            self.current_version.status = "rolled_back"
        target.status = "active"
        self.current_version = target
        return True

    def diff(self, v1_id: str, v2_id: str) -> dict:
        """对比两个版本的差异"""
        v1 = v2 = None
        for v in self.versions:
            if v.version_id == v1_id:
                v1 = v
            if v.version_id == v2_id:
                v2 = v
        if not v1 or not v2:
            return {"error": "version not found"}

        added = set(v2.doc_hashes.keys()) - set(v1.doc_hashes.keys())
        removed = set(v1.doc_hashes.keys()) - set(v2.doc_hashes.keys())
        common = set(v1.doc_hashes.keys()) & set(v2.doc_hashes.keys())
        modified = {d for d in common if v1.doc_hashes[d] != v2.doc_hashes[d]}

        return {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "unchanged": len(common) - len(modified),
        }


# ============================================================
# 第三部分：监控告警与成本分析
# ============================================================

@dataclass
class PipelineMetrics:
    """Pipeline运行指标"""
    index_latency_ms: float = 0.0
    query_latency_ms: float = 0.0
    token_input: int = 0
    token_output: int = 0
    retrieval_hit: bool = False
    tenant_id: str = "default"
    scenario: str = "general"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MonitoringDashboard:
    """监控仪表盘：指标采集 + 告警 + 成本分析"""

    def __init__(self):
        self.metrics: list[PipelineMetrics] = []
        self.alerts: list[dict] = []
        self.thresholds = {
            "query_latency_p99_ms": 2000,
            "hit_rate_min": 0.75,
            "daily_token_budget": 1_000_000,
        }

    def record(self, metric: PipelineMetrics):
        """记录一条指标"""
        self.metrics.append(metric)
        self._check_alerts(metric)

    def _check_alerts(self, metric: PipelineMetrics):
        """检查是否触发告警"""
        if metric.query_latency_ms > self.thresholds["query_latency_p99_ms"]:
            self.alerts.append({
                "type": "latency_spike",
                "message": f"查询延迟 {metric.query_latency_ms:.0f}ms 超过阈值 {self.thresholds['query_latency_p99_ms']}ms",
                "timestamp": metric.timestamp,
            })

    def cost_by_tenant(self) -> dict:
        """按租户拆分Token消耗和成本"""
        tenant_usage = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0})
        for m in self.metrics:
            tenant_usage[m.tenant_id]["input_tokens"] += m.token_input
            tenant_usage[m.tenant_id]["output_tokens"] += m.token_output

        cost_report = {}
        for tenant, usage in tenant_usage.items():
            input_cost = usage["input_tokens"] / 1_000_000 * 2.5
            output_cost = usage["output_tokens"] / 1_000_000 * 10.0
            cost_report[tenant] = {
                **usage,
                "input_cost_usd": round(input_cost, 4),
                "output_cost_usd": round(output_cost, 4),
                "total_cost_usd": round(input_cost + output_cost, 4),
            }
        return cost_report

    def hit_rate(self) -> float:
        if not self.metrics:
            return 0.0
        hits = sum(1 for m in self.metrics if m.retrieval_hit)
        return hits / len(self.metrics)

    def summary(self) -> dict:
        if not self.metrics:
            return {"total_queries": 0}
        latencies = sorted(m.query_latency_ms for m in self.metrics if m.query_latency_ms > 0)
        p50 = latencies[len(latencies) // 2] if latencies else 0
        p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
        return {
            "total_queries": len(self.metrics),
            "hit_rate": round(self.hit_rate(), 4),
            "latency_p50_ms": round(p50, 1),
            "latency_p99_ms": round(p99, 1),
            "total_alerts": len(self.alerts),
        }


# ============================================================
# 第四部分：完整Pipeline编排
# ============================================================

class ProductionRAGPipeline:
    """生产级RAG Pipeline：摄入 → 索引 → 查询 → 监控"""

    def __init__(self):
        self.index_pipeline = AsyncIndexPipeline(batch_size=5, failure_rate=0.1)
        self.version_manager = VersionManager()
        self.dashboard = MonitoringDashboard()

    def ingest_documents(self, documents: list[dict]):
        """摄入文档到索引队列"""
        for doc in documents:
            self.index_pipeline.submit(
                doc_id=doc["id"],
                content=doc["content"],
                source=doc.get("source", "unknown"),
            )

    def run_indexing(self) -> dict:
        """执行索引（可能需要多轮处理重试任务）"""
        total_results = {"success": 0, "failed": 0, "dead_letter": 0}
        max_rounds = 5
        for _ in range(max_rounds):
            if not self.index_pipeline.task_queue:
                break
            batch_result = self.index_pipeline.process_batch()
            for k in total_results:
                total_results[k] += batch_result[k]
        return total_results

    def create_version(self) -> VersionSnapshot:
        """为当前索引创建版本快照"""
        doc_hashes = {
            task.doc_id: task.content_hash
            for task in self.index_pipeline.completed
        }
        return self.version_manager.create_snapshot(doc_hashes)

    def simulate_query(self, query: str, tenant_id: str = "default") -> dict:
        """模拟一次RAG查询（含监控埋点）"""
        start = time.time()

        # 模拟检索 + 生成
        hit = random.random() > 0.2
        token_in = random.randint(500, 2000)
        token_out = random.randint(100, 500)
        # 模拟延迟
        latency = random.uniform(200, 2500)
        time.sleep(0.001)  # 象征性等待

        elapsed = (time.time() - start) * 1000 + latency

        # 记录指标
        self.dashboard.record(PipelineMetrics(
            query_latency_ms=elapsed,
            token_input=token_in,
            token_output=token_out,
            retrieval_hit=hit,
            tenant_id=tenant_id,
        ))

        return {
            "query": query,
            "hit": hit,
            "latency_ms": round(elapsed, 1),
            "tokens": token_in + token_out,
        }


# ============================================================
# 演示入口
# ============================================================

def demo_async_index():
    """演示1：异步索引管道"""
    print("\n--- 1. 异步索引管道 ---")
    pipeline = AsyncIndexPipeline(batch_size=5, failure_rate=0.15)

    # 提交20个文档
    for i in range(20):
        pipeline.submit(f"doc_{i:03d}", f"这是第{i}篇文档的内容，包含知识库信息。", "upload")
    print(f"提交任务数: 20, 队列深度: {pipeline.get_stats()['queue_depth']}")

    # 多轮处理（含重试）
    round_num = 0
    while pipeline.task_queue:
        round_num += 1
        result = pipeline.process_batch()
        stats = pipeline.get_stats()
        print(f"  第{round_num}轮: 成功={result['success']}, 重试={result['failed']}, "
              f"死信={result['dead_letter']}, 队列剩余={stats['queue_depth']}")
        if round_num > 10:
            break

    stats = pipeline.get_stats()
    print(f"最终统计: 完成={stats['completed']}, 死信={stats['dead_letter']}, 队列={stats['queue_depth']}")


def demo_version_management():
    """演示2：数据版本管理"""
    print("\n--- 2. 数据版本管理 ---")
    vm = VersionManager()

    # 创建v1：10篇文档
    v1_hashes = {f"doc_{i}": hashlib.md5(f"content_v1_{i}".encode()).hexdigest() for i in range(10)}
    v1 = vm.create_snapshot(v1_hashes)
    print(f"创建 {v1.version_id}: {v1.doc_count}篇文档")

    # 创建v2：修改3篇 + 新增2篇 + 删除1篇
    v2_hashes = dict(v1_hashes)
    for i in range(3):
        v2_hashes[f"doc_{i}"] = hashlib.md5(f"content_v2_{i}".encode()).hexdigest()
    v2_hashes["doc_10"] = hashlib.md5(b"new_doc_10").hexdigest()
    v2_hashes["doc_11"] = hashlib.md5(b"new_doc_11").hexdigest()
    del v2_hashes["doc_9"]
    v2 = vm.create_snapshot(v2_hashes)
    print(f"创建 {v2.version_id}: {v2.doc_count}篇文档")

    # 版本对比
    diff = vm.diff(v1.version_id, v2.version_id)
    print(f"版本对比 ({v1.version_id} → {v2.version_id}):")
    print(f"  新增={diff['added']}, 删除={diff['removed']}, "
          f"修改={diff['modified']}, 未变={diff['unchanged']}")

    # 回滚
    print(f"当前版本: {vm.current_version.version_id}")
    vm.rollback(v1.version_id)
    print(f"回滚后版本: {vm.current_version.version_id}")


def demo_monitoring():
    """演示3：监控告警与成本分析"""
    print("\n--- 3. 监控告警与成本分析 ---")
    dashboard = MonitoringDashboard()

    # 模拟50次查询
    tenants = ["tenant_A", "tenant_B", "tenant_C"]
    for i in range(50):
        dashboard.record(PipelineMetrics(
            query_latency_ms=random.uniform(200, 3000),
            token_input=random.randint(500, 2000),
            token_output=random.randint(100, 500),
            retrieval_hit=random.random() > 0.2,
            tenant_id=random.choice(tenants),
        ))

    summary = dashboard.summary()
    print(f"总查询数: {summary['total_queries']}")
    print(f"命中率: {summary['hit_rate']:.2%}")
    print(f"延迟 P50: {summary['latency_p50_ms']:.0f}ms, P99: {summary['latency_p99_ms']:.0f}ms")
    print(f"触发告警数: {summary['total_alerts']}")

    # 成本分析
    cost = dashboard.cost_by_tenant()
    print("按租户成本拆分:")
    for tenant, info in cost.items():
        print(f"  {tenant}: input={info['input_tokens']:,} tokens, "
              f"output={info['output_tokens']:,} tokens, "
              f"成本=${info['total_cost_usd']:.4f}")


def demo_full_pipeline():
    """演示4：完整Pipeline编排"""
    print("\n--- 4. 完整Pipeline编排 ---")
    pipeline = ProductionRAGPipeline()

    # Step 1: 摄入文档
    documents = [
        {"id": f"kb_{i:03d}", "content": f"知识库文档{i}：包含产品FAQ和操作指南。", "source": "knowledge_base"}
        for i in range(15)
    ]
    pipeline.ingest_documents(documents)
    print(f"Step 1 - 摄入: {len(documents)}篇文档已入队")

    # Step 2: 执行索引
    index_result = pipeline.run_indexing()
    print(f"Step 2 - 索引: 成功={index_result['success']}, 死信={index_result['dead_letter']}")

    # Step 3: 创建版本快照
    version = pipeline.create_version()
    print(f"Step 3 - 版本: {version.version_id} ({version.doc_count}篇文档)")

    # Step 4: 模拟查询
    queries = ["退货流程是什么", "年假怎么算", "报销需要什么材料"]
    tenants = ["tenant_A", "tenant_B"]
    print("Step 4 - 查询:")
    for q in queries:
        result = pipeline.simulate_query(q, tenant_id=random.choice(tenants))
        status = "✅命中" if result["hit"] else "❌未命中"
        print(f"  [{status}] {result['query']} | 延迟={result['latency_ms']:.0f}ms | tokens={result['tokens']}")

    # Step 5: 查看监控
    summary = pipeline.dashboard.summary()
    print(f"Step 5 - 监控: 命中率={summary['hit_rate']:.2%}, "
          f"P50={summary['latency_p50_ms']:.0f}ms, 告警={summary['total_alerts']}")


if __name__ == "__main__":
    print("=" * 50)
    print("  生产级RAG Pipeline演示")
    print("=" * 50)

    random.seed(42)  # 固定随机种子，保证可复现

    demo_async_index()
    demo_version_management()
    demo_monitoring()
    demo_full_pipeline()

    print("\n" + "=" * 50)
    print("  演示完成！")
    print("=" * 50)
