"""
AI Gateway对比演示：LiteLLM / 自研 / 云厂商
模拟三种Gateway方案的核心能力差异
"""

from dataclasses import dataclass, field


# ============================================================
# 数据结构
# ============================================================
@dataclass
class ModelConfig:
    name: str
    provider: str
    cost_per_1k_input: float
    cost_per_1k_output: float
    max_rpm: int = 60
    available: bool = True


# ============================================================
# LiteLLM风格：统一API代理
# ============================================================
class LiteLLMStyleProxy:
    """模拟LiteLLM的统一代理 + 自动Fallback"""

    def __init__(self):
        self.models: dict[str, ModelConfig] = {}
        self.fallback_order: list[str] = []
        self.usage_log: list[dict] = []

    def register_model(self, config: ModelConfig):
        self.models[config.name] = config

    def set_fallback(self, order: list[str]):
        self.fallback_order = order

    def completion(self, model: str, messages: list[dict]) -> dict:
        models_to_try = [model] + [m for m in self.fallback_order if m != model]
        for m in models_to_try:
            cfg = self.models.get(m)
            if not cfg or not cfg.available:
                continue
            result = self._call(cfg, messages)
            self._log(cfg, result)
            return result
        return {"error": "所有模型均不可用"}

    def _call(self, cfg: ModelConfig, messages: list[dict]) -> dict:
        input_tokens = sum(len(m.get("content", "")) for m in messages)
        return {
            "model": cfg.name,
            "provider": cfg.provider,
            "content": f"[{cfg.provider}] Response from {cfg.name}",
            "usage": {"input_tokens": input_tokens, "output_tokens": 80},
        }

    def _log(self, cfg: ModelConfig, result: dict):
        u = result.get("usage", {})
        cost = (u.get("input_tokens", 0) * cfg.cost_per_1k_input +
                u.get("output_tokens", 0) * cfg.cost_per_1k_output) / 1000
        self.usage_log.append({"model": cfg.name, "cost": round(cost, 6)})

    def total_cost(self) -> float:
        return round(sum(l["cost"] for l in self.usage_log), 4)


# ============================================================
# 自研Gateway：路由 + 限流 + 缓存
# ============================================================
class CustomGateway:
    """自研Gateway：完全可控"""

    def __init__(self):
        self.routes: dict[str, list[ModelConfig]] = {}
        self.rate_counter: dict[str, int] = {}
        self.cache: dict[str, dict] = {}
        self.usage_log: list[dict] = []

    def add_route(self, scene: str, models: list[ModelConfig]):
        self.routes[scene] = models

    def request(self, scene: str, messages: list[dict], user_id: str = "anon") -> dict:
        # 限流
        count = self.rate_counter.get(user_id, 0)
        if count >= 100:
            return {"error": "请求频率超限", "cached": False}
        self.rate_counter[user_id] = count + 1

        # 缓存
        cache_key = f"{scene}:{messages[-1].get('content', '')}" if messages else scene
        if cache_key in self.cache:
            return {**self.cache[cache_key], "cached": True}

        # 路由
        models = self.routes.get(scene, [])
        for cfg in models:
            if not cfg.available:
                continue
            result = {
                "model": cfg.name,
                "content": f"[自研Gateway] {cfg.name} 响应",
                "cached": False,
            }
            self.cache[cache_key] = result
            self.usage_log.append({"model": cfg.name, "scene": scene})
            return result
        return {"error": f"场景 {scene} 无可用模型", "cached": False}

    def stats(self) -> dict:
        return {
            "total_requests": len(self.usage_log),
            "cache_size": len(self.cache),
            "rate_limits": dict(self.rate_counter),
        }


# ============================================================
# 云厂商风格：托管服务
# ============================================================
class CloudGateway:
    """云厂商托管Gateway（简化模拟）"""

    def __init__(self, provider: str):
        self.provider = provider
        self.models: list[str] = []
        self.call_count = 0

    def add_model(self, model: str):
        self.models.append(model)

    def invoke(self, model: str, prompt: str) -> dict:
        if model not in self.models:
            return {"error": f"模型 {model} 不在 {self.provider} 平台内"}
        self.call_count += 1
        return {
            "model": model,
            "provider": self.provider,
            "content": f"[{self.provider}] {model} 响应",
        }


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("AI Gateway对比演示")
    print("=" * 60)

    messages = [{"role": "user", "content": "什么是RAG架构？"}]

    # --- LiteLLM风格 ---
    print("\n--- LiteLLM风格（统一代理） ---")
    proxy = LiteLLMStyleProxy()
    proxy.register_model(ModelConfig("gpt-4o", "OpenAI", 0.005, 0.015))
    proxy.register_model(ModelConfig("claude-3-sonnet", "Anthropic", 0.003, 0.015))
    proxy.register_model(ModelConfig("gemini-pro", "Google", 0.001, 0.002))
    proxy.set_fallback(["gpt-4o", "claude-3-sonnet", "gemini-pro"])

    result = proxy.completion("gpt-4o", messages)
    print(f"  正常请求: {result['content']}")

    # 模拟主模型不可用
    proxy.models["gpt-4o"].available = False
    result = proxy.completion("gpt-4o", messages)
    print(f"  Fallback:  {result['content']}")
    print(f"  累计成本:  ${proxy.total_cost()}")

    # --- 自研Gateway ---
    print("\n--- 自研Gateway（路由+限流+缓存） ---")
    gw = CustomGateway()
    gw.add_route("qa", [ModelConfig("gpt-4o", "OpenAI", 0.005, 0.015)])
    gw.add_route("summary", [ModelConfig("gpt-4o-mini", "OpenAI", 0.0002, 0.0006)])

    r1 = gw.request("qa", messages, user_id="user_1")
    print(f"  首次请求: {r1['content']}  cached={r1['cached']}")
    r2 = gw.request("qa", messages, user_id="user_1")
    print(f"  缓存命中: {r2['content']}  cached={r2['cached']}")
    print(f"  统计: {gw.stats()}")

    # --- 云厂商风格 ---
    print("\n--- 云厂商风格（托管服务） ---")
    cloud = CloudGateway("AWS Bedrock")
    cloud.add_model("claude-3-sonnet")
    cloud.add_model("titan-embed")

    r = cloud.invoke("claude-3-sonnet", "什么是RAG？")
    print(f"  平台内模型: {r['content']}")
    r = cloud.invoke("gpt-4o", "什么是RAG？")
    print(f"  平台外模型: {r.get('error', r.get('content'))}")

    # 对比总结
    print("\n" + "=" * 60)
    print("选型建议")
    print("=" * 60)
    rows = [
        ("LiteLLM", "开箱即用", "100+模型", "中小团队"),
        ("自研Gateway", "完全可控", "按需接入", "大团队/复杂需求"),
        ("云厂商", "零运维", "平台内", "云原生团队"),
    ]
    print(f"{'方案':<16} {'特点':<12} {'模型覆盖':<12} {'适合团队'}")
    print("-" * 55)
    for name, feat, cov, team in rows:
        print(f"{name:<16} {feat:<12} {cov:<12} {team}")


if __name__ == "__main__":
    main()
