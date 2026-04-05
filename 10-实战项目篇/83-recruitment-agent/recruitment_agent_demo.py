"""
招聘助手Agent演示：简历解析 + 匹配 + 面试邀约
对应文章：83-招聘助手Agent简历解析加匹配加面试邀约
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ResumeData:
    name: str = ""
    email: str = ""
    phone: str = ""
    education: str = ""
    years_exp: int = 0
    skills: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class JobRequirement:
    title: str
    required_skills: list[str]
    min_experience: int
    min_education: str
    preferred_skills: list[str] = field(default_factory=list)
    description: str = ""


class ResumeParser:
    """简历解析器"""

    SKILL_KEYWORDS = [
        "Python", "Java", "Go", "JavaScript", "TypeScript",
        "React", "Vue", "Docker", "Kubernetes", "AWS",
        "MySQL", "Redis", "Kafka", "LangChain", "RAG",
        "机器学习", "深度学习", "NLP", "大模型", "微调",
    ]

    def parse(self, text: str) -> ResumeData:
        resume = ResumeData(raw_text=text)
        resume.name = self._extract_name(text)
        resume.email = self._extract_email(text)
        resume.phone = self._extract_phone(text)
        resume.education = self._extract_education(text)
        resume.years_exp = self._extract_experience(text)
        resume.skills = self._extract_skills(text)
        resume.projects = self._extract_projects(text)
        return resume

    def _extract_name(self, text: str) -> str:
        lines = text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            if len(first_line) <= 10:
                return first_line
        return "未知"

    def _extract_email(self, text: str) -> str:
        match = re.search(r"[\w.-]+@[\w.-]+\.\w+", text)
        return match.group() if match else ""

    def _extract_phone(self, text: str) -> str:
        match = re.search(r"1[3-9]\d{9}", text)
        return match.group() if match else ""

    def _extract_education(self, text: str) -> str:
        for level in ["博士", "硕士", "本科", "大专"]:
            if level in text:
                return level
        return "未知"

    def _extract_experience(self, text: str) -> int:
        match = re.search(r"(\d+)\s*年.*(?:经验|工作)", text)
        if match:
            return int(match.group(1))
        match = re.search(r"(?:经验|工作).*?(\d+)\s*年", text)
        return int(match.group(1)) if match else 0

    def _extract_skills(self, text: str) -> list[str]:
        found = []
        text_lower = text.lower()
        for skill in self.SKILL_KEYWORDS:
            if skill.lower() in text_lower:
                found.append(skill)
        return found

    def _extract_projects(self, text: str) -> list[str]:
        projects = []
        for line in text.split("\n"):
            if "项目" in line and len(line.strip()) > 5:
                projects.append(line.strip()[:50])
        return projects[:5]


class MatchingEngine:
    """匹配引擎"""

    EDUCATION_LEVELS = {"高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}

    SKILL_SYNONYMS = {
        "python": ["python3", "python编程", "py"],
        "java": ["java8", "java11", "jdk", "spring"],
        "react": ["reactjs", "react.js"],
        "kubernetes": ["k8s"],
        "大模型": ["llm", "gpt", "chatgpt"],
    }

    def match(self, resume: ResumeData, job: JobRequirement) -> dict:
        skill_score = self._skill_match(
            resume.skills, job.required_skills, job.preferred_skills)
        exp_score = self._experience_match(resume.years_exp, job.min_experience)
        edu_score = self._education_match(resume.education, job.min_education)

        overall = skill_score * 0.4 + exp_score * 0.35 + edu_score * 0.25
        return {
            "name": resume.name,
            "skill_score": round(skill_score, 2),
            "experience_score": round(exp_score, 2),
            "education_score": round(edu_score, 2),
            "overall": round(overall, 2),
            "recommendation": self._recommend(overall),
            "matched_skills": self._get_matched(resume.skills, job.required_skills),
            "missing_skills": self._get_missing(resume.skills, job.required_skills),
        }

    def _skill_match(self, resume_skills, required, preferred) -> float:
        r_norm = {s.lower() for s in resume_skills}
        req_norm = {s.lower() for s in required}
        pref_norm = {s.lower() for s in preferred}

        req_match = len(r_norm & req_norm) / len(req_norm) if req_norm else 0
        pref_match = len(r_norm & pref_norm) / len(pref_norm) if pref_norm else 0
        return req_match * 0.7 + pref_match * 0.3

    def _experience_match(self, actual: int, required: int) -> float:
        if actual >= required:
            return min(1.0, 0.8 + (actual - required) * 0.05)
        return max(0, actual / required)

    def _education_match(self, actual: str, required: str) -> float:
        a = self.EDUCATION_LEVELS.get(actual, 0)
        r = self.EDUCATION_LEVELS.get(required, 0)
        if a >= r:
            return 1.0
        return max(0, a / r) if r > 0 else 0.5

    def _recommend(self, score: float) -> str:
        if score >= 0.8:
            return "强烈推荐面试"
        elif score >= 0.6:
            return "建议面试"
        elif score >= 0.4:
            return "待定，建议HR复审"
        return "不匹配"

    def _get_matched(self, resume_skills, required) -> list[str]:
        r = {s.lower() for s in resume_skills}
        return [s for s in required if s.lower() in r]

    def _get_missing(self, resume_skills, required) -> list[str]:
        r = {s.lower() for s in resume_skills}
        return [s for s in required if s.lower() not in r]


class InterviewScheduler:
    """面试邀约"""

    def generate_invitation(self, resume: ResumeData,
                            job: JobRequirement,
                            match_result: dict) -> dict:
        matched = ", ".join(match_result.get("matched_skills", [])[:3])
        body = (
            f"尊敬的{resume.name}：\n\n"
            f"感谢您投递「{job.title}」岗位。\n"
            f"经过初步筛选，您在{matched}等方面的经验与岗位要求高度匹配，"
            f"诚邀您参加面试。\n\n"
            f"面试形式：线上视频面试\n"
            f"预计时长：45分钟\n\n"
            f"请回复本邮件确认面试时间。\n\n"
            f"祝好！\nHR团队"
        )
        return {
            "to": resume.email or f"{resume.name}@example.com",
            "subject": f"面试邀请 - {job.title}",
            "body": body,
            "match_score": match_result["overall"],
        }


class RecruitmentAgent:
    """招聘助手Agent主控"""

    def __init__(self):
        self.parser = ResumeParser()
        self.engine = MatchingEngine()
        self.scheduler = InterviewScheduler()

    def process_batch(self, resumes: list[str],
                      job: JobRequirement) -> list[dict]:
        results = []
        for text in resumes:
            resume = self.parser.parse(text)
            match = self.engine.match(resume, job)
            result = {"resume": resume, "match": match}

            if match["overall"] >= 0.6:
                invitation = self.scheduler.generate_invitation(
                    resume, job, match)
                result["invitation"] = invitation

            results.append(result)

        results.sort(key=lambda x: x["match"]["overall"], reverse=True)
        return results


def build_test_resumes() -> list[str]:
    return [
        "张三\n邮箱：zhangsan@example.com\n电话：13800138001\n"
        "学历：硕士\n工作经验：5年\n"
        "技能：Python, LangChain, RAG, Docker, MySQL\n"
        "项目经验：\n项目1：企业级RAG知识问答系统\n项目2：AI客服平台",

        "李四\n邮箱：lisi@example.com\n电话：13900139002\n"
        "学历：本科\n工作经验：3年\n"
        "技能：Java, React, MySQL, Redis\n"
        "项目经验：\n项目1：电商后台管理系统",

        "王五\n邮箱：wangwu@example.com\n电话：13700137003\n"
        "学历：硕士\n工作经验：7年\n"
        "技能：Python, 机器学习, 深度学习, NLP, 大模型, Kubernetes\n"
        "项目经验：\n项目1：大模型微调平台\n项目2：NLP文本分类系统\n项目3：AI推荐引擎",

        "赵六\n邮箱：zhaoliu@example.com\n电话：13600136004\n"
        "学历：大专\n工作经验：1年\n"
        "技能：Python, JavaScript\n"
        "项目经验：\n项目1：个人博客网站",

        "钱七\n邮箱：qianqi@example.com\n电话：13500135005\n"
        "学历：本科\n工作经验：4年\n"
        "技能：Python, Docker, AWS, LangChain, RAG, Redis\n"
        "项目经验：\n项目1：智能文档处理系统\n项目2：多Agent协作平台",
    ]


def main():
    agent = RecruitmentAgent()

    print("=" * 60)
    print("招聘助手Agent演示")
    print("=" * 60)

    # 定义岗位
    job = JobRequirement(
        title="AI工程师",
        required_skills=["Python", "LangChain", "RAG", "Docker"],
        preferred_skills=["Kubernetes", "大模型", "NLP"],
        min_experience=3,
        min_education="本科",
        description="负责AI应用开发，包括RAG系统和Agent开发",
    )

    print(f"\n--- 岗位信息 ---")
    print(f"  职位: {job.title}")
    print(f"  必须技能: {job.required_skills}")
    print(f"  加分技能: {job.preferred_skills}")
    print(f"  最低经验: {job.min_experience}年")
    print(f"  最低学历: {job.min_education}")

    # 解析简历
    resumes = build_test_resumes()
    print(f"\n--- 1. 简历解析 ({len(resumes)}份) ---")
    for text in resumes:
        parsed = agent.parser.parse(text)
        print(f"  {parsed.name}: {parsed.education} | "
              f"{parsed.years_exp}年 | 技能: {parsed.skills[:4]}")

    # 批量匹配
    print(f"\n--- 2. 岗位匹配 ---")
    results = agent.process_batch(resumes, job)

    for r in results:
        m = r["match"]
        icon = {"强烈推荐面试": "🟢", "建议面试": "🟡",
                "待定，建议HR复审": "🟠", "不匹配": "🔴"}
        print(f"  {icon.get(m['recommendation'], '?')} {m['name']}: "
              f"总分={m['overall']} "
              f"(技能={m['skill_score']} 经验={m['experience_score']} "
              f"学历={m['education_score']})")
        print(f"     匹配: {m['matched_skills']} | 缺失: {m['missing_skills']}")
        print(f"     建议: {m['recommendation']}")

    # 面试邀约
    print(f"\n--- 3. 面试邀约 ---")
    invited = [r for r in results if "invitation" in r]
    print(f"  共{len(invited)}人达到面试标准")
    for r in invited:
        inv = r["invitation"]
        print(f"\n  收件人: {inv['to']}")
        print(f"  主题: {inv['subject']}")
        print(f"  匹配度: {inv['match_score']}")
        body_preview = inv["body"].split("\n")[2]
        print(f"  内容预览: {body_preview[:60]}...")

    # 统计
    print(f"\n--- 4. 筛选统计 ---")
    categories = {}
    for r in results:
        rec = r["match"]["recommendation"]
        categories[rec] = categories.get(rec, 0) + 1
    for cat, count in categories.items():
        print(f"  {cat}: {count}人")


if __name__ == "__main__":
    main()
