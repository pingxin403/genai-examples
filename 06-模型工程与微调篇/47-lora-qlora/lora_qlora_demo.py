"""
LoRA/QLoRA实战演示
对应文章：47-LoRA-QLoRA实战消费级显卡也能微调大模型
"""
from dataclasses import dataclass, field
import json


@dataclass
class LoRAConfig:
    """LoRA训练配置"""
    base_model: str = "meta-llama/Llama-2-7b-hf"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list = field(
        default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"]
    )
    use_4bit: bool = True
    learning_rate: float = 2e-4
    num_epochs: int = 3
    batch_size: int = 4
    gradient_accumulation: int = 4
    max_seq_length: int = 1024


class LoRATrainer:
    """LoRA训练管理器（演示版）"""

    def __init__(self, config: LoRAConfig):
        self.config = config

    def estimate_memory(self) -> dict:
        base_params = 7_000_000_000
        if self.config.use_4bit:
            base_memory_gb = base_params * 0.5 / 1e9
        else:
            base_memory_gb = base_params * 2 / 1e9

        lora_params = (
            2 * 4096 * self.config.lora_r
            * len(self.config.target_modules)
        )
        lora_memory_gb = lora_params * 2 / 1e9
        overhead_gb = 2.0
        total = base_memory_gb + lora_memory_gb + overhead_gb

        return {
            "base_model_gb": round(base_memory_gb, 1),
            "lora_params": lora_params,
            "lora_memory_gb": round(lora_memory_gb, 3),
            "overhead_gb": overhead_gb,
            "total_gb": round(total, 1),
            "recommended_gpu": self._recommend_gpu(total),
        }

    def _recommend_gpu(self, total_gb: float) -> str:
        if total_gb <= 8:
            return "RTX 4060 (8GB)"
        elif total_gb <= 16:
            return "RTX 4060Ti 16GB"
        elif total_gb <= 24:
            return "RTX 4090 (24GB)"
        elif total_gb <= 40:
            return "A100 40GB"
        return "A100 80GB 或多卡"

    def simulate_training(self, dataset_size: int) -> dict:
        steps_per_epoch = dataset_size // (
            self.config.batch_size * self.config.gradient_accumulation
        )
        total_steps = steps_per_epoch * self.config.num_epochs

        log = []
        loss = 2.5
        for epoch in range(self.config.num_epochs):
            for step in range(steps_per_epoch):
                loss *= 0.995
                if step % max(1, steps_per_epoch // 3) == 0:
                    log.append({
                        "epoch": epoch + 1,
                        "step": epoch * steps_per_epoch + step,
                        "loss": round(loss, 4),
                    })

        return {
            "total_steps": total_steps,
            "final_loss": round(loss, 4),
            "log_entries": len(log),
        }


class LoRAVersionManager:
    """LoRA版本管理"""

    def __init__(self):
        self.versions = {}

    def register(self, name: str, config: LoRAConfig, metrics: dict):
        version_id = f"{name}_v{len(self.versions) + 1}"
        self.versions[version_id] = {
            "config": {
                "r": config.lora_r,
                "alpha": config.lora_alpha,
                "modules": config.target_modules,
                "4bit": config.use_4bit,
            },
            "metrics": metrics,
            "status": "staging",
        }
        return version_id

    def promote(self, version_id: str):
        if version_id in self.versions:
            # 将当前production降级
            for vid, v in self.versions.items():
                if v["status"] == "production":
                    v["status"] = "archived"
            self.versions[version_id]["status"] = "production"

    def list_versions(self) -> dict:
        return self.versions


if __name__ == "__main__":
    # 对比不同配置的显存需求
    configs = [
        ("LoRA r=8 (fp16)", LoRAConfig(lora_r=8, use_4bit=False)),
        ("LoRA r=16 (fp16)", LoRAConfig(lora_r=16, use_4bit=False)),
        ("QLoRA r=16 (4bit)", LoRAConfig(lora_r=16, use_4bit=True)),
        ("QLoRA r=64 (4bit)", LoRAConfig(lora_r=64, use_4bit=True)),
    ]

    print("=== 显存需求对比 ===")
    for name, config in configs:
        trainer = LoRATrainer(config)
        mem = trainer.estimate_memory()
        print(f"\n{name}:")
        print(f"  基础模型: {mem['base_model_gb']}GB")
        print(f"  LoRA参数: {mem['lora_params']:,}")
        print(f"  总显存: {mem['total_gb']}GB")
        print(f"  推荐GPU: {mem['recommended_gpu']}")

    # 模拟训练
    print("\n=== 训练模拟 ===")
    trainer = LoRATrainer(LoRAConfig(lora_r=16, use_4bit=True))
    result = trainer.simulate_training(dataset_size=2000)
    print(f"总步数: {result['total_steps']}")
    print(f"最终Loss: {result['final_loss']}")

    # 版本管理
    print("\n=== 版本管理 ===")
    vm = LoRAVersionManager()
    v1 = vm.register("customer_service", LoRAConfig(lora_r=8),
                      {"accuracy": 0.85})
    v2 = vm.register("customer_service", LoRAConfig(lora_r=16),
                      {"accuracy": 0.90})
    vm.promote(v2)

    for vid, info in vm.list_versions().items():
        print(f"  {vid}: status={info['status']}, "
              f"accuracy={info['metrics']['accuracy']}")
