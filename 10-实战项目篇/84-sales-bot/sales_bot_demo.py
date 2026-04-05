"""
销售赋能Bot演示：客户问答 + 竞品分析 + 话术建议
对应文章：84-销售赋能Bot客户问答加竞品分析加话术建议
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class ProductInfo:
    product_id: str
    name: str
    features: list[str]
    pricing: str
    advantages: list[str]
    use_cases: list[str] = field(default_factory=list)


@dataclass
class CompetitorInfo:
    name: str
    features: list[str]
    pricing: str
    weaknesses: list[str]
    our_advantages: list[str]
    updated_at: float = field(default_factory=time.time)


@dataclass
class SalesTalk:
    scenario: str
    customer_question: str
    recommended_answer: str
    keywords: list[str] = field(default_factory=list)
    tips: str = ""


class ProductKnowledgeBase:
    """产品知识库"""

    def __init__(self):
        self.products: dict[str, ProductInfo] = {}

    def add_product(self, product: ProductInfo):
        self.products[product.product_id] = product

    def search(self, query: str) -> list[dict]:
        results = []
        for p in self.products.values():
            score = self._relevance(query, p)
            if score > 0:
                results.append({"product": p, "score": round(score, 3)})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _relevance(self, query: str, product: ProductInfo) -> float:
        q_set = set(query)
        p_set = set(product.name) | set("".join(product.features))
        union = q_set | p_set
        return len(q_set & p_set) / len(union) if union else 0


class CompetitorAnalyzer:
    """竞品分析引擎"""

    def __init__(self):
        self.competitors: dict[str, CompetitorInfo] = {}

    def add_competitor(self, comp: CompetitorInfo):
        self.competitors[comp.name] = comp

    def compare(self, competitor_name: str,
                our_product: ProductInfo) -> dict:
        comp = None
        for name, c in self.competitors.items():
            if competitor_name in name or name in competitor_name:
                comp = c
                break
        if not comp:
            return {"error": f"未找到竞品: {competitor_name}",
                    "available": list(self.competitors.keys())}

        age_days = (time.time() - comp.updated_at) / 86400
        stale = age_days > 30

        return {
            "competitor": comp.name,
            "our_product": our_product.name,
            "our_advantages": comp.our_advantages,
            "their_weaknesses": comp.weaknesses,
            "pricing": f"我们: {our_product.pricing} vs 竞品: {comp.pricing}",
            "stale_warning": f"⚠️ 信息已{int(age_days)}天未更新" if stale else None,
        }

    def list_competitors(self) -> list[str]:
        return list(self.competitors.keys())


class TalkRecommender:
    """话术推荐引擎"""

    def __init__(self):
        self.talks: list[SalesTalk] = []

    def add_talk(self, talk: SalesTalk):
        self.talks.append(talk)

    def recommend(self, question: str) -> list[SalesTalk]:
        scored = []
        for talk in self.talks:
            score = sum(1 for kw in talk.keywords if kw in question)
            if score > 0:
                scored.append((talk, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in scored[:3]]


class SalesBot:
    """销售赋能Bot主控"""

    def __init__(self):
        self.kb = ProductKnowledgeBase()
        self.analyzer = CompetitorAnalyzer()
        self.recommender = TalkRecommender()

    def handle_query(self, query: str) -> dict:
        intent = self._detect_intent(query)

        if intent == "competitor":
            return self._handle_competitor(query)
        elif intent == "talk":
            return self._handle_talk(query)
        else:
            return self._handle_product(query)

    def _detect_intent(self, query: str) -> str:
        comp_kw = ["竞品", "对比", "区别", "vs", "比较", "竞争"]
        talk_kw = ["话术", "怎么说", "怎么回答", "异议", "拒绝"]
        if any(kw in query for kw in comp_kw):
            return "competitor"
        if any(kw in query for kw in talk_kw):
            return "talk"
        return "product"

    def _handle_product(self, query: str) -> dict:
        results = self.kb.search(query)
        if not results:
            return {"type": "product", "answer": "未找到相关产品信息",
                    "results": []}
        best = results[0]["product"]
        answer = (f"关于{best.name}：\n"
                  f"核心功能：{', '.join(best.features[:3])}\n"
                  f"定价：{best.pricing}\n"
                  f"优势：{', '.join(best.advantages[:2])}")
        return {"type": "product", "answer": answer, "results": results}

    def _handle_competitor(self, query: str) -> dict:
        for comp_name in self.analyzer.list_competitors():
            if comp_name in query:
                products = list(self.kb.products.values())
                if products:
                    comparison = self.analyzer.compare(comp_name, products[0])
                    return {"type": "competitor", "comparison": comparison}
        return {"type": "competitor",
                "answer": f"请指定竞品名称，可选: {self.analyzer.list_competitors()}"}

    def _handle_talk(self, query: str) -> dict:
        talks = self.recommender.recommend(query)
        if not talks:
            return {"type": "talk", "answer": "未找到匹配的话术建议"}
        return {"type": "talk", "talks": [
            {"scenario": t.scenario, "answer": t.recommended_answer,
             "tips": t.tips}
            for t in talks
        ]}


def build_test_data(bot: SalesBot):
    # 产品
    bot.kb.add_product(ProductInfo(
        "p1", "AI智能平台",
        ["RAG知识问答", "Agent工作流", "多模型路由", "可观测性"],
        "企业版 5万/年，旗舰版 15万/年",
        ["响应速度快（P99<500ms）", "支持私有化部署", "中文效果领先"],
        ["智能客服", "内部知识库", "数据分析"],
    ))

    # 竞品
    now = time.time()
    bot.analyzer.add_competitor(CompetitorInfo(
        "竞品A", ["基础RAG", "简单Agent", "云端部署"],
        "3万/年", ["不支持私有化", "中文效果一般", "无可观测性"],
        ["我们支持私有化部署", "中文效果领先30%", "内置可观测性"],
        updated_at=now - 10 * 86400,
    ))
    bot.analyzer.add_competitor(CompetitorInfo(
        "竞品B", ["高级RAG", "多Agent", "混合部署"],
        "20万/年", ["价格昂贵", "学习曲线陡峭", "定制化困难"],
        ["价格优势明显", "上手更快", "定制化灵活"],
        updated_at=now - 60 * 86400,  # 过期信息
    ))

    # 话术
    talks = [
        SalesTalk("价格异议", "你们太贵了",
                  "要点：1.按ROI算账（节省人力成本） 2.对比竞品性价比 3.提供分期方案",
                  ["贵", "价格", "便宜", "预算"],
                  "不要直接降价，先展示价值"),
        SalesTalk("竞品对比", "竞品也有类似功能",
                  "要点：1.承认竞品优点 2.突出差异化（私有化/中文/速度） 3.提供POC对比",
                  ["竞品", "对比", "区别", "类似"],
                  "不要贬低竞品，用数据说话"),
        SalesTalk("需求不明确", "我们还在评估要不要用AI",
                  "要点：1.了解业务痛点 2.提供免费POC 3.分享同行业案例",
                  ["评估", "考虑", "不确定", "要不要"],
                  "先帮客户梳理需求，不急于推销"),
        SalesTalk("拒绝跟进", "我们暂时不需要",
                  "要点：1.尊重决定 2.留下资料 3.约定下次联系时间",
                  ["不需要", "拒绝", "暂时", "以后再说"],
                  "保持专业，不要纠缠"),
    ]
    for t in talks:
        bot.recommender.add_talk(t)


def main():
    bot = SalesBot()
    build_test_data(bot)

    print("=" * 60)
    print("销售赋能Bot演示")
    print("=" * 60)

    # 1. 产品问答
    print("\n--- 1. 产品问答 ---")
    product_queries = [
        "AI平台有什么功能",
        "产品定价多少",
        "支持哪些场景",
    ]
    for q in product_queries:
        result = bot.handle_query(q)
        print(f"\n  问: {q}")
        print(f"  答: {result.get('answer', '无结果')[:80]}")

    # 2. 竞品分析
    print("\n--- 2. 竞品分析 ---")
    comp_queries = [
        "和竞品A对比有什么区别",
        "竞品B怎么样",
    ]
    for q in comp_queries:
        result = bot.handle_query(q)
        print(f"\n  问: {q}")
        if "comparison" in result:
            comp = result["comparison"]
            print(f"  我们的优势: {comp.get('our_advantages', [])}")
            print(f"  竞品弱点: {comp.get('their_weaknesses', [])}")
            print(f"  价格对比: {comp.get('pricing', '')}")
            if comp.get("stale_warning"):
                print(f"  {comp['stale_warning']}")
        else:
            print(f"  {result.get('answer', '')}")

    # 3. 话术推荐
    print("\n--- 3. 话术推荐 ---")
    talk_queries = [
        "客户说太贵了怎么回答",
        "客户说竞品也有类似功能",
        "客户说暂时不需要",
    ]
    for q in talk_queries:
        result = bot.handle_query(q)
        print(f"\n  问: {q}")
        if "talks" in result:
            for t in result["talks"][:1]:
                print(f"  场景: {t['scenario']}")
                print(f"  建议: {t['answer']}")
                print(f"  提示: {t['tips']}")
        else:
            print(f"  {result.get('answer', '')}")

    # 4. 综合演示
    print("\n--- 4. 销售场景模拟 ---")
    scenario = [
        "AI平台支持私有化部署吗",
        "和竞品A对比有什么优势",
        "客户说价格太贵了怎么说",
    ]
    print("  场景：客户咨询AI平台，关注私有化和价格")
    for q in scenario:
        result = bot.handle_query(q)
        print(f"\n  销售问Bot: {q}")
        if result["type"] == "product":
            print(f"  Bot回答: {result.get('answer', '')[:60]}...")
        elif result["type"] == "competitor":
            comp = result.get("comparison", {})
            adv = comp.get("our_advantages", ["无数据"])
            print(f"  Bot回答: 我们的优势 - {adv[0]}")
        elif result["type"] == "talk":
            talks = result.get("talks", [])
            if talks:
                print(f"  Bot建议: {talks[0]['answer'][:60]}...")


if __name__ == "__main__":
    main()
