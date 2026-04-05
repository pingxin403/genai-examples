# 70 - Prompt管理平台演示

> 对应文章：[Prompt管理平台：提示词的Git+CI/CD+灰度](../../../GenAI/09-AI平台工程篇/70-Prompt管理平台提示词的Git加CICD加灰度.md)

## 功能说明

演示Prompt管理平台的核心能力：
- Prompt版本注册与管理
- CI测试Pipeline（评估集回归测试）
- 灰度发布控制器（金丝雀部署）
- 一键回滚

## 运行环境

- Python 3.10+
- 无额外依赖（纯标准库实现）

## 运行方式

```bash
python prompt_platform_demo.py
```

## 预期输出

- Prompt版本创建与历史查看
- CI测试通过/失败演示
- 灰度发布流量分配
- 全量发布与回滚操作
