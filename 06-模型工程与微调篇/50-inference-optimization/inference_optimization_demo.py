"""
推理优化演示
对应文章：50-推理优化首Token时间吞吐量延迟怎么平衡
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class InferenceConfig:
    """推理优化配置"""
    name: str = ""
    quantization: str = "fp16"
    max_batch_size: int = 32
    kv_cache_enabled: bool = True
    continuous_batching: bool = True
    speculative_decoding: bool = False
    gpu_memory_utilization: float = 0.9


class InferenceOptimizer:
    """推理优化分析器"""

    BASE_TTFT_MS = 500
    BASE_TPOT_MS = 30
    BASE_THROUGHPUT = 8

    def analyze(self, config: InferenceConfig) -> dict:
        ttft = self._estimate_ttft(config)
        tpot = self._estimate_tpot(config)
        throughput = self._estimate_throughput(config)
        memory_gb = self._estimate_memory(config)

        return {
            "name": config.name,
            "ttft_ms": round(ttft),
            "tpot_ms": round(tpot, 1),
            "throughput_rps": round(throughput, 1),
            "memory_gb": round(memory_gb, 1),
            "tradeoffs": self._analyze_tradeoffs(config),
        }

    def _estimate_ttft(self, config: InferenceConfig) -> float:
        ttft = self.BASE_TTFT_MS
        quant_factor = {"fp16": 1.0, "int8": 0.7, "int4": 0.5}
        ttft *= quant_factor.get(config.quantization, 1.0)
        if config.continuous_batching:
            ttft *= 1.1
        else:
            ttft *= (1 + config.max_batch_size * 0.02)
        if config.speculative_decoding:
            ttft *= 0.6
        return ttft

    def _estimate_tpot(self, config: InferenceConfig) -> float:
        tpot = self.BASE_TPOT_MS
        quant_factor = {"fp16": 1.0, "int8": 0.65, "int4": 0.45}
        tpot *= quant_factor.get(config.quantization, 1.0)
        if config.speculative_decoding:
            tpot *= 0.4
        return tpot

    def _estimate_throughput(self, config: InferenceConfig) -> float:
        tp = self.BASE_THROUGHPUT
        if config.continuous_batching:
            tp *= 3.5
        else:
            tp *= min(config.max_batch_size, 8) * 0.8
        quant_factor = {"fp16": 1.0, "int8": 1.5, "int4": 2.0}
        tp *= quant_factor.get(config.quantization, 1.0)
        if config.kv_cache_enabled:
            tp *= 1.3
        return tp

    def _estimate_memory(self, config: InferenceConfig) -> float:
        base = 14.0
        mem_factor = {"fp16": 1.0, "int8": 0.55, "int4": 0.3}
        model_mem = base * mem_factor.get(config.quantization, 1.0)
        kv_mem = 2.0 if config.kv_cache_enabled else 0.5
        spec_mem = 1.5 if config.speculative_decoding else 0
        return model_mem + kv_mem + spec_mem

    def _analyze_tradeoffs(self, config: InferenceConfig) -> list[str]:
        notes = []
        if config.quantization == "int4":
            notes.append("INT4量化可能导致1-3%精度下降")
        if config.max_batch_size > 32:
            notes.append("大batch增加单请求延迟")
        if config.speculative_decoding:
            notes.append("需要额外小模型显存")
        if not config.kv_cache_enabled:
            notes.append("关闭KV Cache显著降低吞吐量")
        return notes


def recommend_config(scenario: str) -> InferenceConfig:
    """根据场景推荐配置"""
    presets = {
        "chat": InferenceConfig(
            name="聊天场景(低TTFT优先)",
            quantization="int8",
            continuous_batching=True,
            speculative_decoding=True,
        ),
        "batch": InferenceConfig(
            name="批处理场景(高吞吐优先)",
            quantization="int4",
            max_batch_size=64,
            continuous_batching=True,
        ),
        "precision": InferenceConfig(
            name="高精度场景(质量优先)",
            quantization="fp16",
            continuous_batching=True,
            max_batch_size=16,
        ),
    }
    return presets.get(scenario, presets["chat"])


if __name__ == "__main__":
    optimizer = InferenceOptimizer()

    # 对比不同配置
    configs = [
        InferenceConfig(name="基线(FP16无优化)",
                        quantization="fp16",
                        continuous_batching=False,
                        kv_cache_enabled=False),
        InferenceConfig(name="FP16+连续批处理",
                        quantization="fp16",
                        continuous_batching=True),
        InferenceConfig(name="INT8+连续批处理",
                        quantization="int8",
                        continuous_batching=True),
        InferenceConfig(name="INT4+连续批处理+KV Cache",
                        quantization="int4",
                        continuous_batching=True),
        InferenceConfig(name="INT4+投机解码",
                        quantization="int4",
                        continuous_batching=True,
                        speculative_decoding=True),
    ]

    print("=== 推理优化方案对比 ===\n")
    print(f"{'配置':<30} {'TTFT':>8} {'TPOT':>8} {'吞吐量':>10} {'显存':>8}")
    print("-" * 70)

    for config in configs:
        result = optimizer.analyze(config)
        print(f"{result['name']:<28} "
              f"{result['ttft_ms']:>6}ms "
              f"{result['tpot_ms']:>6}ms "
              f"{result['throughput_rps']:>8} rps "
              f"{result['memory_gb']:>6}GB")
        if result["tradeoffs"]:
            for note in result["tradeoffs"]:
                print(f"  ⚠️  {note}")

    # 场景推荐
    print("\n=== 场景推荐 ===")
    for scenario in ["chat", "batch", "precision"]:
        config = recommend_config(scenario)
        result = optimizer.analyze(config)
        print(f"\n{result['name']}:")
        print(f"  TTFT={result['ttft_ms']}ms, "
              f"吞吐={result['throughput_rps']} rps, "
              f"显存={result['memory_gb']}GB")
