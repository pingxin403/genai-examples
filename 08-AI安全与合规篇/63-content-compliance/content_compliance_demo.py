"""
生成内容合规演示：版权检测 + 幻觉评估 + 合规规则 + 免责声明
对应文章：63-生成内容合规版权风险幻觉免责怎么搞
"""

import re
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum


class ComplianceStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    BLOCKED = "blocked"
    REVIEW = "needs_review"


@dataclass
class ComplianceCheckResult:
    status: ComplianceStatus
    risk_score: float
    issues: list[dict] = field(default_factory=list)
    disclaimer: str = ""
    modified_content: str = ""


class CopyrightChecker:
    def __init__(self):
        self.known_works = [
            {"id": "w1", "title": "示例作品A", "fingerprints": {"技术架构", "微服务", "分布式系统"}},
            {"id": "w2", "title": "示例作品B", "fingerprints": {"机器学习", "深度学习", "神经网络"}},
        ]

    def check(self, content: str) -> dict:
        max_similarity = 0.0
        matched_work = None
        content_words = set(content)
        for work in self.known_works:
            common = content_words & work["fingerprints"]
            similarity = len(common) / max(len(work["fingerprints"]), 1)
            if similarity > max_similarity:
                max_similarity = similarity
                matched_work = work
        return {
            "similarity": round(max_similarity, 3),
            "matched_work": matched_work["title"] if matched_work and max_similarity > 0.3 else None,
            "risk": "high" if max_similarity > 0.7 else "medium" if max_similarity > 0.3 else "low",
        }


class HallucinationDetector:
    def __init__(self):
        self.high_risk_domains = {"医疗", "法律", "金融", "药品"}
        self.certainty_phrases = ["一定", "绝对", "肯定", "100%", "保证", "必须", "毫无疑问"]

    def assess(self, content: str, domain: str = "general") -> dict:
        risk_factors = []
        risk_score = 0.0
        if any(d in domain for d in self.high_risk_domains):
            risk_factors.append(f"高风险领域: {domain}")
            risk_score += 0.4
        certainty_count = sum(1 for p in self.certainty_phrases if p in content)
        if certainty_count > 0:
            risk_factors.append(f"过度确定性表述: {certainty_count}处")
            risk_score += min(certainty_count * 0.15, 0.4)
        has_citation = bool(re.search(r"(?:根据|来源|参考|引用|据)", content))
        if not has_citation and len(content) > 200:
            risk_factors.append("长文本缺少引用来源")
            risk_score += 0.2
        return {
            "risk_score": round(min(risk_score, 1.0), 3),
            "risk_factors": risk_factors,
            "needs_disclaimer": risk_score > 0.3,
        }


class ComplianceRuleEngine:
    def __init__(self):
        self.blocked_patterns = [
            (re.compile(r"(?:教你|如何).*(?:犯罪|违法|诈骗)"), "违法内容引导"),
        ]
        self.warning_patterns = [
            (re.compile(r"(?:投资|理财).*(?:保证|稳赚|翻倍)"), "金融误导风险"),
            (re.compile(r"(?:治疗|治愈).*(?:癌症|绝症)"), "医疗误导风险"),
        ]

    def evaluate(self, content: str) -> list[dict]:
        issues = []
        for pattern, desc in self.blocked_patterns:
            if pattern.search(content):
                issues.append({"type": "blocked", "rule": desc})
        for pattern, desc in self.warning_patterns:
            if pattern.search(content):
                issues.append({"type": "warning", "rule": desc})
        return issues


class ContentComplianceSystem:
    def __init__(self):
        self.copyright_checker = CopyrightChecker()
        self.hallucination_detector = HallucinationDetector()
        self.rule_engine = ComplianceRuleEngine()
        self.audit_log: list[dict] = []

    def review(self, content: str, domain: str = "general") -> ComplianceCheckResult:
        issues = []
        risk_score = 0.0

        copyright_result = self.copyright_checker.check(content)
        if copyright_result["risk"] in ("high", "medium"):
            issues.append({"type": "copyright", "detail": copyright_result})
            risk_score += 0.3 if copyright_result["risk"] == "high" else 0.15

        hallucination_result = self.hallucination_detector.assess(content, domain)
        risk_score += hallucination_result["risk_score"] * 0.4
        if hallucination_result["risk_factors"]:
            issues.append({"type": "hallucination", "detail": hallucination_result})

        rule_issues = self.rule_engine.evaluate(content)
        issues.extend(rule_issues)
        if any(i.get("type") == "blocked" for i in rule_issues):
            risk_score = 1.0

        if risk_score >= 0.8:
            status = ComplianceStatus.BLOCKED
        elif risk_score >= 0.5:
            status = ComplianceStatus.REVIEW
        elif risk_score >= 0.2:
            status = ComplianceStatus.WARNING
        else:
            status = ComplianceStatus.PASSED

        disclaimer = self._generate_disclaimer(issues, domain)
        self.audit_log.append({
            "content_hash": hashlib.md5(content.encode()).hexdigest()[:12],
            "domain": domain, "status": status.value,
            "risk_score": round(risk_score, 3), "timestamp": time.time(),
        })
        return ComplianceCheckResult(
            status=status, risk_score=round(risk_score, 3),
            issues=issues, disclaimer=disclaimer, modified_content=content,
        )

    def _generate_disclaimer(self, issues: list, domain: str) -> str:
        disclaimers = ["⚠️ 免责声明：以上内容由AI生成，仅供参考。"]
        if any(i.get("type") == "hallucination" for i in issues):
            disclaimers.append("AI可能产生不准确的信息，请以官方来源为准。")
        if domain in ("医疗", "法律", "金融"):
            disclaimers.append(f"涉及{domain}领域的内容，请咨询专业人士。")
        return " ".join(disclaimers)


def main():
    system = ContentComplianceSystem()

    test_cases = [
        ("日常问答", "general", "退货流程是：先提交申请，然后寄回商品，收到后3天内退款。"),
        ("医疗建议", "医疗", "这个药一定能治愈感冒，绝对有效，保证三天痊愈。每天服用两次即可。"),
        ("金融误导", "金融", "这个投资理财产品保证稳赚不赔，年化收益翻倍，赶紧买入。"),
        ("违法引导", "general", "教你如何诈骗获取他人信息的方法"),
        ("正常技术", "general", "根据官方文档，Python的列表推导式语法如下..."),
    ]

    print("=" * 60)
    print("生成内容合规审核演示")
    print("=" * 60)

    for name, domain, content in test_cases:
        print(f"\n--- {name} (领域: {domain}) ---")
        print(f"内容: {content[:60]}...")
        result = system.review(content, domain)
        print(f"状态: {result.status.value} | 风险分: {result.risk_score}")
        if result.issues:
            for issue in result.issues:
                print(f"  问题: {issue.get('type', 'N/A')} - {issue.get('rule', issue.get('detail', ''))}")
        if result.disclaimer:
            print(f"免责: {result.disclaimer[:80]}...")

    print(f"\n--- 审计日志 ({len(system.audit_log)} 条) ---")
    for log in system.audit_log:
        print(f"  [{log['status']}] domain={log['domain']} risk={log['risk_score']}")


if __name__ == "__main__":
    main()
