# 🎯 Embedding模型横向评测实战示例

> 配套文章：《Embedding模型怎么选？7款主流模型横向评测》

## 功能简述

演示Embedding模型评测框架的核心实现：

1. **多模型参数对比** - 7款主流Embedding模型的维度、速度、适用场景
2. **评测框架搭建** - 基于Hit Rate和MRR指标的检索质量评估
3. **存储成本估算** - 不同维度模型在大规模知识库下的存储开销计算
4. **选型决策辅助** - 根据评测结果输出模型推荐

## 运行环境

- Python 3.10+
- numpy

## 依赖安装

```bash
pip install numpy
```

## 运行命令

```bash
python embedding_eval_demo.py
```

## 输出说明

程序会模拟7款Embedding模型在多领域数据集上的评测过程，输出每个模型的Hit Rate、MRR、推理速度、向量维度等指标，并生成存储成本估算和最终选型建议。
