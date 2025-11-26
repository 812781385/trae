"""
命令生成和执行代理
"""
import sys
import subprocess
import re
import os
import json
import traceback
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from trae.llm_client import LLMClient
from trae.history import ContextManager
from trae.skills import SkillManager, SystemInfoSkill, MysqlInfoSkill, FollowupAnalysisSkill


@dataclass
class CommandResult:
    """命令执行结果"""
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ActionPlan:
    """LLM 规划结果"""
    intent: str
    explanation: Optional[str] = None
    command: Optional[str] = None
    needs_summary: bool = False
    response: Optional[str] = None
    skill_origin: Optional[str] = None


class CommandAgent:
    """命令生成和执行代理"""
    
    # 危险命令模式
    DANGEROUS_PATTERNS = [
        r'\brm\s+-rf',
        r'\bdd\s+if=',
        r'\bmkfs\b',
        r'\bfdisk\b',
        r'\bchmod\s+[0-7]{3,4}',
        r'\bchown\s+.*\s+/',
        r'>\s*/dev/',
        r'\|\s*sh\s*$',
        r'\|\s*bash\s*$',
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """初始化代理"""
        self.config = config
        self.llm_client = LLMClient(config)
        self.context_window = max(1, int(config.get("context_window", 50)))
        self.context_output_limit = max(200, int(config.get("context_output_limit", 2000)))
        history_path = config.get("context_history_path")
        self.context_manager = ContextManager(
            max_entries=self.context_window,
            history_file=history_path,
            output_limit=self.context_output_limit,
        )
        self.skill_manager = SkillManager([
            SystemInfoSkill(),
            MysqlInfoSkill(),
            FollowupAnalysisSkill(),
        ])

    def plan_interaction(self, query: str) -> Optional[ActionPlan]:
        """返回对用户请求的处理计划（对话或命令）"""
        history = self.get_recent_history()
        skill_result = self.skill_manager.handle(query, history)
        if skill_result:
            return self._plan_from_skill(skill_result)

        prompt = self._build_plan_prompt(query, history)
        
        try:
            response = self.llm_client.generate(prompt)
            plan = self._parse_plan_response(response)
            return plan
        except Exception as e:
            if os.getenv("TRAE_DEBUG") == "1":
                traceback.print_exc()
            print(f"生成命令时出错: {e}", file=sys.stderr)
            return None
    
    def get_recent_history(self) -> List[Dict[str, str]]:
        """返回最近的上下文"""
        if not self.context_manager:
            return []
        return self.context_manager.load()
    
    def record_interaction(self, query: str, command: str, output: Optional[str]) -> None:
        """记录一次交互"""
        if not self.context_manager:
            return
        self.context_manager.add_entry(query, command, output)
    
    def _plan_from_skill(self, skill_result) -> ActionPlan:
        """将技能结果转换为 ActionPlan"""
        intent = skill_result.intent or "run_command"
        return ActionPlan(
            intent=intent,
            command=skill_result.command,
            response=skill_result.response,
            explanation=skill_result.explanation,
            needs_summary=bool(skill_result.needs_summary),
            skill_origin=intent,
        )

    def _build_plan_prompt(self, query: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """构建 Planner 提示词"""
        history_section = self._format_history(history or [])
        return f"""你是一个拥有终端访问权限的智能代理，需要根据用户的需求决定下一步行动。
如果需要执行命令，请在解释完目的后再执行。否则直接用自然语言回答。

请将你的规划输出为 JSON，字段如下：
{{
  "intent": "chat_reply" | "run_command" | "ask_clarification",
  "explanation": "向用户描述你将做什么或回答内容",
  "command": "当 intent=run_command 时需要执行的命令",
  "needs_summary": true or false
}}

若 intent=chat_reply，仅填写 explanation（必要时附加 response 字段）；若需要澄清，intent=ask_clarification 并在 explanation 中提出问题。
命令必须是安全、单行且可直接在 shell 中运行。

历史上下文：
{history_section}

用户查询: {query}

请只输出 JSON："""
    
    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """将历史记录格式化为提示词片段"""
        lines = []
        for item in history:
            lines.append(f"用户: {item.get('query', '')}")
            if item.get("command"):
                lines.append(f"命令: {item['command']}")
            if item.get("output"):
                lines.append(f"输出: {item['output']}")
            lines.append("")
        return "\n".join(lines).strip() or "（无）"

    def _parse_plan_response(self, response: str) -> ActionPlan:
        """解析 LLM 返回的 JSON 规划"""
        cleaned = response.strip()
        cleaned = re.sub(r'^```json', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^```', '', cleaned).strip()
        cleaned = re.sub(r'```$', '', cleaned).strip()

        try:
            data = json.loads(cleaned)
            intent = str(data.get("intent", "run_command")).strip() or "run_command"
            explanation = data.get("explanation")
            command = data.get("command")
            needs_summary = bool(data.get("needs_summary", intent == "run_command"))
            response_text = data.get("response")
            return ActionPlan(
                intent=intent,
                explanation=explanation,
                command=command,
                needs_summary=needs_summary,
                response=response_text,
            )
        except json.JSONDecodeError:
            command = self._extract_command_like(cleaned)
            if command:
                return ActionPlan(
                    intent="run_command",
                    command=command,
                    explanation="我将执行生成的命令以满足请求。",
                    needs_summary=True,
                )
            raise

    def _extract_command_like(self, response: str) -> Optional[str]:
        """兼容旧模型输出，提取首行命令"""
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        if not lines:
            return None
        command = re.sub(r'^[$#>]\s*', '', lines[0])
        return command or None
    
    def is_dangerous_command(self, command: str) -> bool:
        """检查命令是否危险"""
        command_lower = command.lower()
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command_lower):
                return True
        return False
    
    def execute_command(self, command: str) -> CommandResult:
        """
        执行命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            CommandResult 对象
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.get("command_timeout", 30)
            )
            return CommandResult(
                returncode=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                returncode=124,
                stdout="",
                stderr="命令执行超时"
            )
        except Exception as e:
            return CommandResult(
                returncode=1,
                stdout="",
                stderr=f"执行错误: {e}"
            )

    def summarize_result(self, query: str, plan: ActionPlan, result: CommandResult) -> Optional[str]:
        """根据命令输出生成自然语言总结"""
        if not plan.needs_summary:
            return None
        output_text = result.stdout.strip() or result.stderr.strip()
        if not output_text:
            return None

        trimmed = self._truncate_for_summary(output_text)
        prompt = f"""你是一名终端助手，需要向用户总结命令执行结果。
用户原始请求: {query}
执行命令: {plan.command}
命令输出:
{trimmed}

请用简洁的中文总结 1-2 句话，突出关键数字或状态，并说明是否成功。"""

        try:
            summary = self.llm_client.generate(prompt).strip()
            return summary
        except Exception:
            if os.getenv("TRAE_DEBUG") == "1":
                traceback.print_exc()
            return None

    def _truncate_for_summary(self, text: str, limit: int = 1600) -> str:
        if len(text) <= limit:
            return text
        head = text[: limit // 2].rstrip()
        tail = text[-limit // 2 :].lstrip()
        return f"{head}\n...\n{tail}"

