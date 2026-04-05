"""
代码生成助手演示：上下文管理 + 代码安全审查
对应文章：78-代码生成助手上下文管理加代码安全审查
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class CodeFile:
    path: str
    language: str
    content: str
    functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


class CodebaseIndex:
    """代码库索引"""

    def __init__(self):
        self.files: dict[str, CodeFile] = {}

    def index_file(self, path: str, content: str, language: str = "python"):
        functions = self._extract_functions(content, language)
        imports = self._extract_imports(content, language)
        self.files[path] = CodeFile(path, language, content, functions, imports)

    def search_context(self, query: str, max_files: int = 3) -> list[CodeFile]:
        scored = []
        query_lower = query.lower()
        for f in self.files.values():
            score = sum(1 for fn in f.functions if query_lower in fn.lower())
            score += sum(1 for imp in f.imports if query_lower in imp.lower())
            # 路径匹配
            if query_lower in f.path.lower():
                score += 2
            if score > 0:
                scored.append((f, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [f for f, _ in scored[:max_files]]

    def _extract_functions(self, content: str, language: str) -> list[str]:
        if language == "python":
            return re.findall(r'def\s+(\w+)\s*\(', content)
        elif language == "java":
            return re.findall(r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\(', content)
        return []

    def _extract_imports(self, content: str, language: str) -> list[str]:
        if language == "python":
            return re.findall(r'(?:from|import)\s+([\w.]+)', content)
        elif language == "java":
            return re.findall(r'import\s+([\w.]+)', content)
        return []


class SecurityScanner:
    """代码安全扫描器"""

    RULES = [
        {
            "id": "SQL_INJECTION", "severity": "high",
            "pattern": r'["\'].*%s.*["\'].*execute|\.format\(.*(?:SELECT|INSERT|UPDATE|DELETE)',
            "message": "疑似SQL注入：请使用参数化查询",
        },
        {
            "id": "HARDCODED_SECRET", "severity": "high",
            "pattern": r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{3,}["\']',
            "message": "硬编码密钥：请使用环境变量或密钥管理服务",
        },
        {
            "id": "EVAL_USAGE", "severity": "medium",
            "pattern": r'\beval\s*\(|\bexec\s*\(',
            "message": "eval/exec存在代码注入风险",
        },
        {
            "id": "BARE_EXCEPT", "severity": "low",
            "pattern": r'except\s*:',
            "message": "空except会吞掉所有异常，建议指定异常类型",
        },
    ]

    def scan(self, code: str) -> list[dict]:
        findings = []
        lines = code.split("\n")
        for rule in self.RULES:
            for i, line in enumerate(lines, 1):
                if re.search(rule["pattern"], line, re.IGNORECASE):
                    findings.append({
                        "rule_id": rule["id"],
                        "severity": rule["severity"],
                        "line": i,
                        "code": line.strip()[:60],
                        "message": rule["message"],
                    })
        return findings


class ContextBuilder:
    """上下文构建器"""

    SECURITY_PROMPT = """安全规范：
- 数据库查询必须使用参数化查询，禁止字符串拼接
- 禁止硬编码密钥、密码、Token
- 禁止使用eval/exec处理用户输入
- 异常处理必须指定具体异常类型"""

    def __init__(self, index: CodebaseIndex):
        self.index = index

    def build_prompt(self, user_request: str) -> dict:
        relevant = self.index.search_context(user_request)
        context_parts = []
        for f in relevant:
            context_parts.append(f"# {f.path}\n{f.content[:500]}")

        return {
            "system": self.SECURITY_PROMPT,
            "context": "\n\n".join(context_parts) if context_parts else "无相关上下文",
            "request": user_request,
            "context_files": [f.path for f in relevant],
        }


class CodeAssistant:
    """代码生成助手主控"""

    def __init__(self):
        self.index = CodebaseIndex()
        self.scanner = SecurityScanner()
        self.context_builder = ContextBuilder(self.index)

    def generate_and_review(self, request: str, mock_code: str) -> dict:
        # 1. 构建上下文
        prompt = self.context_builder.build_prompt(request)

        # 2. 模拟LLM生成（实际项目中调用LLM API）
        generated_code = mock_code

        # 3. 安全审查
        findings = self.scanner.scan(generated_code)

        # 4. 判定结果
        high_issues = [f for f in findings if f["severity"] == "high"]
        blocked = len(high_issues) > 0

        return {
            "request": request,
            "context_files": prompt["context_files"],
            "generated_code": generated_code,
            "findings": findings,
            "blocked": blocked,
            "summary": f"发现{len(findings)}个问题，"
                       f"其中高危{len(high_issues)}个"
                       + ("，已阻断" if blocked else ""),
        }


def main():
    assistant = CodeAssistant()

    print("=" * 60)
    print("代码生成助手演示")
    print("=" * 60)

    # 1. 索引代码库
    print("\n--- 1. 代码库索引 ---")
    sample_files = {
        "src/models/user.py": (
            "from sqlalchemy import Column, String\n"
            "class User:\n"
            "    def get_user(self, user_id):\n"
            "        return self.session.query(User).filter_by(id=user_id).first()\n"
            "    def create_user(self, name, email):\n"
            "        user = User(name=name, email=email)\n"
            "        self.session.add(user)\n"
        ),
        "src/services/auth.py": (
            "import hashlib\n"
            "import os\n"
            "class AuthService:\n"
            "    def hash_password(self, password):\n"
            "        salt = os.urandom(32)\n"
            "        return hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)\n"
            "    def verify_token(self, token):\n"
            "        return self.jwt_decode(token)\n"
        ),
        "src/api/routes.py": (
            "from flask import Flask, request, jsonify\n"
            "def get_users():\n"
            "    return jsonify(user_service.list_users())\n"
            "def create_user():\n"
            "    data = request.get_json()\n"
            "    return jsonify(user_service.create_user(data))\n"
        ),
    }

    for path, content in sample_files.items():
        assistant.index.index_file(path, content)
        f = assistant.index.files[path]
        print(f"  {path}: {len(f.functions)}个函数, {len(f.imports)}个导入")

    # 2. 上下文检索
    print("\n--- 2. 上下文检索 ---")
    queries = ["user", "auth", "api"]
    for q in queries:
        results = assistant.index.search_context(q)
        files = [r.path for r in results]
        print(f"  查询'{q}' -> {files}")

    # 3. 安全扫描演示
    print("\n--- 3. 安全扫描 ---")
    unsafe_codes = [
        ("SQL注入", 'cursor.execute("SELECT * FROM users WHERE id=%s" % user_id)'),
        ("硬编码密钥", 'api_key = "sk-1234567890abcdef"'),
        ("eval使用", 'result = eval(user_input)'),
        ("空except", 'try:\n    do_something()\nexcept:\n    pass'),
        ("安全代码", 'cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))'),
    ]

    for name, code in unsafe_codes:
        findings = assistant.scanner.scan(code)
        if findings:
            for f in findings:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[f["severity"]]
                print(f"  {severity_icon} [{name}] {f['rule_id']}: {f['message']}")
        else:
            print(f"  ✅ [{name}] 未发现安全问题")

    # 4. 完整流水线
    print("\n--- 4. 生成+审查流水线 ---")
    test_cases = [
        (
            "写一个查询用户的函数",
            'def query_user(name):\n    sql = "SELECT * FROM users WHERE name=\'%s\'" % name\n    cursor.execute(sql)\n    return cursor.fetchall()',
        ),
        (
            "写一个安全的数据库查询",
            "def query_user(name):\n    cursor.execute('SELECT * FROM users WHERE name=?', (name,))\n    return cursor.fetchall()",
        ),
    ]

    for request_text, mock_code in test_cases:
        print(f"\n  请求: {request_text}")
        result = assistant.generate_and_review(request_text, mock_code)
        print(f"  上下文: {result['context_files']}")
        print(f"  结果: {result['summary']}")
        if result["blocked"]:
            print(f"  ⛔ 代码被阻断，需要修复安全问题")
        else:
            print(f"  ✅ 代码通过安全审查")


if __name__ == "__main__":
    main()
