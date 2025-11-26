"""
LLM 客户端 - 支持多种 LLM 提供商
"""
import os
from typing import Dict, Any, Optional
import sys


class LLMClient:
    """LLM 客户端基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化客户端"""
        self.config = config
        self.api_key = config.get("api_key")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.provider = config.get("provider", "openai")
    
    def generate(self, prompt: str) -> str:
        """
        生成响应
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM 响应文本
        """
        if self.provider == "openai":
            return self._generate_openai(prompt)
        elif self.provider == "anthropic":
            return self._generate_anthropic(prompt)
        elif self.provider == "qwen" or self.provider == "dashscope":
            return self._generate_qwen(prompt)
        elif self.provider == "local":
            return self._generate_local(prompt)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")
    
    def _generate_openai(self, prompt: str) -> str:
        """使用 OpenAI API"""
        try:
            import openai
        except ImportError:
            print("错误: 未安装 openai 库。请运行: pip install openai", file=sys.stderr)
            sys.exit(1)
        
        if not self.api_key:
            raise ValueError("未设置 OpenAI API 密钥")
        
        client = openai.OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个 Linux 命令生成助手。只返回命令，不要其他解释。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        return self._extract_text_from_choices(response, "OpenAI")
    
    def _generate_anthropic(self, prompt: str) -> str:
        """使用 Anthropic (Claude) API"""
        try:
            from anthropic import Anthropic
        except ImportError:
            print("错误: 未安装 anthropic 库。请运行: pip install anthropic", file=sys.stderr)
            sys.exit(1)
        
        if not self.api_key:
            raise ValueError("未设置 Anthropic API 密钥")
        
        client = Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=200,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content_blocks = getattr(response, "content", None)
        if not content_blocks:
            raise ValueError("Anthropic 响应未返回内容，请确认模型与配额。")
        text = self._extract_text_from_message(content_blocks[0])
        if not text:
            raise ValueError("Anthropic 响应缺少文本内容，请检查请求参数。")
        return text
    
    def _generate_qwen(self, prompt: str) -> str:
        """使用阿里云 DashScope (Qwen) API"""
        try:
            import dashscope
        except ImportError:
            print("错误: 未安装 dashscope 库。请运行: pip install dashscope", file=sys.stderr)
            sys.exit(1)
        
        if not self.api_key:
            raise ValueError("未设置 DashScope API 密钥")
        
        # 设置 API 密钥
        dashscope.api_key = self.api_key
        
        # 调用 DashScope API
        from dashscope import Generation
        
        response = Generation.call(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个 Linux 命令生成助手。只返回命令，不要其他解释。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        if response.status_code != 200:
            raise Exception(f"DashScope API 错误: {response.status_code} - {response.message}")
        
        return self._extract_text_from_choices(getattr(response, "output", None), "DashScope")
    
    def _generate_local(self, prompt: str) -> str:
        """使用本地模型（通过 Ollama 或其他本地服务）"""
        try:
            import requests
        except ImportError:
            print("错误: 未安装 requests 库。请运行: pip install requests", file=sys.stderr)
            sys.exit(1)
        
        # 默认使用 Ollama
        ollama_url = self.config.get("ollama_url", "http://localhost:11434/api/generate")
        model = self.config.get("model", "llama2")
        
        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API 错误: {response.status_code}")
        
        payload = {}
        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(f"Ollama 响应无法解析 JSON: {exc}") from exc
        
        text = payload.get("response") or payload.get("output")
        if not text:
            raise ValueError(f"Ollama 响应缺少 response 字段: {payload}")
        return str(text).strip()

    def _extract_text_from_choices(self, container: Any, provider: str) -> str:
        """通用解析：从包含 choices 的结构中提取文本"""
        choices = None
        if container is None:
            choices = None
        elif isinstance(container, dict):
            choices = container.get("choices")
        else:
            choices = getattr(container, "choices", None)
        if choices is None and isinstance(container, (list, tuple)):
            choices = container
        if not choices:
            raise ValueError(f"{provider} 响应未返回 choices，请确认模型与权限。")
        first = choices[0]
        text = self._extract_text_from_node(first)
        if not text:
            raise ValueError(f"{provider} 响应缺少 message.content，无法解析: {first}")
        return text

    def _extract_text_from_node(self, node: Any) -> Optional[str]:
        """支持多种 choice/message 结构"""
        if node is None:
            return None
        if isinstance(node, str):
            return node.strip() or None
        message = None
        if isinstance(node, dict):
            message = node.get("message") or node.get("delta") or node.get("content")
        else:
            message = getattr(node, "message", None) or getattr(node, "delta", None) or getattr(node, "content", None)
        if message is None:
            return self._normalize_segment(node)
        return self._extract_text_from_message(message)

    def _extract_text_from_message(self, message: Any) -> Optional[str]:
        """从 message/content 结构中提取文本"""
        if message is None:
            return None
        if isinstance(message, str):
            return message.strip() or None
        content = None
        text = None
        if isinstance(message, dict):
            content = message.get("content")
            text = message.get("text")
        else:
            content = getattr(message, "content", None)
            text = getattr(message, "text", None)
        normalized = self._normalize_segment(content)
        if normalized:
            return normalized
        return self._normalize_segment(text)

    def _normalize_segment(self, segment: Any) -> Optional[str]:
        """标准化各种结构（列表 / 字典 / 对象）的文本"""
        if segment is None:
            return None
        if isinstance(segment, str):
            stripped = segment.strip()
            return stripped if stripped else None
        if isinstance(segment, list):
            parts = []
            for item in segment:
                text = self._normalize_segment(item)
                if text:
                    parts.append(text)
            if parts:
                return "\n".join(parts).strip()
            return None
        if isinstance(segment, dict):
            nested = segment.get("text") or segment.get("content") or segment.get("value")
            return self._normalize_segment(nested)
        attr_text = getattr(segment, "text", None)
        if attr_text:
            return self._normalize_segment(attr_text)
        attr_content = getattr(segment, "content", None)
        return self._normalize_segment(attr_content)

