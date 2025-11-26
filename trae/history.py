"""
上下文管理器 - 负责持久化查询历史
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional


class ContextManager:
    """简单的 JSONL 历史记录管理器"""

    def __init__(
        self,
        max_entries: int = 50,
        history_file: Optional[str] = None,
        output_limit: int = 2000,
    ) -> None:
        self.max_entries = max(1, int(max_entries))
        self.output_limit = max(200, int(output_limit))

        if history_file:
            history_path = Path(history_file)
            history_path.parent.mkdir(parents=True, exist_ok=True)
            self.history_file = history_path
        else:
            base_dir = Path.home() / ".trae"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = base_dir / "history.jsonl"

    def load(self) -> List[Dict[str, str]]:
        """读取最近的历史记录"""
        entries: List[Dict[str, str]] = []

        if not self.history_file.exists():
            return entries

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if not isinstance(data, dict):
                        continue

                    query = data.get("query")
                    command = data.get("command")
                    output = data.get("output")

                    if not isinstance(query, str) or not isinstance(command, str):
                        continue

                    entry: Dict[str, str] = {
                        "query": query,
                        "command": command,
                    }
                    if isinstance(output, str) and output:
                        entry["output"] = output
                    entries.append(entry)
        except OSError:
            return []

        return entries[-self.max_entries :]

    def add_entry(self, query: str, command: str, output: Optional[str] = None) -> None:
        """追加一条历史记录"""
        entry: Dict[str, str] = {
            "query": query,
            "command": command,
        }
        if output:
            entry["output"] = self._truncate(output)

        entries = self.load()
        entries.append(entry)
        entries = entries[-self.max_entries :]

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                for item in entries:
                    json.dump(item, f, ensure_ascii=False)
                    f.write("\n")
        except OSError:
            pass

    def _truncate(self, text: str) -> str:
        """限制输出长度，避免提示词过长"""
        text = text.strip()
        limit = self.output_limit
        if len(text) <= limit:
            return text
        head = max(100, limit // 2)
        tail = limit - head
        head_text = text[:head].rstrip()
        tail_text = text[-tail:].lstrip()
        return f"{head_text}\n...\n{tail_text}"

