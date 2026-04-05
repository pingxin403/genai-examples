"""
LLM 能力边界评估器 —— 判断任务是否适合用 LLM

对应文章：《别啥都上AI！一张图看懂LLM的能力边界》

用法：
    python app.py                # 评估内置示例任务
    python app.py --interactive  # 交互模式，手动输入评分

核心思路：
    用 5 个维度给任务打分（0-10），加权求和后按阈值输出选型建议。
"""

import json
import os
import sys

# ============================================================
# 评估维度定义
# ============================================================

DIMENSIONS = {
    "business_value": {
        "weight": 0.30,
        "label": "业务价值",
        "question": "自动化后是否显著提升效率或体验？(0=无提升, 10=极大提升)",
    },
    "replaceability": {
        "weight": 0.20,
        "label": "可替代性(反向)",
        "question": "规则引擎能否更简单更稳地解决？(0=规则完全能搞定, 10=规则搞不定)",
    },
    "risk_cost": {
        "weight": 0.20,
        "label": "风险成本(反向)",
        "question": "错误代价是否可承受？(0=出错就是事故, 10=错了无所谓)",
    },
    "running_cost": {
        "weight": 0.15,
        "label": "运行成本",
        "question": "Token+推理+运维成本是否可控？(0=成本极高, 10=成本很低)",
    },
    "measurability": {
        "weight": 0.15,
        "label": "可评估性",
        "question": "能否定义可观测指标做闭环？(0=无法量化, 10=指标清晰)",
    },
}

# ============================================================
# 评估逻辑
# ============================================================


def evaluate_task(name: str, scores: dict) -> dict:
    """
    对单个任务进行 LLM 适配度评估。

    参数:
        name:   任务名称
        scores: 各维度评分 {"business_value": 8, ...}，每项 0-10

    返回:
        {"name", "score", "decision", "reason", "details"}
    """
    total = 0.0
    details = []
    for dim, cfg in DIMENSIONS.items():
        val = scores.get(dim, 5)
        weighted = val * cfg["weight"]
        total += weighted
        details.append(f"  {cfg['label']}: {val}/10 (权重{cfg['weight']:.0%}, 贡献{weighted:.1f})")

    if total >= 7.0:
        decision = "LLM 主导"
        reason = "业务价值高、规则难替代、风险可控，建议以 LLM 为核心方案"
    elif total >= 5.0:
        decision = "混合架构（LLM + 规则）"
        reason = "部分环节适合 LLM，但需规则兜底和人工复核"
    else:
        decision = "规则系统优先"
        reason = "规则明确或风险过高，优先确定性系统，LLM 仅做辅助"

    return {
        "name": name,
        "score": round(total, 1),
        "decision": decision,
        "reason": reason,
        "details": details,
    }


def print_result(result: dict) -> None:
    """格式化输出评估结果。"""
    print(f"\n{'='*50}")
    print(f"任务: {result['name']}")
    print(f"{'='*50}")
    for line in result["details"]:
        print(line)
    print(f"  {'─'*40}")
    print(f"  综合得分: {result['score']}")
    print(f"  选型建议: {result['decision']}")
    print(f"  理由: {result['reason']}")


# ============================================================
# 示例任务集
# ============================================================


def load_tasks() -> list:
    """从 tasks.json 加载示例任务，若文件不存在则用内置数据。"""
    json_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 内置 fallback
    return [
        {
            "name": "内容头脑风暴 / 文案初稿",
            "scores": {"business_value": 8, "replaceability": 9, "risk_cost": 9, "running_cost": 7, "measurability": 6},
        },
        {
            "name": "FAQ 自动分类",
            "scores": {"business_value": 7, "replaceability": 5, "risk_cost": 8, "running_cost": 7, "measurability": 8},
        },
        {
            "name": "合规审批自动判定",
            "scores": {"business_value": 6, "replaceability": 2, "risk_cost": 2, "running_cost": 4, "measurability": 5},
        },
        {
            "name": "税务金额计算",
            "scores": {"business_value": 3, "replaceability": 1, "risk_cost": 1, "running_cost": 3, "measurability": 9},
        },
    ]


# ============================================================
# 交互模式
# ============================================================


def interactive_mode() -> None:
    """让用户手动输入评分，实时输出选型建议。"""
    print("\n🎯 LLM 能力边界评估器 — 交互模式")
    print("请为你的任务在每个维度打分（0-10）\n")

    task_name = input("任务名称: ").strip() or "未命名任务"
    scores = {}
    for dim, cfg in DIMENSIONS.items():
        while True:
            try:
                val = int(input(f"  {cfg['label']} — {cfg['question']}: "))
                if 0 <= val <= 10:
                    scores[dim] = val
                    break
                print("    请输入 0-10 之间的整数")
            except ValueError:
                print("    请输入 0-10 之间的整数")

    result = evaluate_task(task_name, scores)
    print_result(result)


# ============================================================
# 主入口
# ============================================================


def main() -> None:
    if "--interactive" in sys.argv:
        interactive_mode()
        return

    print("🎯 LLM 能力边界评估器 — 批量评估模式\n")
    tasks = load_tasks()
    for task in tasks:
        result = evaluate_task(task["name"], task["scores"])
        print_result(result)

    print(f"\n{'='*50}")
    print("提示: 运行 python app.py --interactive 进入交互模式")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
