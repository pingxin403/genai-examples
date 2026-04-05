"""
🧠 输出结构化控制的3层防线 — 完整演示
配套文章：《别让AI乱说话！输出结构化控制的3层防线》

演示内容：
1. 第1层：JSON模式解析（模拟）
2. 第2层：Pydantic风格的结构校验
3. 第3层：业务规则验证
4. 重试修复机制
5. 端到端Pipeline

运行方式：python structured_output_demo.py
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Union


# ============================================================
# 1. 第1层防线：JSON模式解析
# ============================================================

class JsonParser:
    """
    第1层防线：确保AI输出是合法JSON。
    生产环境中应使用 response_format={"type": "json_object"} 参数，
    这里演示当模型未开启JSON模式时的兜底解析。
    """

    @staticmethod
    def parse(raw_output: str) -> tuple[bool, dict | str]:
        """尝试从AI原始输出中提取合法JSON"""
        # 尝试1：直接解析
        try:
            data = json.loads(raw_output.strip())
            return True, data
        except json.JSONDecodeError:
            pass

        # 尝试2：提取代码块中的JSON
        code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw_output, re.DOTALL)
        if code_block:
            try:
                data = json.loads(code_block.group(1).strip())
                return True, data
            except json.JSONDecodeError:
                pass

        # 尝试3：提取花括号包裹的内容
        brace_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if brace_match:
            try:
                data = json.loads(brace_match.group(0))
                return True, data
            except json.JSONDecodeError:
                pass

        return False, "无法从输出中提取合法JSON"


# ============================================================
# 2. 第2层防线：Pydantic风格的结构校验
# ============================================================

class ProductCategory(Enum):
    ELECTRONICS = "电子产品"
    CLOTHING = "服装"
    FOOD = "食品"
    HOME = "家居"
    OTHER = "其他"


@dataclass
class ProductInfo:
    """商品信息数据模型（模拟Pydantic BaseModel）"""
    name: str
    price: float
    category: str
    brand: Optional[str] = None


class StructureValidator:
    """
    第2层防线：校验JSON数据是否符合预期结构。
    生产环境建议使用Pydantic BaseModel，这里用纯Python演示核心逻辑。
    """

    VALID_CATEGORIES = {c.value for c in ProductCategory}

    def validate(self, data: dict) -> tuple[bool, ProductInfo | str]:
        errors = []

        # 必填字段检查
        for required_field in ["name", "price", "category"]:
            if required_field not in data:
                errors.append(f"缺少必填字段: {required_field}")

        if errors:
            return False, "; ".join(errors)

        # name: 字符串，非空，长度限制
        name = data.get("name")
        if not isinstance(name, str) or not name.strip():
            errors.append("name必须是非空字符串")
        elif len(name) > 100:
            errors.append("name长度不能超过100字符")

        # price: 数字，大于0
        price = data.get("price")
        if isinstance(price, str):
            # 尝试从字符串中提取数字（如"199元" → 199）
            num_match = re.search(r"(\d+(?:\.\d+)?)", str(price))
            if num_match:
                price = float(num_match.group(1))
                data["price"] = price  # 修正
            else:
                errors.append("price无法解析为数字")
        elif not isinstance(price, (int, float)):
            errors.append("price必须是数字")
        elif price <= 0:
            errors.append("price必须大于0")

        # category: 枚举值
        category = data.get("category")
        if category not in self.VALID_CATEGORIES:
            errors.append(
                f"category必须是以下之一: {', '.join(self.VALID_CATEGORIES)}，"
                f"实际值: {category}"
            )

        # brand: 可选，字符串
        brand = data.get("brand")
        if brand is not None and not isinstance(brand, str):
            errors.append("brand必须是字符串或null")

        if errors:
            return False, "; ".join(errors)

        product = ProductInfo(
            name=str(data["name"]).strip(),
            price=float(data["price"]),
            category=str(data["category"]),
            brand=str(data["brand"]) if data.get("brand") else None,
        )
        return True, product


# ============================================================
# 3. 第3层防线：业务规则验证
# ============================================================

class BusinessRuleValidator:
    """
    第3层防线：校验数据是否符合业务逻辑。
    结构正确不代表业务合理，比如价格为0.01元的电脑。
    """

    PRICE_RANGES = {
        "电子产品": (1, 50000),
        "服装": (1, 10000),
        "食品": (0.5, 5000),
        "家居": (1, 100000),
        "其他": (0.1, 100000),
    }

    def validate(self, product: ProductInfo) -> tuple[bool, list[str]]:
        errors = []

        # 规则1：价格范围检查
        price_range = self.PRICE_RANGES.get(product.category, (0.1, 100000))
        if not (price_range[0] <= product.price <= price_range[1]):
            errors.append(
                f"价格{product.price}元超出{product.category}的合理范围"
                f"({price_range[0]}-{price_range[1]}元)"
            )

        # 规则2：名称不应包含价格信息
        if re.search(r"\d+元", product.name):
            errors.append("商品名称中不应包含价格信息")

        # 规则3：名称不应过短（可能是提取错误）
        if len(product.name) < 2:
            errors.append("商品名称过短，可能提取有误")

        # 规则4：品牌名称合理性
        if product.brand and len(product.brand) > 30:
            errors.append("品牌名称异常过长")

        return len(errors) == 0, errors


# ============================================================
# 4. 重试修复机制
# ============================================================

class RetryWithFeedback:
    """
    重试修复器：校验失败时，构造带错误反馈的重试Prompt。
    生产环境中会将错误信息追加到对话历史，让模型修正输出。
    """

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def build_fix_prompt(self, original_output: str, error_message: str) -> str:
        """构造修复Prompt"""
        return (
            f"你之前的输出存在问题：\n"
            f"原始输出：{original_output}\n"
            f"错误信息：{error_message}\n"
            f"请修正后重新输出，只返回JSON，不要添加任何其他文字。"
        )


# ============================================================
# 5. 端到端Pipeline
# ============================================================

class StructuredOutputPipeline:
    """三层防线 + 重试修复的完整Pipeline"""

    def __init__(self, max_retries: int = 2):
        self.json_parser = JsonParser()
        self.structure_validator = StructureValidator()
        self.business_validator = BusinessRuleValidator()
        self.retry = RetryWithFeedback(max_retries)
        self.max_retries = max_retries

    def process(self, raw_output: str) -> dict:
        """处理AI原始输出，经过三层防线"""
        log = {"raw": raw_output, "layers": []}

        # 第1层：JSON解析
        json_ok, json_result = self.json_parser.parse(raw_output)
        log["layers"].append({
            "layer": "JSON解析",
            "passed": json_ok,
            "detail": "合法JSON" if json_ok else json_result,
        })
        if not json_ok:
            return {"success": False, "stage": "json_parse", "error": json_result, "log": log}

        # 第2层：结构校验
        struct_ok, struct_result = self.structure_validator.validate(json_result)
        log["layers"].append({
            "layer": "结构校验",
            "passed": struct_ok,
            "detail": "结构正确" if struct_ok else struct_result,
        })
        if not struct_ok:
            return {"success": False, "stage": "structure", "error": struct_result, "log": log}

        # 第3层：业务规则
        biz_ok, biz_errors = self.business_validator.validate(struct_result)
        log["layers"].append({
            "layer": "业务规则",
            "passed": biz_ok,
            "detail": "规则通过" if biz_ok else "; ".join(biz_errors),
        })
        if not biz_ok:
            return {
                "success": False,
                "stage": "business_rule",
                "error": "; ".join(biz_errors),
                "log": log,
            }

        return {
            "success": True,
            "data": {
                "name": struct_result.name,
                "price": struct_result.price,
                "category": struct_result.category,
                "brand": struct_result.brand,
            },
            "log": log,
        }


# ============================================================
# 演示主流程
# ============================================================

def demo_json_parsing():
    print("=" * 60)
    print("1. 第1层防线：JSON模式解析")
    print("=" * 60)
    parser = JsonParser()

    test_cases = [
        (
            '{"name": "无线耳机", "price": 199, "category": "电子产品"}',
            "标准JSON",
        ),
        (
            '当然！以下是提取结果：\n{"name": "蓝牙音箱", "price": 299, "category": "电子产品"}\n希望有帮助！',
            "JSON前后有废话",
        ),
        (
            '```json\n{"name": "机械键盘", "price": 599, "category": "电子产品"}\n```',
            "Markdown代码块包裹",
        ),
        (
            "这不是JSON格式的输出",
            "完全无法解析",
        ),
    ]

    for raw, desc in test_cases:
        ok, result = parser.parse(raw)
        status = "✅ 成功" if ok else "❌ 失败"
        detail = json.dumps(result, ensure_ascii=False) if ok else result
        print(f"  {status} | {desc}")
        print(f"         → {detail}")
    print()


def demo_structure_validation():
    print("=" * 60)
    print("2. 第2层防线：Pydantic风格结构校验")
    print("=" * 60)
    validator = StructureValidator()

    test_cases = [
        (
            {"name": "无线耳机", "price": 199, "category": "电子产品", "brand": "Sony"},
            "完全正确的数据",
        ),
        (
            {"name": "蓝牙音箱", "price": "大约299元", "category": "电子产品"},
            "price是字符串（自动修复）",
        ),
        (
            {"name": "", "price": 199, "category": "电子产品"},
            "name为空",
        ),
        (
            {"price": 199, "category": "电子产品"},
            "缺少name字段",
        ),
        (
            {"name": "T恤", "price": 99, "category": "衣服"},
            "category不在枚举范围",
        ),
        (
            {"name": "数据线", "price": -10, "category": "电子产品"},
            "price为负数",
        ),
    ]

    for data, desc in test_cases:
        ok, result = validator.validate(data.copy())
        status = "✅ 通过" if ok else "❌ 拒绝"
        detail = f"{result.name}, ¥{result.price}" if ok else result
        print(f"  {status} | {desc}")
        print(f"         → {detail}")
    print()


def demo_business_rules():
    print("=" * 60)
    print("3. 第3层防线：业务规则验证")
    print("=" * 60)
    validator = BusinessRuleValidator()

    test_cases = [
        (
            ProductInfo(name="无线耳机", price=199, category="电子产品", brand="Sony"),
            "正常商品",
        ),
        (
            ProductInfo(name="笔记本电脑", price=99999, category="电子产品"),
            "价格超出合理范围",
        ),
        (
            ProductInfo(name="199元特价耳机", price=199, category="电子产品"),
            "名称包含价格信息",
        ),
        (
            ProductInfo(name="A", price=50, category="服装"),
            "名称过短",
        ),
        (
            ProductInfo(
                name="普通T恤",
                price=99,
                category="服装",
                brand="这是一个超级超级超级超级超级超级超级超级超级超级超级长的品牌名称不合理",
            ),
            "品牌名称过长",
        ),
    ]

    for product, desc in test_cases:
        ok, errors = validator.validate(product)
        status = "✅ 通过" if ok else "❌ 违规"
        detail = "业务规则全部通过" if ok else "; ".join(errors)
        print(f"  {status} | {desc}: {product.name} ¥{product.price}")
        print(f"         → {detail}")
    print()


def demo_retry_mechanism():
    print("=" * 60)
    print("4. 重试修复机制")
    print("=" * 60)
    retry = RetryWithFeedback(max_retries=2)

    original = '{"name": "耳机", "price": "免费", "category": "数码"}'
    error = "price无法解析为数字; category必须是以下之一: 电子产品, 服装, 食品, 家居, 其他"

    fix_prompt = retry.build_fix_prompt(original, error)
    print(f"  原始输出: {original}")
    print(f"  错误信息: {error}")
    print(f"  修复Prompt:")
    for line in fix_prompt.split("\n"):
        print(f"    {line}")
    print()


def demo_end_to_end():
    print("=" * 60)
    print("5. 端到端Pipeline演示")
    print("=" * 60)
    pipeline = StructuredOutputPipeline()

    scenarios = [
        (
            '{"name": "无线蓝牙耳机", "price": 199, "category": "电子产品", "brand": "Sony"}',
            "完美输出 — 三层全部通过",
        ),
        (
            '好的！结果如下：\n{"name": "机械键盘", "price": 599, "category": "电子产品"}\n希望有帮助',
            "JSON前后有废话 — 第1层兜底解析",
        ),
        (
            '{"name": "", "price": 199, "category": "电子产品"}',
            "name为空 — 第2层拦截",
        ),
        (
            '{"name": "笔记本电脑", "price": 99999, "category": "电子产品"}',
            "价格超范围 — 第3层拦截",
        ),
        (
            "这不是JSON",
            "完全无法解析 — 第1层拦截",
        ),
    ]

    for raw, desc in scenarios:
        print(f"\n  场景: {desc}")
        result = pipeline.process(raw)

        if result["success"]:
            data = result["data"]
            print(f"  结果: ✅ {data['name']} | ¥{data['price']} | {data['category']}")
        else:
            print(f"  结果: ❌ [{result['stage']}] {result['error']}")

        # 打印每层状态
        for layer in result["log"]["layers"]:
            icon = "✅" if layer["passed"] else "❌"
            print(f"    {icon} {layer['layer']}: {layer['detail']}")
    print()


def print_summary():
    print("=" * 60)
    print("三层防线要点总结")
    print("=" * 60)
    print()
    print(f"  {'防线层级':<14} {'解决的问题':<20} {'关键实现'}")
    print("  " + "-" * 60)
    rows = [
        ("第1层: JSON模式", "输出不是合法JSON", "response_format + 兜底正则提取"),
        ("第2层: 结构校验", "字段缺失/类型错误", "Pydantic模型 + 自定义validator"),
        ("第3层: 业务规则", "数据合法但不合理", "规则引擎 + 范围/关联校验"),
        ("重试修复", "校验失败的恢复", "错误反馈 + 最大重试次数"),
    ]
    for layer, problem, impl in rows:
        print(f"  {layer:<12} {problem:<18} {impl}")
    print()


if __name__ == "__main__":
    print()
    print("🧠 输出结构化控制的3层防线 — 完整演示")
    print("=" * 60)
    print()

    demo_json_parsing()
    demo_structure_validation()
    demo_business_rules()
    demo_retry_mechanism()
    demo_end_to_end()
    print_summary()

    print("✅ 演示完成！生产环境中请替换模拟逻辑为真实LLM API调用。")
