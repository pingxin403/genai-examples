"""
AI应用四层架构演示
对应文章：🧭《一张图看懂AI应用架构：从用户请求到大模型》

演示应用层/编排层/模型层/基础设施层的职责划分与交互流程。
使用模拟数据，无需API Key即可运行。
"""

import time
from datetime import datetime


# ============================================================
# 基础设施层 (Infrastructure Layer)
# 职责：数据存储、缓存、监控、日志
# ============================================================

class VectorStore:
    """基础设施层：向量数据库（简化模拟）"""

    def __init__(self):
        self.documents = {
            "退货流程": "用户申请退货后，需在7天内将商品寄回原仓库，仓库验收通过后3个工作日内退款到原支付账户。",
            "换货流程": "用户可在收货15天内申请换货，需保持商品及包装完好，运费由平台承担。",
            "投诉渠道": "可通过400-888-0000热线或在线客服提交投诉，承诺24小时内首次响应。",
            "会员权益": "金卡会员享受免运费、优先客服、专属折扣三项权益，年消费满5000元自动升级。",
            "配送时效": "标准配送3-5个工作日，加急配送1-2个工作日（部分偏远地区除外）。",
        }

    def search(self, query, top_k=2):
        """模拟向量相似度检索"""
        results = []
        for title, content in self.documents.items():
            # 简化：用关键词匹配模拟向量相似度
            score = sum(1 for char in query if char in title) / max(len(title), 1)
            if score > 0.1:
                results.append({"title": title, "content": content, "score": round(score, 3)})

        results.sort(key=lambda x: x["score"], reverse=True)
        if not results:
            results = [{"title": "通用回复", "content": "请联系人工客服获取帮助。", "score": 0.1}]
        return results[:top_k]


class MetricsCollector:
    """基础设施层：监控指标收集"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "avg_latency_ms": 0.0,
            "requests_log": [],
        }

    def record_request(self, tokens_used, cost, latency_ms):
        self.metrics["total_requests"] += 1
        self.metrics["total_tokens"] += tokens_used
        self.metrics["total_cost"] += cost
        # 滚动平均延迟
        n = self.metrics["total_requests"]
        self.metrics["avg_latency_ms"] = (
            self.metrics["avg_latency_ms"] * (n - 1) + latency_ms
        ) / n
        self.metrics["requests_log"].append({
            "timestamp": datetime.now().isoformat(),
            "tokens": tokens_used,
            "cost": cost,
            "latency_ms": latency_ms,
        })

    def get_summary(self):
        return {
            "总请求数": self.metrics["total_requests"],
            "总Token消耗": self.metrics["total_tokens"],
            "总成本(USD)": round(self.metrics["total_cost"], 6),
            "平均延迟(ms)": round(self.metrics["avg_latency_ms"], 1),
        }


class AuditLogger:
    """基础设施层：审计日志"""

    def __init__(self):
        self.logs = []

    def log(self, user_id, action, detail):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "detail": detail,
        }
        self.logs.append(entry)
        print(f"  [审计] {action}: {detail[:60]}...")

    def get_logs(self):
        return self.logs


# ============================================================
# 模型层 (Model Layer)
# 职责：LLM推理、Embedding生成、模型路由与降级
# ============================================================

class LLMService:
    """模型层：LLM推理服务（模拟）"""

    def __init__(self, model_name="gpt-4o-mini", timeout=5):
        self.model_name = model_name
        self.timeout = timeout
        self.price_per_1k_input = 0.00015
        self.price_per_1k_output = 0.0006

    def generate(self, prompt, max_tokens=500):
        """模拟LLM推理调用"""
        start = time.time()

        # 模拟推理延迟
        time.sleep(0.05)

        # 模拟生成回答（生产环境替换为真实API调用）
        simulated_output = (
            "根据知识库信息，为您解答如下：\n"
            "退货流程分为三步：1）在订单页面点击申请退货；"
            "2）在7天内将商品寄回指定仓库；"
            "3）仓库验收通过后，3个工作日内退款到原支付账户。\n"
            "如有其他问题，请随时咨询。"
        )

        input_tokens = len(prompt) // 4  # 粗略估算
        output_tokens = len(simulated_output) // 4
        cost = (
            input_tokens * self.price_per_1k_input / 1000
            + output_tokens * self.price_per_1k_output / 1000
        )
        latency_ms = (time.time() - start) * 1000

        return {
            "content": simulated_output,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": round(cost, 6),
            "model": self.model_name,
            "latency_ms": round(latency_ms, 1),
        }


class ModelRouter:
    """模型层：模型路由与降级"""

    def __init__(self):
        self.primary = LLMService(model_name="gpt-4o", timeout=5)
        self.fallback = LLMService(model_name="gpt-4o-mini", timeout=3)

    def generate(self, prompt, max_tokens=500):
        """先尝试主模型，失败则降级到备用模型"""
        try:
            result = self.primary.generate(prompt, max_tokens)
            result["routed_to"] = "primary"
            return result
        except Exception as e:
            print(f"  [模型层] 主模型失败({e})，降级到备用模型")
            result = self.fallback.generate(prompt, max_tokens)
            result["routed_to"] = "fallback"
            return result


# ============================================================
# 编排层 (Orchestration Layer)
# 职责：Prompt组装、RAG检索编排、输出校验、Token预算
# ============================================================

class OrchestrationLayer:
    """编排层：核心业务逻辑编排"""

    SYSTEM_PROMPT = (
        "你是一个专业的电商客服助手。请严格根据提供的知识库内容回答用户问题。"
        "如果知识库中没有相关信息，请诚实告知用户并建议联系人工客服。"
        "回答要简洁、准确、友好，不要推荐其他商品。"
    )

    def __init__(self, model_router, vector_store, metrics, audit_logger):
        self.model_router = model_router
        self.vector_store = vector_store
        self.metrics = metrics
        self.audit_logger = audit_logger
        self.token_budget = 2000
        self.blocked_words = ["竞品推荐", "购买链接", "加微信"]

    def process(self, user_query, user_id="anonymous", user_context=None):
        """编排完整的请求处理流程"""
        print(f"\n  [编排层] 开始处理: '{user_query}'")

        # Step 1: RAG检索
        print("  [编排层] Step 1 - RAG检索...")
        retrieved_docs = self.vector_store.search(user_query)
        context_text = "\n".join(
            [f"- {doc['title']}: {doc['content']}" for doc in retrieved_docs]
        )
        print(f"  [编排层] 检索到 {len(retrieved_docs)} 条相关文档")

        # Step 2: Prompt组装
        print("  [编排层] Step 2 - Prompt组装...")
        prompt = self._build_prompt(user_query, context_text, user_context)

        # Step 3: Token预算检查
        estimated_tokens = len(prompt) // 4
        print(f"  [编排层] Step 3 - Token预算检查: 预估{estimated_tokens}/{self.token_budget}")
        if estimated_tokens > self.token_budget:
            self.audit_logger.log(user_id, "REJECTED", f"Token超预算: {estimated_tokens}")
            return {"content": "问题过长，请精简后重试。", "status": "rejected"}

        # Step 4: 调用模型（通过模型路由）
        print("  [编排层] Step 4 - 调用模型...")
        result = self.model_router.generate(prompt)
        print(f"  [编排层] 模型返回: {result['total_tokens']} tokens, "
              f"${result['cost']}, {result['latency_ms']}ms")

        # Step 5: 输出校验
        print("  [编排层] Step 5 - 输出校验...")
        validated_content = self._validate_output(result["content"])

        # Step 6: 记录指标和审计
        self.metrics.record_request(result["total_tokens"], result["cost"], result["latency_ms"])
        self.audit_logger.log(user_id, "QUERY", f"Q: {user_query[:50]}")

        return {
            "content": validated_content,
            "sources": [doc["title"] for doc in retrieved_docs],
            "tokens_used": result["total_tokens"],
            "cost": result["cost"],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "status": "success",
        }

    def _build_prompt(self, query, context, user_context=None):
        user_info = f"\n用户上下文：{user_context}" if user_context else ""
        return f"""系统提示：{self.SYSTEM_PROMPT}
{user_info}
知识库检索结果：
{context}

用户问题：{query}

请根据知识库内容回答："""

    def _validate_output(self, content):
        for word in self.blocked_words:
            if word in content:
                content = content.replace(word, "[已过滤]")
                print(f"  [编排层] 过滤敏感词: {word}")
        return content


# ============================================================
# 应用层 (Application Layer)
# 职责：用户交互、认证鉴权、会话管理、请求路由
# ============================================================

class ApplicationLayer:
    """应用层：请求入口"""

    def __init__(self, orchestration):
        self.orchestration = orchestration
        self.sessions = {}
        self.valid_users = {"user_001", "user_002", "user_003"}

    def handle_request(self, user_id, message):
        """处理用户请求"""
        print(f"\n{'='*60}")
        print(f"[应用层] 收到请求 - 用户: {user_id}")

        # Step 1: 认证
        if user_id not in self.valid_users:
            print(f"[应用层] 认证失败: {user_id}")
            return {"error": "未认证用户", "status": 401}
        print(f"[应用层] 认证通过")

        # Step 2: 会话管理
        if user_id not in self.sessions:
            self.sessions[user_id] = {"history": [], "created_at": datetime.now().isoformat()}
        session = self.sessions[user_id]
        print(f"[应用层] 会话历史: {len(session['history'])}轮对话")

        # Step 3: 调用编排层
        result = self.orchestration.process(
            user_query=message,
            user_id=user_id,
            user_context=f"历史对话{len(session['history'])}轮",
        )

        # Step 4: 更新会话
        if result.get("status") == "success":
            session["history"].append({
                "user": message,
                "assistant": result["content"][:100],
            })

        print(f"\n[应用层] 请求完成 - 状态: {result.get('status', 'unknown')}")
        return result


# ============================================================
# 主程序：组装四层并运行演示
# ============================================================

def main():
    print("=" * 60)
    print("🧭 AI应用四层架构演示")
    print("=" * 60)

    # --- 初始化四层 ---
    # 基础设施层
    vector_store = VectorStore()
    metrics = MetricsCollector()
    audit_logger = AuditLogger()

    # 模型层
    model_router = ModelRouter()

    # 编排层
    orchestration = OrchestrationLayer(
        model_router=model_router,
        vector_store=vector_store,
        metrics=metrics,
        audit_logger=audit_logger,
    )

    # 应用层
    app = ApplicationLayer(orchestration)

    # --- 模拟用户请求 ---
    test_cases = [
        ("user_001", "退货流程怎么走？"),
        ("user_001", "换货需要什么条件？"),
        ("user_002", "你们的配送要多久？"),
        ("invalid_user", "这个用户没有权限"),  # 认证失败测试
    ]

    results = []
    for user_id, message in test_cases:
        result = app.handle_request(user_id, message)
        results.append((user_id, message, result))

    # --- 输出汇总 ---
    print("\n" + "=" * 60)
    print("📊 请求结果汇总")
    print("=" * 60)

    for user_id, message, result in results:
        status = result.get("status", result.get("error", "unknown"))
        print(f"\n  用户: {user_id}")
        print(f"  问题: {message}")
        print(f"  状态: {status}")
        if "content" in result:
            print(f"  回答: {result['content'][:80]}...")
        if "sources" in result:
            print(f"  来源: {result['sources']}")
        if "tokens_used" in result:
            print(f"  Token: {result['tokens_used']}, 成本: ${result['cost']}")

    # --- 系统指标 ---
    print("\n" + "=" * 60)
    print("📈 系统指标汇总")
    print("=" * 60)
    summary = metrics.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # --- 审计日志 ---
    print(f"\n  审计日志条数: {len(audit_logger.get_logs())}")

    print("\n" + "=" * 60)
    print("✅ 演示完成！四层架构各司其职，请求链路清晰可追踪。")
    print("=" * 60)


if __name__ == "__main__":
    main()
