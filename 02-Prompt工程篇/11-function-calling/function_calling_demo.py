"""
🔁 函数调用（Function Calling）工程化落地 — 完整演示
配套文章：《函数调用（Function Calling）的工程化落地》

演示内容：
1. 工具Schema设计
2. 参数校验
3. 错误处理与重试
4. 超时熔断（CircuitBreaker）
5. 端到端Function Calling流程

运行方式：python function_calling_demo.py
"""

import json
import re
import time
from dataclasses import dataclass, field


# ============================================================
# 1. 工具Schema设计
# ============================================================

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": (
                "根据订单ID查询订单状态和详情。"
                "仅支持精确的订单ID查询，不支持模糊搜索。"
                "如果用户没有提供具体订单ID，应先询问用户。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID，格式为ORD-开头加9位数字，如ORD-202401001",
                        "pattern": "^ORD-\\d{9}$",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": (
                "取消指定订单。此操作不可逆，调用前必须与用户确认。"
                "仅支持状态为'待发货'的订单取消。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID，格式为ORD-开头加9位数字",
                        "pattern": "^ORD-\\d{9}$",
                    },
                    "reason": {
                        "type": "string",
                        "description": "取消原因，不超过200字",
                        "maxLength": 200,
                    },
                },
                "required": ["order_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_logistics",
            "description": "查询订单的物流信息，包括快递公司、运单号和物流轨迹。",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID，格式为ORD-开头加9位数字",
                        "pattern": "^ORD-\\d{9}$",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
]


# ============================================================
# 2. 参数校验器
# ============================================================

class ParameterValidator:
    """对模型生成的参数做严格校验，不信任任何模型输出"""

    VALIDATORS = {
        "query_order": {
            "order_id": {
                "type": str,
                "pattern": r"^ORD-\d{9}$",
                "required": True,
            }
        },
        "cancel_order": {
            "order_id": {
                "type": str,
                "pattern": r"^ORD-\d{9}$",
                "required": True,
            },
            "reason": {
                "type": str,
                "max_length": 200,
                "required": True,
            },
        },
        "query_logistics": {
            "order_id": {
                "type": str,
                "pattern": r"^ORD-\d{9}$",
                "required": True,
            }
        },
    }

    def validate(self, function_name: str, params: dict) -> tuple[bool, str]:
        rules = self.VALIDATORS.get(function_name)
        if rules is None:
            return False, f"未知的工具: {function_name}"

        for field_name, rule in rules.items():
            value = params.get(field_name)

            # 必填检查
            if rule.get("required") and value is None:
                return False, f"缺少必填参数: {field_name}"

            if value is None:
                continue

            # 类型检查
            if not isinstance(value, rule["type"]):
                return False, f"参数类型错误: {field_name} 应为 {rule['type'].__name__}"

            # 正则检查
            if rule.get("pattern") and not re.match(rule["pattern"], str(value)):
                return False, f"参数格式错误: {field_name}，期望格式: {rule['pattern']}"

            # 长度检查
            if rule.get("max_length") and len(str(value)) > rule["max_length"]:
                return False, f"参数过长: {field_name}，最大长度: {rule['max_length']}"

        return True, "校验通过"


# ============================================================
# 3. 模拟工具实现（下游服务）
# ============================================================

# 模拟订单数据库
MOCK_ORDERS = {
    "ORD-202401001": {"status": "已发货", "amount": 299.0, "product": "无线耳机"},
    "ORD-202401002": {"status": "待发货", "amount": 1599.0, "product": "机械键盘"},
    "ORD-202401003": {"status": "已完成", "amount": 89.0, "product": "数据线"},
}


def mock_query_order(order_id: str) -> dict:
    """模拟查询订单"""
    order = MOCK_ORDERS.get(order_id)
    if order is None:
        raise ValueError(f"订单不存在: {order_id}")
    return {"order_id": order_id, **order}


def mock_cancel_order(order_id: str, reason: str) -> dict:
    """模拟取消订单"""
    order = MOCK_ORDERS.get(order_id)
    if order is None:
        raise ValueError(f"订单不存在: {order_id}")
    if order["status"] != "待发货":
        raise ValueError(f"订单状态为'{order['status']}'，无法取消")
    return {"order_id": order_id, "cancelled": True, "reason": reason}


def mock_query_logistics(order_id: str) -> dict:
    """模拟查询物流"""
    order = MOCK_ORDERS.get(order_id)
    if order is None:
        raise ValueError(f"订单不存在: {order_id}")
    if order["status"] == "待发货":
        raise ValueError("订单尚未发货，暂无物流信息")
    return {
        "order_id": order_id,
        "carrier": "顺丰速运",
        "tracking_no": "SF1234567890",
        "status": "运输中",
    }


def mock_slow_service(order_id: str) -> dict:
    """模拟慢服务（用于演示超时）"""
    time.sleep(0.3)  # 模拟延迟
    return {"order_id": order_id, "data": "slow response"}


TOOL_REGISTRY = {
    "query_order": mock_query_order,
    "cancel_order": mock_cancel_order,
    "query_logistics": mock_query_logistics,
}


# ============================================================
# 4. 工具执行器（带错误处理和重试）
# ============================================================

class ToolExecutor:
    """带错误处理和重试限制的工具调用执行器"""

    def __init__(self, max_retries: int = 2, timeout: float = 5.0):
        self.max_retries = max_retries
        self.timeout = timeout

    def execute(self, function_name: str, params: dict) -> dict:
        func = TOOL_REGISTRY.get(function_name)
        if func is None:
            return {"success": False, "error": f"未注册的工具: {function_name}"}

        for attempt in range(self.max_retries + 1):
            try:
                result = func(**params)
                return {"success": True, "data": result, "attempts": attempt + 1}
            except ValueError as e:
                # 业务错误不重试
                return {"success": False, "error": str(e), "attempts": attempt + 1}
            except TimeoutError:
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": "服务超时，请稍后重试",
                        "attempts": attempt + 1,
                    }
            except Exception as e:
                if attempt == self.max_retries:
                    return {
                        "success": False,
                        "error": f"服务异常: {type(e).__name__}",
                        "attempts": attempt + 1,
                    }
        return {"success": False, "error": "重试次数已用尽"}


# ============================================================
# 5. 熔断器（CircuitBreaker）
# ============================================================

class CircuitBreaker:
    """
    熔断器：连续失败超过阈值时自动熔断，防止级联故障。

    状态流转：
    CLOSED（正常）→ 连续失败达阈值 → OPEN（熔断）
    OPEN → 超过恢复时间 → HALF_OPEN（试探）
    HALF_OPEN → 调用成功 → CLOSED
    HALF_OPEN → 调用失败 → OPEN
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = 0.0

    def call(self, func, *args, **kwargs):
        # 熔断状态检查
        if self.state == "OPEN":
            elapsed = time.time() - self.last_failure_time
            if elapsed > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                return {
                    "success": False,
                    "error": f"服务熔断中，{self.recovery_timeout - elapsed:.0f}秒后重试",
                    "circuit_state": "OPEN",
                }

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return {**result, "circuit_state": self.state}
        except Exception as e:
            self._on_failure()
            return {
                "success": False,
                "error": str(e),
                "circuit_state": self.state,
            }

    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
        }


# ============================================================
# 6. 端到端Function Calling编排器
# ============================================================

class FunctionCallingOrchestrator:
    """端到端的Function Calling编排：校验 → 确认 → 执行 → 格式化"""

    # 需要二次确认的危险操作
    DANGEROUS_OPERATIONS = {"cancel_order", "delete_account"}

    def __init__(self):
        self.validator = ParameterValidator()
        self.executor = ToolExecutor(max_retries=2)
        self.breakers: dict[str, CircuitBreaker] = {}
        self.call_log: list[dict] = []

    def handle_tool_call(self, function_name: str, params: dict) -> dict:
        """处理一次完整的工具调用"""
        log_entry = {
            "function": function_name,
            "params": params,
            "timestamp": time.time(),
        }

        # Step 1: 参数校验
        valid, message = self.validator.validate(function_name, params)
        if not valid:
            log_entry["result"] = "validation_failed"
            log_entry["error"] = message
            self.call_log.append(log_entry)
            return {"success": False, "stage": "validation", "error": message}

        # Step 2: 危险操作确认
        if function_name in self.DANGEROUS_OPERATIONS:
            log_entry["requires_confirmation"] = True
            # 实际项目中这里会暂停并等待用户确认
            # 演示中直接标记
            return {
                "success": False,
                "stage": "confirmation",
                "message": f"操作'{function_name}'需要用户确认后才能执行",
                "params": params,
            }

        # Step 3: 熔断检查 + 执行
        breaker = self._get_breaker(function_name)
        result = breaker.call(self.executor.execute, function_name, params)

        log_entry["result"] = "success" if result.get("success") else "failed"
        self.call_log.append(log_entry)
        return result

    def _get_breaker(self, function_name: str) -> CircuitBreaker:
        if function_name not in self.breakers:
            self.breakers[function_name] = CircuitBreaker(
                failure_threshold=3, recovery_timeout=30
            )
        return self.breakers[function_name]

    def get_call_stats(self) -> dict:
        total = len(self.call_log)
        success = sum(1 for log in self.call_log if log.get("result") == "success")
        return {
            "total_calls": total,
            "success_calls": success,
            "success_rate": f"{success / max(total, 1) * 100:.1f}%",
        }


# ============================================================
# 演示主流程
# ============================================================

def demo_schema_design():
    print("=" * 60)
    print("1. 工具Schema设计")
    print("=" * 60)
    for schema in TOOL_SCHEMAS:
        func = schema["function"]
        print(f"\n  工具: {func['name']}")
        print(f"  描述: {func['description'][:60]}...")
        params = func["parameters"]["properties"]
        for pname, pdef in params.items():
            print(f"  参数: {pname} ({pdef['type']}) - {pdef['description'][:40]}...")
    print()


def demo_parameter_validation():
    print("=" * 60)
    print("2. 参数校验")
    print("=" * 60)
    validator = ParameterValidator()

    test_cases = [
        ("query_order", {"order_id": "ORD-202401001"}, "正确的订单ID"),
        ("query_order", {"order_id": "最近的"}, "自然语言当参数"),
        ("query_order", {"order_id": "12345"}, "格式不对的ID"),
        ("query_order", {}, "缺少必填参数"),
        ("cancel_order", {"order_id": "ORD-202401002", "reason": "不想要了"}, "正确的取消请求"),
        ("cancel_order", {"order_id": "ORD-202401002"}, "缺少取消原因"),
        ("unknown_tool", {"a": 1}, "未知工具"),
    ]

    for func_name, params, desc in test_cases:
        valid, msg = validator.validate(func_name, params)
        status = "✅ 通过" if valid else "❌ 拒绝"
        print(f"  {status} | {desc}: {func_name}({json.dumps(params, ensure_ascii=False)}) → {msg}")
    print()


def demo_tool_execution():
    print("=" * 60)
    print("3. 工具执行（带错误处理和重试）")
    print("=" * 60)
    executor = ToolExecutor(max_retries=2)

    test_calls = [
        ("query_order", {"order_id": "ORD-202401001"}, "查询存在的订单"),
        ("query_order", {"order_id": "ORD-999999999"}, "查询不存在的订单"),
        ("cancel_order", {"order_id": "ORD-202401002", "reason": "不想要了"}, "取消待发货订单"),
        ("cancel_order", {"order_id": "ORD-202401001", "reason": "不想要了"}, "取消已发货订单"),
        ("query_logistics", {"order_id": "ORD-202401001"}, "查询物流"),
    ]

    for func_name, params, desc in test_calls:
        result = executor.execute(func_name, params)
        status = "✅" if result["success"] else "❌"
        detail = result.get("data", result.get("error", ""))
        print(f"  {status} {desc}: {detail}")
    print()


def demo_circuit_breaker():
    print("=" * 60)
    print("4. 熔断器演示")
    print("=" * 60)
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=2)

    def failing_call():
        raise ConnectionError("服务不可用")

    def success_call():
        return {"success": True, "data": "ok"}

    # 连续失败触发熔断
    for i in range(4):
        result = breaker.call(failing_call)
        status = breaker.get_status()
        print(f"  第{i + 1}次失败调用 → 状态: {status['state']}, 失败计数: {status['failure_count']}")

    # 熔断状态下直接拒绝
    result = breaker.call(success_call)
    print(f"  熔断中调用 → {result.get('error', 'N/A')}")

    # 等待恢复
    print(f"  等待恢复（{breaker.recovery_timeout}秒）...")
    time.sleep(breaker.recovery_timeout + 0.1)

    # 半开状态试探成功
    result = breaker.call(success_call)
    status = breaker.get_status()
    print(f"  恢复后调用 → 状态: {status['state']}, 结果: 成功")
    print()


def demo_end_to_end():
    print("=" * 60)
    print("5. 端到端Function Calling流程")
    print("=" * 60)
    orchestrator = FunctionCallingOrchestrator()

    scenarios = [
        {
            "desc": "用户: '帮我查一下订单ORD-202401001的状态'",
            "function": "query_order",
            "params": {"order_id": "ORD-202401001"},
        },
        {
            "desc": "用户: '查一下最近的订单'（模型传了自然语言）",
            "function": "query_order",
            "params": {"order_id": "最近的"},
        },
        {
            "desc": "用户: '取消订单ORD-202401002'（危险操作）",
            "function": "cancel_order",
            "params": {"order_id": "ORD-202401002", "reason": "不想要了"},
        },
        {
            "desc": "用户: '查一下ORD-202401001的物流'",
            "function": "query_logistics",
            "params": {"order_id": "ORD-202401001"},
        },
    ]

    for scenario in scenarios:
        print(f"\n  场景: {scenario['desc']}")
        result = orchestrator.handle_tool_call(scenario["function"], scenario["params"])

        if result.get("success"):
            print(f"  结果: ✅ {result.get('data', '')}")
        elif result.get("stage") == "validation":
            print(f"  结果: ❌ 参数校验失败 → {result['error']}")
        elif result.get("stage") == "confirmation":
            print(f"  结果: ⚠️ {result['message']}")
        else:
            print(f"  结果: ❌ {result.get('error', '未知错误')}")

    # 调用统计
    stats = orchestrator.get_call_stats()
    print(f"\n  调用统计: 总计{stats['total_calls']}次, 成功率{stats['success_rate']}")
    print()


def print_summary():
    print("=" * 60)
    print("工程化要点总结")
    print("=" * 60)
    print()
    print(f"  {'环节':<14} {'核心原则':<24} {'关键实现'}")
    print("  " + "-" * 64)
    rows = [
        ("Schema设计", "description写清边界", "格式约束+负面说明"),
        ("参数校验", "不信任模型输出", "正则+类型+必填检查"),
        ("错误处理", "区分业务错误和系统错误", "业务错误不重试"),
        ("重试限制", "防止无限重试", "最大重试次数+降级"),
        ("超时熔断", "防止级联故障", "CircuitBreaker模式"),
        ("危险操作", "不可逆操作需确认", "二次确认+审计日志"),
    ]
    for stage, principle, impl in rows:
        print(f"  {stage:<12} {principle:<22} {impl}")
    print()


if __name__ == "__main__":
    print()
    print("🔁 函数调用（Function Calling）工程化落地 — 完整演示")
    print("=" * 60)
    print()

    demo_schema_design()
    demo_parameter_validation()
    demo_tool_execution()
    demo_circuit_breaker()
    demo_end_to_end()
    print_summary()

    print("✅ 演示完成！生产环境中请替换mock实现为真实API调用。")
