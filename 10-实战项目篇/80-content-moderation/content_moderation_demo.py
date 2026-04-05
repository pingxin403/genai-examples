"""
AI内容审核演示：多模态 + 规则引擎 + 人工复审
对应文章：80-AI内容审核多模态加规则引擎加人工复审
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class TextModerator:
    """文本审核引擎"""

    SENSITIVE_WORDS = {
        "high": ["赌博", "代开发票", "枪支"],
        "medium": ["加微信", "免费领取", "点击链接"],
    }

    PII_PATTERNS = {
        "phone": r"1[3-9]\d{9}",
        "id_card": r"\d{17}[\dXx]",
        "email": r"[\w.-]+@[\w.-]+\.\w+",
    }

    def moderate(self, text: str) -> dict:
        findings = []
        for level, words in self.SENSITIVE_WORDS.items():
            for w in words:
                if w in text:
                    findings.append({
                        "type": "sensitive_word", "level": level,
                        "detail": w,
                    })
        for pii_type, pattern in self.PII_PATTERNS.items():
            match = re.search(pattern, text)
            if match:
                findings.append({
                    "type": "pii", "level": "medium",
                    "detail": f"{pii_type}: {match.group()[:6]}***",
                })
        return {
            "content": text[:50],
            "findings": findings,
            "passed": len(findings) == 0,
        }


class ImageModerator:
    """图片审核引擎（模拟）"""

    MOCK_RESULTS = {
        "normal.jpg": {"label": "safe", "confidence": 0.95},
        "ad_image.jpg": {"label": "advertisement", "confidence": 0.85},
        "violent.jpg": {"label": "violence", "confidence": 0.92},
        "text_in_image.jpg": {"label": "safe", "confidence": 0.7,
                              "ocr_text": "加微信领红包"},
    }

    def moderate(self, image_name: str) -> dict:
        result = self.MOCK_RESULTS.get(image_name, {
            "label": "safe", "confidence": 0.99,
        })
        findings = []

        if result["label"] != "safe":
            findings.append({
                "type": "image_classification",
                "level": "high" if result["confidence"] > 0.8 else "medium",
                "detail": f"{result['label']} (置信度{result['confidence']})",
            })

        ocr_text = result.get("ocr_text", "")
        if ocr_text:
            text_mod = TextModerator()
            text_result = text_mod.moderate(ocr_text)
            for f in text_result["findings"]:
                f["detail"] = f"OCR提取: {f['detail']}"
                findings.append(f)

        return {
            "image": image_name,
            "findings": findings,
            "passed": len(findings) == 0,
        }


class RuleEngine:
    """审核规则引擎"""

    def evaluate(self, text_result: dict,
                 image_result: dict | None = None) -> dict:
        all_findings = list(text_result.get("findings", []))
        if image_result:
            all_findings.extend(image_result.get("findings", []))

        high = [f for f in all_findings if f.get("level") == "high"]
        medium = [f for f in all_findings if f.get("level") == "medium"]

        if high:
            decision = "reject"
            reason = f"高危内容: {high[0]['detail']}"
        elif medium:
            decision = "review"
            reason = f"需人工复审: {medium[0]['detail']}"
        elif all_findings:
            decision = "review"
            reason = "存在风险项"
        else:
            decision = "pass"
            reason = "审核通过"

        return {
            "decision": decision,
            "reason": reason,
            "high_count": len(high),
            "medium_count": len(medium),
            "total_findings": len(all_findings),
        }


class HumanReviewQueue:
    """人工复审队列"""

    def __init__(self):
        self.queue: list[dict] = []
        self._counter = 0

    def add(self, content: str, reason: str, risk_level: str = "medium"):
        self._counter += 1
        item = {
            "id": f"review_{self._counter:04d}",
            "content": content[:80],
            "reason": reason,
            "risk_level": risk_level,
            "status": "pending",
            "reviewer": None,
        }
        self.queue.append(item)
        return item["id"]

    def review(self, review_id: str, decision: str,
               reviewer: str) -> dict | None:
        for item in self.queue:
            if item["id"] == review_id:
                item["status"] = decision
                item["reviewer"] = reviewer
                return item
        return None

    def pending_count(self) -> int:
        return sum(1 for q in self.queue if q["status"] == "pending")

    def stats(self) -> dict:
        return {
            "total": len(self.queue),
            "pending": sum(1 for q in self.queue if q["status"] == "pending"),
            "approved": sum(1 for q in self.queue if q["status"] == "approved"),
            "rejected": sum(1 for q in self.queue if q["status"] == "rejected"),
        }


class ContentModerationSystem:
    """内容审核系统主控"""

    def __init__(self):
        self.text_mod = TextModerator()
        self.image_mod = ImageModerator()
        self.rule_engine = RuleEngine()
        self.review_queue = HumanReviewQueue()

    def moderate(self, content: str, image: str | None = None) -> dict:
        text_result = self.text_mod.moderate(content)
        image_result = self.image_mod.moderate(image) if image else None
        decision = self.rule_engine.evaluate(text_result, image_result)

        if decision["decision"] == "review":
            review_id = self.review_queue.add(
                content, decision["reason"])
            decision["review_id"] = review_id

        return decision


def main():
    system = ContentModerationSystem()

    print("=" * 60)
    print("AI内容审核系统演示")
    print("=" * 60)

    # 1. 文本审核
    print("\n--- 1. 文本审核 ---")
    texts = [
        "这个产品真不错，推荐给大家！",
        "加微信领取免费课程，名额有限！",
        "赌博网站推荐，稳赚不赔",
        "我的手机号是13812345678，请联系我",
        "今天天气真好，适合出去玩",
    ]

    for text in texts:
        result = system.text_mod.moderate(text)
        icon = "✅" if result["passed"] else "❌"
        findings = [f["detail"] for f in result["findings"]]
        print(f"  {icon} \"{text[:30]}\" -> "
              f"{'通过' if result['passed'] else findings}")

    # 2. 图片审核
    print("\n--- 2. 图片审核 ---")
    images = ["normal.jpg", "ad_image.jpg", "violent.jpg", "text_in_image.jpg"]
    for img in images:
        result = system.image_mod.moderate(img)
        icon = "✅" if result["passed"] else "❌"
        findings = [f["detail"] for f in result["findings"]]
        print(f"  {icon} {img} -> "
              f"{'通过' if result['passed'] else findings}")

    # 3. 完整审核流水线
    print("\n--- 3. 完整审核流水线 ---")
    cases = [
        ("好评！物流很快", None),
        ("加微信免费领取优惠券", None),
        ("赌博推荐，日赚千元", None),
        ("风景真美", "normal.jpg"),
        ("看看这个", "ad_image.jpg"),
        ("分享一下", "text_in_image.jpg"),
    ]

    for text, image in cases:
        result = system.moderate(text, image)
        icons = {"pass": "✅", "reject": "⛔", "review": "🔍"}
        icon = icons.get(result["decision"], "?")
        img_info = f" + {image}" if image else ""
        print(f"  {icon} \"{text}\"{img_info} -> "
              f"{result['decision']} ({result['reason']})")

    # 4. 人工复审
    print("\n--- 4. 人工复审队列 ---")
    stats = system.review_queue.stats()
    print(f"  队列状态: 总计{stats['total']}条, "
          f"待审{stats['pending']}条")

    for item in system.review_queue.queue:
        if item["status"] == "pending":
            decision = "approved" if "免费" in item["content"] else "rejected"
            system.review_queue.review(item["id"], decision, "审核员小张")
            print(f"  [{item['id']}] \"{item['content'][:30]}\" "
                  f"-> {decision} (审核员小张)")

    stats = system.review_queue.stats()
    print(f"\n  最终统计: 通过{stats['approved']}条, "
          f"拒绝{stats['rejected']}条, 待审{stats['pending']}条")


if __name__ == "__main__":
    main()
