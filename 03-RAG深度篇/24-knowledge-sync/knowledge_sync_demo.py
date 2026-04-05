"""
知识同步示例 - CDC+版本控制方案
配套文章：《知识更新了，向量库咋同步？CDC+版本控制方案》

演示内容：
1. 文件哈希CDC变更检测：基于SHA256检测文档新增/修改/删除
2. 带版本控制的向量同步：旧版本软删除 + 新版本写入
3. 过期向量清理：定时清理不活跃的旧版本chunk
4. 完整管道编排：变更检测 → 增量同步 → 过期清理
"""

import hashlib
import json
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


# ============================================================
# 变更类型定义
# ============================================================

class ChangeType(Enum):
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class ChangeEvent:
    """变更事件"""
    file_path: str
    change_type: ChangeType
    old_hash: str = ""
    new_hash: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# 策略1: 文件哈希CDC变更检测
# ============================================================

class FileHashCDC:
    """
    基于文件内容哈希的变更检测器。
    每次扫描时比较当前文件哈希与上次记录的哈希，
    检测新增、修改、删除三种变更。
    """

    def __init__(self):
        self.state: dict[str, str] = {}  # {file_path: hash}

    def detect_changes(self, files: dict[str, str]) -> list[ChangeEvent]:
        """
        检测变更。
        Args:
            files: 当前文件集合 {file_path: content}
        Returns:
            变更事件列表
        """
        changes = []
        current_hashes = {}

        # 检测新增和修改
        for path, content in files.items():
            file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
            current_hashes[path] = file_hash

            if path not in self.state:
                changes.append(ChangeEvent(
                    file_path=path,
                    change_type=ChangeType.CREATED,
                    new_hash=file_hash,
                ))
            elif self.state[path] != file_hash:
                changes.append(ChangeEvent(
                    file_path=path,
                    change_type=ChangeType.MODIFIED,
                    old_hash=self.state[path],
                    new_hash=file_hash,
                ))

        # 检测删除
        for old_path in self.state:
            if old_path not in current_hashes:
                changes.append(ChangeEvent(
                    file_path=old_path,
                    change_type=ChangeType.DELETED,
                    old_hash=self.state[old_path],
                ))

        # 更新状态
        self.state = current_hashes
        return changes


def demo_file_hash_cdc():
    """演示文件哈希CDC变更检测"""
    print("=" * 60)
    print("Demo 1: 文件哈希CDC变更检测")
    print("=" * 60)
    print()

    cdc = FileHashCDC()

    # --- 第1次扫描：初始化 ---
    files_v1 = {
        "docs/policy.md": "员工年假天数根据工龄计算，5年以下5天",
        "docs/faq.md": "Q: 年假怎么请？A: 在OA系统提交申请",
        "docs/guide.md": "新员工入职指南：第一天报到流程",
    }

    print("--- 第1次扫描（初始化）---")
    changes = cdc.detect_changes(files_v1)
    print(f"  检测到 {len(changes)} 个变更:")
    for c in changes:
        print(f"    [{c.change_type.value.upper():8s}] {c.file_path}")
    print()

    # --- 第2次扫描：无变更 ---
    print("--- 第2次扫描（无变更）---")
    changes = cdc.detect_changes(files_v1)
    print(f"  检测到 {len(changes)} 个变更（预期为0）")
    print()

    # --- 第3次扫描：修改一个文件 ---
    files_v2 = files_v1.copy()
    files_v2["docs/policy.md"] = "员工年假天数根据工龄计算，5年以下7天（2024年新政策）"

    print("--- 第3次扫描（修改policy.md）---")
    changes = cdc.detect_changes(files_v2)
    print(f"  检测到 {len(changes)} 个变更:")
    for c in changes:
        print(f"    [{c.change_type.value.upper():8s}] {c.file_path}")
        if c.old_hash:
            print(f"      哈希: {c.old_hash} → {c.new_hash}")
    print()

    # --- 第4次扫描：删除一个文件 + 新增一个文件 ---
    files_v3 = {k: v for k, v in files_v2.items() if k != "docs/guide.md"}
    files_v3["docs/benefits.md"] = "2024年员工福利手册"

    print("--- 第4次扫描（删除guide.md + 新增benefits.md）---")
    changes = cdc.detect_changes(files_v3)
    print(f"  检测到 {len(changes)} 个变更:")
    for c in changes:
        print(f"    [{c.change_type.value.upper():8s}] {c.file_path}")
    print()


# ============================================================
# 策略2: 带版本控制的向量同步
# ============================================================

@dataclass
class VectorRecord:
    """向量记录（带版本号）"""
    chunk_id: str
    doc_id: str
    version: int
    content: str
    embedding: list[float]
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class VersionedVectorSync:
    """
    带版本控制的向量同步器。
    - 新增文档：解析分块后写入，版本号=1
    - 修改文档：旧版本软删除，新版本写入，版本号+1
    - 删除文档：所有chunk软删除
    - 定时清理：硬删除所有不活跃的chunk
    """

    def __init__(self):
        self.vectors: dict[str, VectorRecord] = {}
        self.doc_versions: dict[str, int] = {}

    def handle_change(self, event: ChangeEvent, content: str = ""):
        """根据变更事件执行同步"""
        if event.change_type == ChangeType.CREATED:
            self._handle_create(event, content)
        elif event.change_type == ChangeType.MODIFIED:
            self._handle_modify(event, content)
        elif event.change_type == ChangeType.DELETED:
            self._handle_delete(event)

    def _handle_create(self, event: ChangeEvent, content: str):
        """新文档入库"""
        doc_id = event.file_path
        version = 1
        self.doc_versions[doc_id] = version

        chunks = self._simulate_chunking(content or doc_id)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}::v{version}::chunk_{i}"
            self.vectors[chunk_id] = VectorRecord(
                chunk_id=chunk_id,
                doc_id=doc_id,
                version=version,
                content=chunk,
                embedding=self._simulate_embedding(chunk),
            )
        print(f"    [CREATE] {doc_id} → {len(chunks)} chunks (v{version})")

    def _handle_modify(self, event: ChangeEvent, content: str):
        """文档修改：旧版本淘汰 + 新版本写入"""
        doc_id = event.file_path
        old_version = self.doc_versions.get(doc_id, 0)
        new_version = old_version + 1
        self.doc_versions[doc_id] = new_version

        # 旧版本软删除
        deactivated = 0
        for record in self.vectors.values():
            if record.doc_id == doc_id and record.is_active:
                record.is_active = False
                deactivated += 1

        # 新版本写入
        chunks = self._simulate_chunking(content or doc_id)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}::v{new_version}::chunk_{i}"
            self.vectors[chunk_id] = VectorRecord(
                chunk_id=chunk_id,
                doc_id=doc_id,
                version=new_version,
                content=chunk,
                embedding=self._simulate_embedding(chunk),
            )
        print(f"    [MODIFY] {doc_id}: v{old_version}→v{new_version}, "
              f"淘汰{deactivated}条, 新增{len(chunks)}条")

    def _handle_delete(self, event: ChangeEvent):
        """文档删除：所有chunk软删除"""
        doc_id = event.file_path
        deactivated = 0
        for record in self.vectors.values():
            if record.doc_id == doc_id and record.is_active:
                record.is_active = False
                deactivated += 1
        print(f"    [DELETE] {doc_id} → 淘汰{deactivated}条chunk")

    def cleanup_stale(self):
        """清理所有不活跃的向量（硬删除）"""
        to_delete = [cid for cid, r in self.vectors.items() if not r.is_active]
        for cid in to_delete:
            del self.vectors[cid]
        print(f"    [CLEANUP] 硬删除{len(to_delete)}条过期向量")
        return len(to_delete)

    def get_stats(self) -> dict:
        """获取向量库统计"""
        active = sum(1 for r in self.vectors.values() if r.is_active)
        stale = sum(1 for r in self.vectors.values() if not r.is_active)
        docs = len(set(r.doc_id for r in self.vectors.values() if r.is_active))
        return {"total": len(self.vectors), "active": active, "stale": stale, "docs": docs}

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """模拟检索（只返回活跃的chunk）"""
        active_records = [r for r in self.vectors.values() if r.is_active]
        # 模拟相关性排序
        results = []
        for r in active_records:
            score = len(set(query) & set(r.content)) / max(len(set(query)), 1)
            results.append({"chunk_id": r.chunk_id, "content": r.content,
                            "version": r.version, "score": round(score, 3)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _simulate_chunking(self, content: str) -> list[str]:
        """模拟分块（每个文档分成3个chunk）"""
        return [f"{content}_part{i}" for i in range(3)]

    def _simulate_embedding(self, text: str) -> list[float]:
        """模拟Embedding"""
        random.seed(hash(text) % 2**32)
        return [round(random.random(), 4) for _ in range(4)]


def demo_versioned_sync():
    """演示带版本控制的向量同步"""
    print("=" * 60)
    print("Demo 2: 带版本控制的增量同步")
    print("=" * 60)
    print()

    syncer = VersionedVectorSync()

    # 1. 新增两个文档
    print("  步骤1: 新增两个文档")
    syncer.handle_change(
        ChangeEvent("policy.md", ChangeType.CREATED),
        content="年假天数5年以下5天"
    )
    syncer.handle_change(
        ChangeEvent("faq.md", ChangeType.CREATED),
        content="年假申请流程OA提交"
    )
    stats = syncer.get_stats()
    print(f"    状态: 活跃={stats['active']}, 待清理={stats['stale']}")
    print()

    # 2. 修改一个文档
    print("  步骤2: 修改policy.md（年假从5天改为7天）")
    syncer.handle_change(
        ChangeEvent("policy.md", ChangeType.MODIFIED),
        content="年假天数5年以下7天（2024新政策）"
    )
    stats = syncer.get_stats()
    print(f"    状态: 活跃={stats['active']}, 待清理={stats['stale']}")
    print()

    # 3. 检索验证（只返回活跃版本）
    print("  步骤3: 检索验证（应只返回最新版本）")
    results = syncer.search("年假天数")
    for r in results:
        print(f"    [v{r['version']}] {r['content'][:40]}...")
    print()

    # 4. 删除一个文档
    print("  步骤4: 删除faq.md")
    syncer.handle_change(ChangeEvent("faq.md", ChangeType.DELETED))
    stats = syncer.get_stats()
    print(f"    状态: 活跃={stats['active']}, 待清理={stats['stale']}")
    print()

    # 5. 清理过期向量
    print("  步骤5: 清理过期向量")
    syncer.cleanup_stale()
    stats = syncer.get_stats()
    print(f"    状态: 活跃={stats['active']}, 待清理={stats['stale']}, 总计={stats['total']}")
    print()


# ============================================================
# 完整管道编排
# ============================================================

class KnowledgeSyncPipeline:
    """
    完整的知识同步管道。
    变更检测 → 增量同步 → 过期清理
    """

    def __init__(self):
        self.cdc = FileHashCDC()
        self.syncer = VersionedVectorSync()
        self.sync_history: list[dict] = []

    def run_sync(self, files: dict[str, str]) -> dict:
        """执行一次同步"""
        start = time.time()

        # 1. 变更检测
        changes = self.cdc.detect_changes(files)

        if not changes:
            return {"changes": 0, "latency_ms": 0}

        # 2. 增量同步
        for event in changes:
            content = files.get(event.file_path, "")
            self.syncer.handle_change(event, content)

        latency = (time.time() - start) * 1000
        stats = self.syncer.get_stats()

        result = {
            "changes": len(changes),
            "latency_ms": round(latency, 1),
            "stats": stats,
        }
        self.sync_history.append(result)
        return result

    def run_cleanup(self) -> int:
        """清理过期向量"""
        return self.syncer.cleanup_stale()


def demo_full_pipeline():
    """演示完整同步管道"""
    print("=" * 60)
    print("Demo 3: 完整同步管道")
    print("=" * 60)
    print()

    pipeline = KnowledgeSyncPipeline()

    # 第1轮：初始灌入
    print("  第1轮同步（初始灌入3个文档）:")
    files_v1 = {
        "hr/年假制度.md": "工龄5年以下享有5天年假",
        "hr/考勤规则.md": "工作时间9:00-18:00",
        "finance/报销流程.md": "报销需在30天内提交",
    }
    result = pipeline.run_sync(files_v1)
    print(f"    变更数: {result['changes']}, 延迟: {result['latency_ms']}ms")
    print(f"    向量库: {result['stats']}")
    print()

    # 第2轮：修改+新增
    print("  第2轮同步（修改年假制度 + 新增福利手册）:")
    files_v2 = files_v1.copy()
    files_v2["hr/年假制度.md"] = "工龄5年以下享有7天年假（2024年新政策）"
    files_v2["hr/福利手册.md"] = "2024年员工福利包括补充医疗保险"
    result = pipeline.run_sync(files_v2)
    print(f"    变更数: {result['changes']}, 延迟: {result['latency_ms']}ms")
    print(f"    向量库: {result['stats']}")
    print()

    # 第3轮：删除
    print("  第3轮同步（删除报销流程）:")
    files_v3 = {k: v for k, v in files_v2.items() if "报销" not in k}
    result = pipeline.run_sync(files_v3)
    print(f"    变更数: {result['changes']}, 延迟: {result['latency_ms']}ms")
    print(f"    向量库: {result['stats']}")
    print()

    # 清理过期向量
    print("  执行过期清理:")
    cleaned = pipeline.run_cleanup()
    stats = pipeline.syncer.get_stats()
    print(f"    清理后向量库: {stats}")
    print()

    # 检索验证
    print("  检索验证（query: 年假）:")
    results = pipeline.syncer.search("年假天数")
    for r in results:
        print(f"    [v{r['version']} | score: {r['score']}] {r['content'][:50]}...")
    print()


# ============================================================
# 同步策略对比
# ============================================================

def demo_strategy_comparison():
    """对比全量重建 vs 增量同步的性能"""
    print("=" * 60)
    print("Demo 4: 全量重建 vs 增量同步 性能对比")
    print("=" * 60)
    print()

    doc_count = 1000
    changed_count = 50

    # 模拟文档集
    all_docs = {f"doc_{i}.md": f"文档{i}的内容，包含各种知识" for i in range(doc_count)}

    # 全量重建：处理所有文档
    start = time.time()
    full_chunks = 0
    for content in all_docs.values():
        # 模拟分块+Embedding
        chunks = [f"{content}_part{j}" for j in range(3)]
        for chunk in chunks:
            _ = [random.random() for _ in range(4)]  # 模拟Embedding
            full_chunks += 1
    full_latency = (time.time() - start) * 1000

    # 增量同步：只处理变更的文档
    start = time.time()
    incr_chunks = 0
    for i in range(changed_count):
        content = all_docs[f"doc_{i}.md"]
        chunks = [f"{content}_part{j}" for j in range(3)]
        for chunk in chunks:
            _ = [random.random() for _ in range(4)]
            incr_chunks += 1
    incr_latency = (time.time() - start) * 1000

    print(f"  文档总数: {doc_count}, 变更文档数: {changed_count}")
    print()
    print(f"  {'策略':>12s} | {'处理chunk数':>10s} | {'延迟(ms)':>10s} | {'节省'}")
    print(f"  {'-' * 55}")
    print(f"  {'全量重建':>10s} | {full_chunks:>10d} | {full_latency:>10.1f} | -")
    print(f"  {'增量同步':>10s} | {incr_chunks:>10d} | {incr_latency:>10.1f} | "
          f"{(1 - incr_latency / full_latency) * 100:.0f}%")
    print()


# ============================================================
# 主函数
# ============================================================

def main():
    print()
    print("🔄 知识同步管道演示 - CDC + 版本控制")
    print("=" * 60)
    print()

    demo_file_hash_cdc()
    demo_versioned_sync()
    demo_full_pipeline()
    demo_strategy_comparison()

    print("=" * 60)
    print("演示完成！")
    print()
    print("生产环境建议：")
    print("  1. 用Watchdog库监听文件系统事件，替代定时哈希扫描")
    print("  2. 用消息队列（Kafka/Redis Stream）解耦变更检测和同步")
    print("  3. 向量库选择支持metadata过滤的（如Qdrant/Milvus）")
    print("  4. 软删除保留1-7天后再硬删除，支持快速回滚")
    print("  5. 监控同步延迟和失败率，设置告警")
    print()


if __name__ == "__main__":
    main()
