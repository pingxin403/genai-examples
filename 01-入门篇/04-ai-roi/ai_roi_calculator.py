"""
AI项目ROI计算器
配套文章：《老板问"AI值不值"？这是我算ROI的Excel模板》

从用户采纳率、成本节约、转化提升三个维度量化AI价值。
"""


# ============================================================
# 1. 成本计算器
# ============================================================

class AICostCalculator:
    """AI项目全口径成本计算器
    
    不只算Token成本，还包括工程维护、人审评测、基础设施。
    """

    def __init__(self, config: dict):
        self.config = config

    def monthly_inference_cost(self) -> float:
        """推理成本 = 月请求量 × Token消耗 × Token单价"""
        monthly_requests = self.config["daily_requests"] * 30
        input_cost = (
            monthly_requests
            * self.config["avg_input_tokens"]
            * self.config["input_price_per_1k"]
            / 1000
        )
        output_cost = (
            monthly_requests
            * self.config["avg_output_tokens"]
            * self.config["output_price_per_1k"]
            / 1000
        )
        return round(input_cost + output_cost, 2)

    def monthly_operation_cost(self) -> float:
        """运营成本 = 工程维护 + 人工评测 + 基础设施"""
        engineering = (
            self.config["engineer_hours_per_month"]
            * self.config["engineer_hourly_rate"]
        )
        review = (
            self.config["review_hours_per_month"]
            * self.config["reviewer_hourly_rate"]
        )
        infra = self.config["monthly_infra_cost"]
        return round(engineering + review + infra, 2)

    def total_monthly_cost(self) -> float:
        return round(self.monthly_inference_cost() + self.monthly_operation_cost(), 2)

    def cost_breakdown(self) -> dict:
        """成本结构拆解"""
        inference = self.monthly_inference_cost()
        operation = self.monthly_operation_cost()
        total = inference + operation
        return {
            "推理成本": inference,
            "运营成本": operation,
            "总成本": total,
            "推理占比": f"{inference / total * 100:.1f}%" if total > 0 else "0%",
            "运营占比": f"{operation / total * 100:.1f}%" if total > 0 else "0%",
        }


# ============================================================
# 2. 收益计算器
# ============================================================

class AIBenefitCalculator:
    """AI项目三条价值线收益计算器
    
    价值线1: 成本节约（人工替代）
    价值线2: 收入提升（转化增量）
    价值线3: 风险降低（事故减少）
    """

    def __init__(self, config: dict):
        self.config = config

    def monthly_cost_saving(self) -> float:
        """成本节约 = 自动处理量 × 单次人工成本"""
        daily_requests = self.config["daily_requests"]
        adoption_rate = self.config["adoption_rate"]
        auto_handled = daily_requests * adoption_rate * 30
        per_manual_cost = (
            self.config["manual_minutes_per_request"]
            / 60
            * self.config["manual_hourly_rate"]
        )
        return round(auto_handled * per_manual_cost, 2)

    def monthly_revenue_uplift(self) -> float:
        """收入提升 = 增量转化数 × 客单价"""
        monthly_sessions = self.config["daily_requests"] * 30
        incremental = monthly_sessions * (
            self.config["ai_conversion_rate"]
            - self.config["baseline_conversion_rate"]
        )
        return round(max(0, incremental * self.config["avg_order_value"]), 2)

    def monthly_risk_reduction(self) -> float:
        """风险降低 = 历史月均事故成本 × 降低比例"""
        return round(
            self.config["monthly_incident_cost"]
            * self.config["incident_reduction_rate"],
            2,
        )

    def total_monthly_benefit(self) -> float:
        return round(
            self.monthly_cost_saving()
            + self.monthly_revenue_uplift()
            + self.monthly_risk_reduction(),
            2,
        )

    def benefit_breakdown(self) -> dict:
        """收益结构拆解"""
        saving = self.monthly_cost_saving()
        revenue = self.monthly_revenue_uplift()
        risk = self.monthly_risk_reduction()
        total = saving + revenue + risk
        return {
            "成本节约": saving,
            "收入提升": revenue,
            "风险降低": risk,
            "总收益": total,
        }


# ============================================================
# 3. 情景分析引擎
# ============================================================

def scenario_analysis(base_config: dict) -> dict:
    """三档情景分析：乐观 / 基准 / 悲观
    
    管理层通常更看重"悲观情景是否还能活"。
    """
    scenarios = {
        "乐观": {
            "adoption_rate": 0.80,
            "ai_conversion_rate": 0.08,
            "incident_reduction_rate": 0.50,
        },
        "基准": {
            "adoption_rate": 0.60,
            "ai_conversion_rate": 0.06,
            "incident_reduction_rate": 0.30,
        },
        "悲观": {
            "adoption_rate": 0.35,
            "ai_conversion_rate": 0.045,
            "incident_reduction_rate": 0.15,
        },
    }

    results = {}
    for name, overrides in scenarios.items():
        config = {**base_config, **overrides}
        cost_calc = AICostCalculator(config)
        benefit_calc = AIBenefitCalculator(config)

        monthly_cost = cost_calc.total_monthly_cost()
        monthly_benefit = benefit_calc.total_monthly_benefit()
        monthly_net = round(monthly_benefit - monthly_cost, 2)
        annual_cost = monthly_cost * 12
        annual_net = monthly_net * 12
        roi = (annual_net / annual_cost) * 100 if annual_cost > 0 else 0

        payback = "无法回本"
        if monthly_net > 0 and base_config.get("initial_investment", 0) > 0:
            payback = f"{base_config['initial_investment'] / monthly_net:.1f}个月"

        results[name] = {
            "月成本": monthly_cost,
            "月收益": monthly_benefit,
            "月净收益": monthly_net,
            "年ROI": f"{roi:.1f}%",
            "回本周期": payback,
            "成本明细": cost_calc.cost_breakdown(),
            "收益明细": benefit_calc.benefit_breakdown(),
        }

    return results


# ============================================================
# 4. 投资决策引擎
# ============================================================

def investment_decision(scenario_results: dict) -> dict:
    """基于情景分析结果给出投资建议"""
    decisions = {}
    for scenario, metrics in scenario_results.items():
        monthly_net = metrics["月净收益"]
        if monthly_net > 50000:
            decisions[scenario] = "✅ 扩大投入"
        elif monthly_net > 0:
            decisions[scenario] = "🔄 维持观察"
        elif monthly_net > -10000:
            decisions[scenario] = "⚠️ 降级投入"
        else:
            decisions[scenario] = "🛑 止损退出"

    # 综合建议
    pessimistic_net = scenario_results.get("悲观", {}).get("月净收益", 0)
    if pessimistic_net > 0:
        decisions["综合建议"] = "悲观情景仍可盈利，建议分阶段推进"
    elif scenario_results.get("基准", {}).get("月净收益", 0) > 0:
        decisions["综合建议"] = "基准情景可盈利但悲观情景亏损，建议小规模试点验证"
    else:
        decisions["综合建议"] = "基准情景即亏损，建议重新评估场景选择或成本结构"

    return decisions


# ============================================================
# 5. 主程序：完整ROI报告
# ============================================================

def print_report(config: dict):
    """生成完整ROI分析报告"""
    print("=" * 60)
    print("           AI项目ROI计算报告")
    print("=" * 60)

    # 基准成本分析
    cost_calc = AICostCalculator(config)
    cost_detail = cost_calc.cost_breakdown()
    print("\n【成本分析】")
    print(f"  推理成本（月）:     ¥{cost_detail['推理成本']:>12,.2f}")
    print(f"  运营成本（月）:     ¥{cost_detail['运营成本']:>12,.2f}")
    print(f"  总成本（月）:       ¥{cost_detail['总成本']:>12,.2f}")
    print(f"  推理占比: {cost_detail['推理占比']}, 运营占比: {cost_detail['运营占比']}")

    # 基准收益分析
    benefit_calc = AIBenefitCalculator(config)
    benefit_detail = benefit_calc.benefit_breakdown()
    print("\n【收益分析（基准情景）】")
    print(f"  成本节约（月）:     ¥{benefit_detail['成本节约']:>12,.2f}")
    print(f"  收入提升（月）:     ¥{benefit_detail['收入提升']:>12,.2f}")
    print(f"  风险降低（月）:     ¥{benefit_detail['风险降低']:>12,.2f}")
    print(f"  总收益（月）:       ¥{benefit_detail['总收益']:>12,.2f}")

    # 情景分析
    results = scenario_analysis(config)
    print("\n【三档情景分析】")
    for name in ["乐观", "基准", "悲观"]:
        r = results[name]
        print(f"  {name}: 年ROI={r['年ROI']}, 回本周期={r['回本周期']}, "
              f"月净收益=¥{r['月净收益']:,.2f}")

    # 投资建议
    decisions = investment_decision(results)
    print("\n【投资建议】")
    for scenario, decision in decisions.items():
        print(f"  {scenario}: {decision}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 示例配置：AI客服增强项目（中等规模）
    sample_config = {
        # 请求量
        "daily_requests": 500,
        # Token消耗（GPT-4级别定价）
        "avg_input_tokens": 800,
        "avg_output_tokens": 400,
        "input_price_per_1k": 0.06,   # ¥/千Token（输入）
        "output_price_per_1k": 0.12,  # ¥/千Token（输出）
        # 运营成本
        "engineer_hours_per_month": 60,
        "engineer_hourly_rate": 250,
        "review_hours_per_month": 40,
        "reviewer_hourly_rate": 120,
        "monthly_infra_cost": 5000,
        # 收益参数（基准情景）
        "adoption_rate": 0.60,
        "manual_minutes_per_request": 3,
        "manual_hourly_rate": 60,
        "baseline_conversion_rate": 0.03,
        "ai_conversion_rate": 0.06,
        "avg_order_value": 200,
        "monthly_incident_cost": 50000,
        "incident_reduction_rate": 0.30,
        # 初始投入
        "initial_investment": 200000,
    }

    print_report(sample_config)
