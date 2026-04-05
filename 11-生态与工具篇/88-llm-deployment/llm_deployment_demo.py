"""
LLM部署方案对比演示：vLLM / TGI / TensorRT-LLM / Ollama
模拟四种推理引擎的核心特性与性能差异
"""

import random
import time
from dataclasses import dataclass


# ============================================================
# 数据结构
# ============================================================
@dataclass
class InferenceRequest:
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7


@dataclass
class InferenceResult:
    engine: str
    tokens_generated: int
    time_to_first_token_ms: float
    total_time_ms: float
    tokens_per_second: float


# ============================================================
# 推理引擎基类
# ============================================================
class LLMEngine:
    def __init__(self, name: str, base_ttft_ms: float, base_tps: float):
        self.name = name
        self.base_ttft_ms = base_ttft_ms
        self.base_tps = base_tps

    def infer(self, request: InferenceRequest) -> InferenceResult:
        jitter = random.uniform(-0.1, 0.1)
        ttft = self.base_ttft_ms * (1 + jitter)
        tps = self.base_tps * (1 + jitter)
        gen_time_ms = request.max_tokens / tps * 1000
        return InferenceResult(
            engine=self.name,
            tokens_generated=request.max_tokens,
            time_to_first_token_ms=round(ttft, 2),
            total_time_ms=round(ttft + gen_time_ms, 2),
            tokens_per_second=round(tps, 1),
        )


class VLLMEngine(LLMEngine):
    """vLLM: PagedAttention + Continuous Batching"""
    def __init__(self):
        super().__init__("vLLM", base_ttft_ms=50, base_tps=80)
        self.paged_attention = True
        self.continuous_batching = True


class TGIEngine(LLMEngine):
    """TGI: Flash Attention + Token Streaming"""
    def __init__(self):
        super().__init__("TGI", base_ttft_ms=60, base_tps=70)
        self.flash_attention = True


class TensorRTEngine(LLMEngine):
    """TensorRT-LLM: Kernel Fusion + In-flight Batching"""
    def __init__(self):
        super().__init__("TensorRT-LLM", base_ttft_ms=30, base_tps=100)
        self.kernel_fusion = True


class OllamaEngine(LLMEngine):
    """Ollama: llama.cpp 本地推理"""
    def __init__(self):
        super().__init__("Ollama", base_ttft_ms=200, base_tps=30)
        self.cpu_support = True


# ============================================================
# Benchmark
# ============================================================
def run_benchmark(engines: list[LLMEngine], num_requests: int = 50):
    request = InferenceRequest(prompt="解释什么是RAG架构", max_tokens=100)
    results: dict[str, dict] = {}

    for engine in engines:
        runs = [engine.infer(request) for _ in range(num_requests)]
        avg_ttft = sum(r.time_to_first_token_ms for r in runs) / len(runs)
        avg_tps = sum(r.tokens_per_second for r in runs) / len(runs)
        avg_total = sum(r.total_time_ms for r in runs) / len(runs)
        results[engine.name] = {
            "avg_ttft_ms": round(avg_ttft, 1),
            "avg_tps": round(avg_tps, 1),
            "avg_total_ms": round(avg_total, 1),
        }
    return results


# ============================================================
# 主函数
# ============================================================
def main():
    print("=" * 60)
    print("LLM推理引擎性能对比演示")
    print("=" * 60)

    engines = [VLLMEngine(), TGIEngine(), TensorRTEngine(), OllamaEngine()]

    # 单次推理演示
    req = InferenceRequest(prompt="什么是向量数据库？", max_tokens=100)
    print("\n--- 单次推理 ---")
    for engine in engines:
        r = engine.infer(req)
        print(f"  {r.engine:<16} TTFT={r.time_to_first_token_ms:>7.1f}ms  "
              f"TPS={r.tokens_per_second:>6.1f}  Total={r.total_time_ms:>8.1f}ms")

    # Benchmark
    print("\n--- Benchmark (50次平均) ---")
    bench = run_benchmark(engines, num_requests=50)
    print(f"{'引擎':<16} {'TTFT(ms)':<12} {'TPS':<10} {'总延迟(ms)'}")
    print("-" * 50)
    for name, m in bench.items():
        print(f"{name:<16} {m['avg_ttft_ms']:<12} {m['avg_tps']:<10} {m['avg_total_ms']}")

    # 选型建议
    print("\n" + "=" * 60)
    print("选型建议")
    print("=" * 60)
    tips = [
        ("本地开发/测试", "Ollama", "零配置，CPU即可运行"),
        ("生产环境首选", "vLLM", "性能与易用性平衡"),
        ("极致延迟场景", "TensorRT-LLM", "NVIDIA GPU深度优化"),
        ("HuggingFace生态", "TGI", "与HF Hub无缝集成"),
    ]
    for scene, engine, reason in tips:
        print(f"  {scene:<16} → {engine:<16} {reason}")


if __name__ == "__main__":
    main()
