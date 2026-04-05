"""
模型运维部署对比演示
对应文章：52-模型运维vLLM-TGI-TensorRT-LLM部署对比
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class DeploymentScenario:
    """部署场景"""
    name: str
    model_size_b: float
    target_throughput: int
    latency_budget_ms: int
    gpu_type: str
    gpu_count: int
    need_multi_model: bool
    team_size: str  # small/medium/large


@dataclass
class FrameworkProfile:
    """框架能力画像"""
    name: str
    throughput_factor: float
    latency_factor: float
    memory_efficiency: float
    setup_complexity: int
    multi_model_support: bool
    features: list[str] = field(default_factory=list)


class ServingFrameworkSelector:
    """推理框架选型器"""

    FRAMEWORKS = {
        "vLLM": FrameworkProfile(
            name="vLLM",
            throughput_factor=1.0,
            latency_factor=1.0,
            memory_efficiency=0.92,
            setup_complexity=2,
            multi_model_support=True,
            features=["PagedAttention", "连续批处理",
                      "OpenAI兼容API", "LoRA热加载"],
        ),
        "TGI": FrameworkProfile(
            name="TGI",
            throughput_factor=0.85,
            latency_factor=0.95,
            memory_efficiency=0.88,
            setup_complexity=2,
            multi_model_support=True,
            features=["Flash Attention", "HF Hub集成",
                      "Docker部署", "Prometheus监控"],
        ),
        "TensorRT-LLM": FrameworkProfile(
            name="TensorRT-LLM",
            throughput_factor=1.4,
            latency_factor=0.7,
            memory_efficiency=0.95,
            setup_complexity=4,
            multi_model_support=False,
            features=["Kernel融合", "INT4/INT8量化",
                      "多GPU张量并行", "极致吞吐"],
        ),
    }

    def evaluate(self, scenario: DeploymentScenario) -> list[dict]:
        results = []
        for name, fw in self.FRAMEWORKS.items():
            score = self._score(fw, scenario)
            results.append({
                "framework": name,
                "score": round(score, 2),
                "est_throughput": round(
                    scenario.target_throughput * fw.throughput_factor
                ),
                "est_latency_ms": round(
                    scenario.latency_budget_ms * fw.latency_factor
                ),
                "complexity": fw.setup_complexity,
                "features": fw.features,
                "notes": self._fit_notes(fw, scenario),
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _score(self, fw: FrameworkProfile,
               s: DeploymentScenario) -> float:
        score = fw.throughput_factor * 30
        score += (1 - fw.latency_factor) * 25
        penalty = {"small": 5, "medium": 3, "large": 1}
        score -= fw.setup_complexity * penalty.get(s.team_size, 3)
        if s.need_multi_model and fw.multi_model_support:
            score += 15
        elif s.need_multi_model and not fw.multi_model_support:
            score -= 10
        score += fw.memory_efficiency * 10
        return score

    def _fit_notes(self, fw: FrameworkProfile,
                   s: DeploymentScenario) -> list[str]:
        notes = []
        if s.team_size == "small" and fw.setup_complexity > 3:
            notes.append("⚠️ 小团队维护成本高")
        if s.need_multi_model and not fw.multi_model_support:
            notes.append("⚠️ 不支持多模型热切换")
        if fw.name == "TensorRT-LLM":
            notes.append("需要30-60分钟编译时间")
        return notes


def generate_deploy_config(framework: str, model: str,
                           gpu_count: int) -> dict:
    """生成部署配置模板"""
    configs = {
        "vLLM": {
            "command": f"python -m vllm.entrypoints.openai.api_server "
                       f"--model {model} --tensor-parallel-size {gpu_count}",
            "env": {"CUDA_VISIBLE_DEVICES": ",".join(
                str(i) for i in range(gpu_count)
            )},
            "port": 8000,
            "health_check": "/health",
        },
        "TGI": {
            "command": f"text-generation-launcher --model-id {model} "
                       f"--num-shard {gpu_count}",
            "env": {"PORT": "8080"},
            "port": 8080,
            "health_check": "/health",
        },
        "TensorRT-LLM": {
            "steps": [
                f"1. trtllm-build --model {model} --tp {gpu_count}",
                "2. tritonserver --model-repository=/models",
            ],
            "port": 8001,
            "health_check": "/v2/health/ready",
        },
    }
    return configs.get(framework, {})


if __name__ == "__main__":
    selector = ServingFrameworkSelector()

    scenarios = [
        DeploymentScenario(
            name="初创团队-快速迭代",
            model_size_b=7,
            target_throughput=20,
            latency_budget_ms=500,
            gpu_type="A100",
            gpu_count=1,
            need_multi_model=True,
            team_size="small",
        ),
        DeploymentScenario(
            name="大厂-高吞吐生产",
            model_size_b=13,
            target_throughput=100,
            latency_budget_ms=200,
            gpu_type="H100",
            gpu_count=4,
            need_multi_model=False,
            team_size="large",
        ),
        DeploymentScenario(
            name="中型团队-多模型服务",
            model_size_b=7,
            target_throughput=50,
            latency_budget_ms=300,
            gpu_type="A100",
            gpu_count=2,
            need_multi_model=True,
            team_size="medium",
        ),
    ]

    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"场景: {scenario.name}")
        print(f"模型: {scenario.model_size_b}B, "
              f"目标: {scenario.target_throughput} req/s, "
              f"延迟: <{scenario.latency_budget_ms}ms")
        print(f"GPU: {scenario.gpu_count}x {scenario.gpu_type}, "
              f"团队: {scenario.team_size}")

        results = selector.evaluate(scenario)
        print(f"\n推荐排序:")
        for i, r in enumerate(results):
            marker = "🏆" if i == 0 else "  "
            print(f"  {marker} {r['framework']}: "
                  f"评分={r['score']}, "
                  f"吞吐≈{r['est_throughput']} rps, "
                  f"延迟≈{r['est_latency_ms']}ms")
            for note in r["notes"]:
                print(f"      {note}")

    # 生成部署配置
    print(f"\n{'='*60}")
    print("=== vLLM 部署配置示例 ===")
    config = generate_deploy_config("vLLM", "meta-llama/Llama-2-7b", 1)
    for k, v in config.items():
        print(f"  {k}: {v}")
