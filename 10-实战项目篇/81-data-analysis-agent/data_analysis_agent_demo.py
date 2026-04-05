"""
数据分析Agent演示：NL2SQL + 工具调用 + 可视化
对应文章：81-数据分析Agent-NL2SQL加工具调用加可视化
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field


@dataclass
class TableSchema:
    name: str
    columns: list[dict]
    description: str = ""


class SchemaManager:
    """数据库Schema管理"""

    def __init__(self):
        self.tables: dict[str, TableSchema] = {}

    def register(self, table: TableSchema):
        self.tables[table.name] = table

    def get_context(self, query: str) -> str:
        relevant = []
        for t in self.tables.values():
            col_names = [c["name"] for c in t.columns]
            keywords = col_names + [t.name] + t.description.split()
            if any(kw in query for kw in keywords):
                relevant.append(t)
        targets = relevant or list(self.tables.values())
        lines = ["可用表结构："]
        for t in targets:
            cols = ", ".join(f"{c['name']}({c['type']})" for c in t.columns)
            lines.append(f"  {t.name} ({t.description}): {cols}")
        return "\n".join(lines)


class SQLSafetyChecker:
    """SQL安全检查"""

    FORBIDDEN = [
        r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE)\b",
        r"\b(GRANT|REVOKE)\b",
        r";\s*\w",
    ]

    def check(self, sql: str) -> dict:
        sql_upper = sql.upper().strip()
        for pattern in self.FORBIDDEN:
            if re.search(pattern, sql_upper):
                return {"safe": False, "reason": f"包含禁止操作",
                        "sql": sql}
        if "LIMIT" not in sql_upper:
            sql = sql.rstrip(";") + " LIMIT 1000"
        return {"safe": True, "sql": sql, "reason": "通过"}


class QueryExecutor:
    """查询执行器（SQLite内存数据库）"""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._init_data()

    def _init_data(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE orders (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                channel TEXT,
                amount REAL,
                order_date TEXT,
                status TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                name TEXT,
                city TEXT,
                register_date TEXT
            )
        """)
        orders = [
            (1, "u1", "直播", 299.0, "2024-10-01", "completed"),
            (2, "u2", "搜索", 159.0, "2024-10-02", "completed"),
            (3, "u1", "直播", 499.0, "2024-10-03", "completed"),
            (4, "u3", "推荐", 89.0, "2024-10-04", "refunded"),
            (5, "u2", "搜索", 1299.0, "2024-10-05", "completed"),
            (6, "u4", "直播", 399.0, "2024-10-06", "completed"),
            (7, "u5", "推荐", 199.0, "2024-10-07", "completed"),
            (8, "u3", "搜索", 599.0, "2024-10-08", "completed"),
        ]
        cur.executemany(
            "INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
        users = [
            ("u1", "张三", "北京", "2024-01-01"),
            ("u2", "李四", "上海", "2024-02-15"),
            ("u3", "王五", "广州", "2024-03-20"),
            ("u4", "赵六", "深圳", "2024-04-10"),
            ("u5", "钱七", "杭州", "2024-05-05"),
        ]
        cur.executemany("INSERT INTO users VALUES (?,?,?,?)", users)
        self.conn.commit()

    def execute(self, sql: str) -> dict:
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return {"success": True, "columns": columns,
                    "rows": rows, "row_count": len(rows)}
        except Exception as e:
            return {"success": False, "error": str(e),
                    "columns": [], "rows": []}


class ResultInterpreter:
    """查询结果解释"""

    def interpret(self, query: str, result: dict) -> dict:
        if not result["success"]:
            return {"summary": f"查询失败: {result.get('error', '未知错误')}",
                    "chart_type": "none"}

        rows = result["rows"]
        columns = result["columns"]
        summary = f"查询返回{len(rows)}条记录，包含字段: {', '.join(columns)}。"

        if len(rows) > 0 and len(columns) >= 2:
            # 数值汇总
            for i, col in enumerate(columns):
                values = [r[i] for r in rows if isinstance(r[i], (int, float))]
                if values:
                    summary += f"\n  {col}: 总计={sum(values):.1f}, 平均={sum(values)/len(values):.1f}"

        chart_type = self._suggest_chart(columns, rows)
        return {
            "summary": summary,
            "chart_type": chart_type,
            "preview": rows[:5],
        }

    def _suggest_chart(self, columns: list, rows: list) -> str:
        if any("date" in c.lower() or "time" in c.lower() for c in columns):
            return "line（折线图）"
        if len(rows) <= 10:
            return "bar（柱状图）"
        return "table（表格）"


class DataAnalysisAgent:
    """数据分析Agent主控"""

    def __init__(self):
        self.schema = SchemaManager()
        self.checker = SQLSafetyChecker()
        self.executor = QueryExecutor()
        self.interpreter = ResultInterpreter()
        self._register_schemas()

    def _register_schemas(self):
        self.schema.register(TableSchema(
            "orders",
            [{"name": "id", "type": "int"},
             {"name": "user_id", "type": "text"},
             {"name": "channel", "type": "text"},
             {"name": "amount", "type": "real"},
             {"name": "order_date", "type": "date"},
             {"name": "status", "type": "text"}],
            "订单 销售 渠道 金额",
        ))
        self.schema.register(TableSchema(
            "users",
            [{"name": "id", "type": "text"},
             {"name": "name", "type": "text"},
             {"name": "city", "type": "text"},
             {"name": "register_date", "type": "date"}],
            "用户 城市 注册",
        ))

    def query(self, natural_language: str, mock_sql: str) -> dict:
        # 1. Schema上下文
        context = self.schema.get_context(natural_language)

        # 2. 安全检查
        safety = self.checker.check(mock_sql)
        if not safety["safe"]:
            return {"status": "blocked", "reason": safety["reason"]}

        # 3. 执行查询
        result = self.executor.execute(safety["sql"])

        # 4. 结果解释
        interpretation = self.interpreter.interpret(natural_language, result)

        return {
            "status": "success",
            "sql": safety["sql"],
            "result": result,
            "interpretation": interpretation,
        }


def main():
    agent = DataAnalysisAgent()

    print("=" * 60)
    print("数据分析Agent演示")
    print("=" * 60)

    # 1. Schema信息
    print("\n--- 1. Schema上下文 ---")
    ctx = agent.schema.get_context("销售渠道")
    print(f"  {ctx}")

    # 2. SQL安全检查
    print("\n--- 2. SQL安全检查 ---")
    test_sqls = [
        ("SELECT * FROM orders", "只读查询"),
        ("SELECT channel, SUM(amount) FROM orders GROUP BY channel", "聚合查询"),
        ("DELETE FROM orders WHERE id=1", "删除操作"),
        ("DROP TABLE orders", "删表操作"),
        ("SELECT * FROM orders; DROP TABLE users", "多语句注入"),
    ]
    for sql, desc in test_sqls:
        result = agent.checker.check(sql)
        icon = "✅" if result["safe"] else "⛔"
        print(f"  {icon} [{desc}] {sql[:50]} -> {result['reason']}")

    # 3. 完整查询流程
    print("\n--- 3. 自然语言查询 ---")
    queries = [
        ("各渠道的销售额是多少",
         "SELECT channel, SUM(amount) as total_amount, COUNT(*) as order_count "
         "FROM orders WHERE status='completed' GROUP BY channel"),
        ("每天的订单量",
         "SELECT order_date, COUNT(*) as cnt, SUM(amount) as total "
         "FROM orders GROUP BY order_date ORDER BY order_date"),
        ("哪个城市的用户最多",
         "SELECT city, COUNT(*) as user_count FROM users GROUP BY city "
         "ORDER BY user_count DESC"),
    ]

    for nl, sql in queries:
        print(f"\n  问: {nl}")
        result = agent.query(nl, sql)
        if result["status"] == "success":
            interp = result["interpretation"]
            print(f"  SQL: {result['sql'][:70]}")
            print(f"  {interp['summary']}")
            print(f"  推荐图表: {interp['chart_type']}")
            if interp["preview"]:
                cols = result["result"]["columns"]
                print(f"  预览: {cols}")
                for row in interp["preview"][:3]:
                    print(f"    {list(row)}")
        else:
            print(f"  ⛔ {result['reason']}")

    # 4. 危险查询拦截
    print("\n--- 4. 危险查询拦截 ---")
    result = agent.query("删除所有订单", "DELETE FROM orders")
    print(f"  问: 删除所有订单")
    print(f"  结果: {result['status']} - {result.get('reason', '')}")


if __name__ == "__main__":
    main()
