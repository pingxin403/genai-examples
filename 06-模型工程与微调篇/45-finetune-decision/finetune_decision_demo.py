"""
微调决策框架演示
对应文章：45-微调决策框架什么时候RAG不够必须微调
"""
from dataclasses import dataclass


@dataclass
class ScenarioProfile:
    """场景画像"""
    name: str
    knowledge_update_freq: str   # daily/weekly/monthly/quarterly
    style_requirement: str       # generic/domain-specific
    labeled_data_count: int
    latency_budget_ms: int
    daily_call_volume: int
    traceability_needed: bool


class FinetuneDecisionFramework:
    """微调决策框架：基于多维度加权评分"""

    WEIGHTS = {
        "knowledge_freshness": 0.2,
        "style_fit": 0.25,
        "data_readiness": 0.2,
        "latency": 0.15,
        "cost_efficiency": 0.1,
        "traceability": 0.1,
    }

    def evaluate(self, profile: ScenarioProfile) -> dict:
        scores = {
            "rag": self._score_rag(profile),
            "finetune": self._score_finetune(profile),
            "hybrid": self._score_hybrid(profile),
        }
        recommendation = max(scores, key=scores.get)
        return {
            "scenario": profile.name,
            "scores": scores,
            "recommendation": recommendation,
            "reason": self._explain(recommendation, profile),
        }

    def _score_rag(self, p: ScenarioProfile) -> float:
        score = 0.0
        if p.knowledge_update_freq in ("daily", "weekly"):
            score += self.WEIGHTS["knowledge_freshness"]
        if p.style_requirement == "generic":
            score += self.WEIGHTS["style_fit"]
        if p.traceability_needed:
            score += self.WEIGHTS["traceability"]
        score += self.WEIGHTS["data_readiness"]
        return round(score, 2)

    def _score_finetune(self, p: ScenarioProfile) -> float:
        score = 0.0
        if p.style_requirement == "domain-specific":
            score += self.WEIGHTS["style_fit"]
        if p.labeled_data_count >= 500:
            score += self.WEIGHTS["data_readiness"]
        if p.latency_budget_ms < 500:
            score += self.WEIGHTS["latency"]
        if p.daily_call_volume > 10000:
            score += self.WEIGHTS["cost_efficiency"]
        return round(score, 2)

    def _score_hybrid(self, p: ScenarioProfile) -> float:
        rag = self._score_rag(p)
        ft = self._score_finetune(p)
        return round((rag + ft) * 0.6, 2)

    def _explain(self, rec: str, p: ScenarioProfile) -> str:
        reasons = {
            "rag": f"知识更新频率高({p.knowledge_update_freq})，且需要可追溯性",
            "finetune": f"需要领域特定风格，有{p.labeled_data_count}条标注数据",
            "hybrid": "兼顾知识时效性和输出风格，推荐组合方案",
        }
        return reasons.get(rec, "")


def estimate_monthly_cost(approach: str, daily_volume: int) -> dict:
    """估算月度成本"""
    costs = {
        "rag": {
            "vector_db": 500,
            "embedding": daily_volume * 30 * 0.01,
            "llm_inference": daily_volume * 30 * 0.02,
        },
        "finetune": {
            "training": 300,  # 一次性训练，摊到月
            "llm_inference": daily_volume * 30 * 0.008,
        },
        "hybrid": {
            "vector_db": 500,
            "embedding": daily_volume * 30 * 0.01,
            "llm_inference": daily_volume * 30 * 0.012,
            "training": 300,
        },
    }
    cost_detail = costs.get(approach, {})
    cost_detail["total"] = sum(cost_detail.values())
    return cost_detail


if __name__ == "__main__":
    framework = FinetuneDecisionFramework()

    scenarios = [
        ScenarioProfile(
            name="法律合同审查",
            knowledge_update_freq="monthly",
            style_requirement="domain-specific",
            labeled_data_count=800,
            latency_budget_ms=1000,
            daily_call_volume=5000,
            traceability_needed=True,
        ),
        ScenarioProfile(
            name="实时新闻问答",
            knowledge_update_freq="daily",
            style_requirement="generic",
            labeled_data_count=0,
            latency_budget_ms=2000,
            daily_call_volume=20000,
            traceability_needed=True,
        ),
        ScenarioProfile(
            name="医疗报告生成",
            knowledge_update_freq="quarterly",
            style_requirement="domain-specific",
            labeled_data_count=1200,
            latency_budget_ms=300,
            daily_call_volume=15000,
            traceability_needed=False,
        ),
    ]

    for scenario in scenarios:
        result = framework.evaluate(scenario)
        print(f"\n{'='*50}")
        print(f"场景: {result['scenario']}")
        print(f"评分: RAG={result['scores']['rag']}, "
              f"微调={result['scores']['finetune']}, "
              f"混合={result['scores']['hybrid']}")
        print(f"推荐: {result['recommendation']}")
        print(f"原因: {result['reason']}")

        cost = estimate_monthly_cost(result["recommendation"], scenario.daily_call_volume)
        print(f"预估月成本: ¥{cost['total']:,.0f}")
