"""
📦 5种省Token的实战技巧 — 完整演示
配套文章：《上下文窗口爆了？这是5种省Token的实战技巧》

演示5种生产级省Token技巧：
1. 摘要压缩
2. 滑动窗口
3. 关键帧提取
4. 检索增强（RAG）
5. 记忆裁剪

运行方式：python token_saving_demo.py
"""

import math
from collections import Counter


# ============================================================
# 工具函数
# ============================================================

def estimate_tokens(text: str) -> int:
    """粗略估算Token数（中文约1.5字/token，英文约4字符/token）"""
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars
    return int(chinese_chars / 1.5 + other_chars / 4)


def mock_llm_call(prompt: str) -> str:
    """模拟LLM调用（实际项目中替换为真实API调用）"""
    if "压缩" in prompt or "摘要" in prompt:
        return "2024年Q3营收12.3亿元，同比增长23.5%。净利润1.8亿元，同比增长15.2%。主要增长来自AI业务线，占总营收35%。"
    if "关键信息" in prompt:
        return ("- 关键点1：用户为企业客户，年消费50万以上\n"
                "- 关键点2：需要批量采购API调用额度\n"
                "- 关键点3：要求99.9%可用性SLA")
    return "这是模拟的LLM回答。"


# ============================================================
# 技巧1：摘要压缩
# ============================================================

class SummaryCompressor:
    """摘要压缩：将长文本压缩为摘要，减少Token消耗"""

    def compress(self, long_text: str, max_summary_tokens: int = 200) -> str:
        prompt = f"""请将以下内容压缩为不超过{max_summary_tokens}字的摘要，
保留所有关键事实、数字和结论，去掉冗余描述。

原文：
{long_text}

摘要："""
        return mock_llm_call(prompt)

    def analyze_with_summary(self, long_document: str, question: str) -> dict:
        summary = self.compress(long_document)
        original_tokens = estimate_tokens(long_document)
        summary_tokens = estimate_tokens(summary)

        prompt = f"""基于以下文档摘要回答问题。

文档摘要：{summary}

问题：{question}
回答："""
        answer = mock_llm_call(prompt)

        return {
            "answer": answer,
            "original_tokens": original_tokens,
            "summary_tokens": summary_tokens,
            "saving_rate": f"{(1 - summary_tokens / original_tokens) * 100:.1f}%",
        }


# ============================================================
# 技巧2：滑动窗口
# ============================================================

class SlidingWindowMemory:
    """滑动窗口：只保留最近N轮对话"""

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.history: list[dict] = []

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.window_size * 2:
            self.history = self.history[-self.window_size * 2:]

    def get_context(self) -> list[dict]:
        return self.history.copy()

    def estimate_tokens(self) -> int:
        return sum(estimate_tokens(msg["content"]) for msg in self.history)

    def get_stats(self) -> dict:
        return {
            "total_turns_added": len(self.history),
            "retained_turns": len(self.history),
            "window_size": self.window_size,
            "estimated_tokens": self.estimate_tokens(),
        }


# ============================================================
# 技巧3：关键帧提取
# ============================================================

class KeyFrameExtractor:
    """关键帧提取：从长文本中提取关键信息点"""

    def extract(self, long_text: str, max_points: int = 10) -> str:
        prompt = f"""从以下内容中提取最多{max_points}个关键信息点。
每个信息点用一句话概括，保留具体数字和关键结论。

格式要求：
- 关键点1：...
- 关键点2：...

原文：
{long_text}

关键信息点："""
        return mock_llm_call(prompt)

    def extract_from_conversation(self, conversation_history: list[dict]) -> str:
        formatted = "\n".join(
            f"{msg['role']}: {msg['content']}" for msg in conversation_history
        )
        prompt = f"""从以下对话历史中提取关键信息：
1. 用户的核心诉求
2. 已确认的事实
3. 待解决的问题
4. 已达成的共识

对话历史：
{formatted}

关键信息："""
        return mock_llm_call(prompt)


# ============================================================
# 技巧4：检索增强（RAG）
# ============================================================

class RetrievalAugmented:
    """检索增强：按需检索相关片段，而非全量塞入上下文"""

    def __init__(self, chunk_size: int = 500, top_k: int = 3):
        self.chunk_size = chunk_size
        self.top_k = top_k
        self.chunks: list[str] = []

    def index_document(self, document: str):
        """将文档分块并建立索引"""
        self.chunks = self._split_into_chunks(document)
        print(f"  已索引 {len(self.chunks)} 个文档片段")

    def query(self, question: str) -> dict:
        """检索最相关的片段并生成回答"""
        top_chunks = self._find_top_k(question)
        context = "\n---\n".join(top_chunks)

        prompt = f"""基于以下参考信息回答问题。只使用提供的信息。

参考信息：
{context}

问题：{question}
回答："""

        total_doc_tokens = sum(estimate_tokens(c) for c in self.chunks)
        used_tokens = estimate_tokens(context)

        return {
            "answer": mock_llm_call(prompt),
            "total_doc_tokens": total_doc_tokens,
            "used_tokens": used_tokens,
            "saving_rate": f"{(1 - used_tokens / max(total_doc_tokens, 1)) * 100:.1f}%",
            "chunks_retrieved": len(top_chunks),
        }

    def _split_into_chunks(self, document: str) -> list[str]:
        words = document.split("。")
        chunks, current = [], ""
        for sentence in words:
            if len(current) + len(sentence) > self.chunk_size:
                if current:
                    chunks.append(current.strip())
                current = sentence
            else:
                current += sentence + "。"
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _find_top_k(self, question: str) -> list[str]:
        """简化的相关性匹配（实际项目中用向量相似度）"""
        scored = []
        q_chars = set(question)
        for chunk in self.chunks:
            overlap = len(q_chars & set(chunk))
            scored.append((overlap, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[: self.top_k]]


# ============================================================
# 技巧5：记忆裁剪
# ============================================================

class MemoryPruner:
    """记忆裁剪：按重要度评分，优先保留关键记忆"""

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens
        self.memories: list[dict] = []

    def add_memory(self, content: str, importance: str = "medium"):
        score_map = {"high": 3, "medium": 2, "low": 1}
        self.memories.append({
            "content": content,
            "importance": score_map.get(importance, 2),
            "timestamp": len(self.memories),
        })

    def get_pruned_context(self) -> list[str]:
        """按重要度+时间衰减排序，裁剪到Token预算内"""
        scored = []
        for mem in self.memories:
            recency = 1.0 / (1 + (len(self.memories) - mem["timestamp"]) * 0.1)
            final_score = mem["importance"] * 0.7 + recency * 0.3
            scored.append((final_score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)

        result, total_tokens = [], 0
        for score, mem in scored:
            tokens = estimate_tokens(mem["content"])
            if total_tokens + tokens > self.max_tokens:
                break
            result.append(mem["content"])
            total_tokens += tokens
        return result

    def get_stats(self) -> dict:
        pruned = self.get_pruned_context()
        total_tokens = sum(estimate_tokens(m["content"]) for m in self.memories)
        pruned_tokens = sum(estimate_tokens(c) for c in pruned)
        return {
            "total_memories": len(self.memories),
            "retained_memories": len(pruned),
            "total_tokens": total_tokens,
            "pruned_tokens": pruned_tokens,
            "saving_rate": f"{(1 - pruned_tokens / max(total_tokens, 1)) * 100:.1f}%",
        }


# ============================================================
# 演示主流程
# ============================================================

def demo_summary_compressor():
    print("=" * 60)
    print("技巧1：摘要压缩")
    print("=" * 60)

    long_report = (
        "2024年第三季度财务报告摘要：本季度公司实现营业收入12.3亿元人民币，"
        "较去年同期增长23.5%。其中，AI业务线贡献营收4.3亿元，占总营收35%，"
        "同比增长67.8%。传统业务营收8.0亿元，同比增长5.2%。净利润1.8亿元，"
        "同比增长15.2%。研发投入2.1亿元，占营收17.1%。员工总数增至3200人，"
        "其中AI相关岗位占比从去年的15%提升至28%。公司在本季度完成了三个重要"
        "里程碑：一是AI客服系统日均处理量突破50万次；二是大模型推理成本降低40%；"
        "三是获得ISO 27001信息安全认证。展望下一季度，公司预计营收将达到13-14亿元，"
        "AI业务占比有望突破40%。"
    )

    compressor = SummaryCompressor()
    result = compressor.analyze_with_summary(long_report, "AI业务的增长情况如何？")

    print(f"  原文Token数：{result['original_tokens']}")
    print(f"  摘要Token数：{result['summary_tokens']}")
    print(f"  节省率：{result['saving_rate']}")
    print(f"  回答：{result['answer']}")
    print()


def demo_sliding_window():
    print("=" * 60)
    print("技巧2：滑动窗口")
    print("=" * 60)

    memory = SlidingWindowMemory(window_size=5)

    conversations = [
        ("user", "我是企业客户，年消费50万以上"),
        ("assistant", "好的，已为您标记为VIP企业客户"),
        ("user", "我想了解API批量采购方案"),
        ("assistant", "我们提供三种批量方案：基础版、专业版、旗舰版"),
        ("user", "专业版的价格是多少？"),
        ("assistant", "专业版月费8万元，包含500万次API调用"),
        ("user", "有没有年付优惠？"),
        ("assistant", "年付可享8折优惠，即76.8万/年"),
        ("user", "SLA保障是多少？"),
        ("assistant", "专业版SLA为99.9%，旗舰版为99.99%"),
        ("user", "我需要99.99%的SLA"),
        ("assistant", "那建议您选择旗舰版，月费12万元"),
    ]

    all_tokens = sum(estimate_tokens(content) for _, content in conversations)
    for role, content in conversations:
        memory.add_turn(role, content)

    stats = memory.get_stats()
    print(f"  总对话轮数：{len(conversations)}")
    print(f"  保留轮数：{stats['retained_turns']}")
    print(f"  全量Token：{all_tokens}")
    print(f"  窗口Token：{stats['estimated_tokens']}")
    print(f"  节省率：{(1 - stats['estimated_tokens'] / all_tokens) * 100:.1f}%")
    print()


def demo_key_frame_extractor():
    print("=" * 60)
    print("技巧3：关键帧提取")
    print("=" * 60)

    conversation = [
        {"role": "user", "content": "我是企业客户，年消费50万以上，需要批量采购API调用额度"},
        {"role": "assistant", "content": "好的，我们有三种方案供您选择"},
        {"role": "user", "content": "我需要99.9%以上的SLA保障"},
        {"role": "assistant", "content": "专业版提供99.9%SLA，旗舰版提供99.99%SLA"},
        {"role": "user", "content": "价格分别是多少？"},
        {"role": "assistant", "content": "专业版月费8万，旗舰版月费12万"},
    ]

    extractor = KeyFrameExtractor()
    key_frames = extractor.extract_from_conversation(conversation)

    original_tokens = sum(estimate_tokens(m["content"]) for m in conversation)
    frame_tokens = estimate_tokens(key_frames)

    print(f"  原始对话Token：{original_tokens}")
    print(f"  关键帧Token：{frame_tokens}")
    print(f"  节省率：{(1 - frame_tokens / original_tokens) * 100:.1f}%")
    print(f"  提取结果：\n{key_frames}")
    print()


def demo_retrieval_augmented():
    print("=" * 60)
    print("技巧4：检索增强（RAG）")
    print("=" * 60)

    knowledge_base = (
        "API定价方案：基础版月费2万元，包含100万次调用。专业版月费8万元，包含500万次调用。"
        "旗舰版月费12万元，包含无限次调用。所有方案均支持年付8折优惠。"
        "SLA保障：基础版99%可用性。专业版99.9%可用性。旗舰版99.99%可用性。"
        "超出调用次数后按0.01元/次计费。"
        "技术支持：基础版提供工单支持。专业版提供电话+工单支持。旗舰版提供专属技术经理。"
        "数据安全：所有方案均支持数据加密传输。专业版及以上支持私有化部署。"
        "旗舰版支持独立集群部署和自定义安全策略。"
        "合同条款：最低签约周期为1个月。年付合同提前终止需支付剩余月份30%的违约金。"
        "企业客户可申请定制合同条款。"
    )

    rag = RetrievalAugmented(chunk_size=100, top_k=2)
    rag.index_document(knowledge_base)
    result = rag.query("旗舰版的SLA是多少？")

    print(f"  文档总Token：{result['total_doc_tokens']}")
    print(f"  检索使用Token：{result['used_tokens']}")
    print(f"  节省率：{result['saving_rate']}")
    print(f"  检索片段数：{result['chunks_retrieved']}")
    print()


def demo_memory_pruner():
    print("=" * 60)
    print("技巧5：记忆裁剪")
    print("=" * 60)

    pruner = MemoryPruner(max_tokens=150)

    pruner.add_memory("用户是企业客户，年消费50万以上", importance="high")
    pruner.add_memory("用户询问了天气情况", importance="low")
    pruner.add_memory("用户需要99.99%的SLA保障", importance="high")
    pruner.add_memory("用户提到喜欢蓝色的界面主题", importance="low")
    pruner.add_memory("用户选择了旗舰版方案，月费12万", importance="high")
    pruner.add_memory("用户问了一个关于周末活动的闲聊", importance="low")
    pruner.add_memory("用户要求年付合同，预计总费用115.2万", importance="high")
    pruner.add_memory("系统推荐了相关的技术文档链接", importance="medium")

    stats = pruner.get_stats()
    pruned_context = pruner.get_pruned_context()

    print(f"  总记忆条数：{stats['total_memories']}")
    print(f"  保留条数：{stats['retained_memories']}")
    print(f"  总Token：{stats['total_tokens']}")
    print(f"  裁剪后Token：{stats['pruned_tokens']}")
    print(f"  节省率：{stats['saving_rate']}")
    print(f"  保留的记忆：")
    for mem in pruned_context:
        print(f"    - {mem}")
    print()


def print_comparison_table():
    print("=" * 60)
    print("效果对比总结")
    print("=" * 60)
    print()
    print(f"{'技巧':<16} {'Token节省率':<14} {'信息保留度':<12} {'实现复杂度':<12} {'适用场景'}")
    print("-" * 76)
    rows = [
        ("摘要压缩", "60-80%", "中", "低", "长文档处理"),
        ("滑动窗口", "50-70%", "低", "低", "多轮对话"),
        ("关键帧提取", "70-85%", "高", "中", "会议记录/日志"),
        ("检索增强(RAG)", "80-95%", "高", "高", "知识库问答"),
        ("记忆裁剪", "60-75%", "中高", "中", "Agent长任务"),
    ]
    for name, saving, retention, complexity, scenario in rows:
        print(f"  {name:<14} {saving:<12} {retention:<10} {complexity:<10} {scenario}")
    print()


if __name__ == "__main__":
    print()
    print("📦 5种省Token的实战技巧 — 完整演示")
    print("=" * 60)
    print()

    demo_summary_compressor()
    demo_sliding_window()
    demo_key_frame_extractor()
    demo_retrieval_augmented()
    demo_memory_pruner()
    print_comparison_table()

    print("✅ 演示完成！建议根据实际场景组合使用多种技巧。")
