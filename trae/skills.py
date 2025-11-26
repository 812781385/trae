"""
智能技能模块 - 在调用 LLM 之前优先匹配常见需求
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence
import re


@dataclass
class SkillResult:
    """技能匹配结果"""

    intent: str
    command: Optional[str] = None
    response: Optional[str] = None
    explanation: Optional[str] = None
    needs_summary: bool = False


@dataclass
class SkillContext:
    """技能上下文"""

    history: List[dict]


class BaseSkill:
    """技能基类"""

    keywords: Iterable[str] = ()

    def match(self, query: str, ctx: Optional[SkillContext] = None) -> bool:
        if not self.keywords:
            return False
        normalized = query.lower()
        return any(keyword in normalized for keyword in self.keywords)

    def build_command(self, query: str, ctx: Optional[SkillContext] = None) -> SkillResult:
        raise NotImplementedError


class SystemInfoSkill(BaseSkill):
    """查询机器配置"""

    keywords = ("机器配置", "硬件信息", "配置", "cpu", "gpu", "内存", "主机配置")

    def match(self, query: str, ctx: Optional[SkillContext] = None) -> bool:
        normalized = query.lower()
        if "mysql" in normalized:
            return False
        return any(keyword in query for keyword in self.keywords)

    def build_command(self, query: str, ctx: Optional[SkillContext] = None) -> SkillResult:
        command = r"""python3 - <<'PY'
import os
import platform
import subprocess


def get_mem():
    try:
        with open('/proc/meminfo', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('MemTotal'):
                    total_kb = int(line.split()[1])
                    return f"{total_kb / 1024 / 1024:.2f} GB"
    except Exception:
        pass
    return "未知"


def get_gpu():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            capture_output=True,
            text=True,
            check=True,
        )
        names = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return ", ".join(names) if names else "未检测到 GPU"
    except Exception:
        return "未检测到 GPU"


def get_disk():
    try:
        result = subprocess.run(
            ['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "可执行 lsblk 以查看磁盘信息"


rows = [
    ("操作系统", platform.platform()),
    ("内核版本", platform.release()),
    ("处理器", platform.processor() or platform.machine()),
    ("CPU 核心数", os.cpu_count()),
    ("内存", get_mem()),
    ("GPU", get_gpu()),
]

title = "您的机器配置如下："
width = max(len(str(label)) for label, _ in rows)
print(title)
print("-" * (width + 25))
for label, value in rows:
    print(f"{label:<{width}} | {value}")
print("-" * (width + 25))
print("\n磁盘 (lsblk):")
print(get_disk())
PY"""
        return SkillResult(
            intent="run_command",
            command=command,
            explanation="我会收集 CPU/内存/GPU 等硬件信息并展示磁盘概况。",
            needs_summary=True,
        )


class MysqlInfoSkill(BaseSkill):
    """处理需要 MySQL 凭据的查询"""

    keywords = ("mysql", "数据库", "数据表", "schema")
    MYSQL_CREDENTIAL_PATTERN = re.compile(r"mysql", re.IGNORECASE)

    def match(self, query: str, ctx: Optional[SkillContext] = None) -> bool:
        if not self.MYSQL_CREDENTIAL_PATTERN.search(query):
            return False
        intents = ("几个数据库", "表有哪些", "列举", "统计", "显示", "有多少")
        return any(intent in query for intent in intents) or "?" in query

    def build_command(self, query: str, ctx: Optional[SkillContext] = None) -> SkillResult:
        message = (
            "我需要 MySQL 的连接信息（主机、端口、用户名、密码）才能执行查询。\n"
            "请提供具备只读权限的账号，或明确说明是否已配置默认凭据。"
        )
        return SkillResult(intent="chat_reply", response=message)


class FollowupAnalysisSkill(BaseSkill):
    """处理解释/分析/追问"""
    
    capacity_keywords: Sequence[str] = ("够用", "足够", "够不够", "行不行", "是否够", "够吗")
    explain_keywords: Sequence[str] = ("分析", "什么意思", "啥意思", "解释", "看法", "如何看", "怎么看")
    action_keywords: Sequence[str] = (
        "执行了什么",
        "执行了啥",
        "做了什么",
        "做了啥",
        "运行了什么",
        "运行了啥",
        "你执行",
        "你刚才",
        "刚才干嘛",
        "上一条命令",
        "上一个命令",
        "什么操作",
        "哪个命令",
    )
    
    def match(self, query: str, ctx: Optional[SkillContext] = None) -> bool:
        intent = self._detect_intent(query)
        return intent is not None
    
    def build_command(self, query: str, ctx: Optional[SkillContext] = None) -> SkillResult:
        history = ctx.history if ctx else []
        intent = self._detect_intent(query)
        
        if intent == "capacity":
            message = self._build_capacity_response(query, history)
        elif intent == "action":
            message = self._build_action_response(history)
        else:
            message = self._build_explain_response(query, history)
        
        return SkillResult(intent="chat_reply", response=message)
    
    def _detect_intent(self, query: str) -> Optional[str]:
        normalized = query.lower()
        if any(keyword in query for keyword in self.capacity_keywords):
            return "capacity"
        if any(keyword in query for keyword in self.action_keywords) or any(
            keyword in normalized for keyword in ("你做", "你干嘛", "你干了啥")
        ):
            return "action"
        if any(keyword in normalized for keyword in self.explain_keywords):
            return "explain"
        return None

    def _build_capacity_response(self, query: str, history: List[dict]) -> str:
        latest = self._latest_history(history)
        if not latest:
            return (
                f"你问“{query}”。我需要最近一次的资源监控结果（如 `trae 查询内存使用情况`）"
                "才能判断是否足够，请先提供相关输出。"
            )

        output = latest.get("output") or ""
        snippet = self._snippet(output)
        memory_value = self._extract_memory_value(output)
        summary = (
            f"最新的引用结果显示总内存约 {memory_value}。" if memory_value else "最新输出中未找到明确的内存容量。"
        )

        return (
            f"根据上一条命令（{latest.get('command', '未知命令')}）的输出：\n"
            f"{snippet}\n\n{summary}\n"
            f"是否“够用”取决于你的具体工作负载。"
            "如果主要进行日常开发/办公，这个配置通常已经相当充足；"
            "若需要运行大型模型、海量数据处理或多虚拟机并行，请说明目标负载，我可以再给出更具体的建议。"
        )

    def _build_explain_response(self, query: str, history: List[dict]) -> str:
        latest = self._latest_history(history)
        if not latest:
            return f"你提到“{query}”。请告诉我需要分析的命令或输出内容，这样我才能进一步解释。"

        output = latest.get("output") or ""
        snippet = self._snippet(output)
        return (
            f"你想让我分析“{query}”。\n"
            f"上一条命令（{latest.get('command', '未知命令')}）的输出摘要如下：\n"
            f"{snippet}\n\n"
            "请具体说明你希望关注的字段、指标或异常点，我会基于这些信息进行解释。"
        )
    
    def _build_action_response(self, history: List[dict]) -> str:
        latest = self._latest_command(history)
        if not latest:
            return "我还没有执行任何命令，无法复述操作。请先让我运行一条命令。"
        
        command = latest.get("command", "（未知命令）")
        query = latest.get("query")
        output = latest.get("output")
        snippet = self._snippet(output) if output else "（该命令未产生输出）"
        
        response = [
            "上一条命令的执行摘要：",
            f"- 命令: {command}",
        ]
        if query:
            response.append(f"- 对应请求: {query}")
        
        if output:
            response.append("- 输出摘录:")
            response.append(snippet)
        else:
            response.append("- 输出摘录: （无可引用输出）")
        
        response.append("如果需要重新执行或进一步分析，请告诉我。")
        return "\n".join(response)

    @staticmethod
    def _latest_history(history: List[dict]) -> Optional[dict]:
        for item in reversed(history or []):
            if item.get("output"):
                return item
        return history[-1] if history else None
    
    @staticmethod
    def _latest_command(history: List[dict]) -> Optional[dict]:
        return history[-1] if history else None

    @staticmethod
    def _snippet(text: str, limit: int = 600) -> str:
        text = (text or "").strip()
        if not text:
            return "（无可引用输出）"
        if len(text) <= limit:
            return text
        head = text[: limit // 2].rstrip()
        tail = text[-limit // 2 :].lstrip()
        return f"{head}\n...\n{tail}"

    @staticmethod
    def _extract_memory_value(text: str) -> Optional[str]:
        pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(Gi|GB|G|Mi|MB)', re.IGNORECASE)
        match = pattern.search(text.replace("：", ":"))
        if match:
            return f"{match.group(1)} {match.group(2).upper()}"
        return None


class SkillManager:
    """管理技能列表"""

    def __init__(self, skills: Optional[List[BaseSkill]] = None) -> None:
        self.skills = skills or []

    def handle(self, query: str, history: Optional[List[dict]] = None) -> Optional[SkillResult]:
        if not query:
            return None
        ctx = SkillContext(history=history or [])
        for skill in self.skills:
            try:
                if skill.match(query, ctx):
                    return skill.build_command(query, ctx)
            except Exception:
                continue
        return None

