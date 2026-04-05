# 88 - LLM部署方案对比演示

> 对应文章：[LLM部署方案：vLLM/TGI/TensorRT-LLM/Ollama对比](../../../GenAI/11-生态与工具篇/88-LLM部署方案vLLM-TGI-TensorRT-LLM-Ollama对比.md)

## 功能说明

演示四大LLM推理引擎的核心设计差异：
- vLLM风格：PagedAttention + Continuous Batching
- TGI风格：Flash Attention + Token Streaming
- TensorRT-LLM风格：Kernel Fusion + In-flight Batching
- Ollama风格：llama.cpp本地推理
- 统一Benchmark性能对比

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python llm_deployment_demo.py
```

## 预期输出

- 四种推理引擎的性能模拟对比
- 首Token延迟、吞吐量、Token生成速度
- 选型建议总结
