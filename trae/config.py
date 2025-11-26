"""
配置管理
"""
import os
import json
from typing import Dict, Any
from pathlib import Path


def _parse_int(value: Any, default: int) -> int:
    """安全地将值转换为 int"""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_config() -> Dict[str, Any]:
    """获取配置"""
    config = {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "api_key": None,
        "command_timeout": 30,
        "ollama_url": "http://localhost:11434/api/generate",
        "dashscope_base_url": None,  # 可选，自定义 DashScope API 地址
        "context_window": 50,
        "context_history_path": None,
        "context_output_limit": 2000,
    }
    
    # 从环境变量读取
    config["api_key"] = os.getenv("TRAE_API_KEY", config["api_key"])
    config["provider"] = os.getenv("TRAE_PROVIDER", config["provider"])
    config["model"] = os.getenv("TRAE_MODEL", config["model"])
    
    context_env = os.getenv("TRAE_CONTEXT_WINDOW")
    if context_env is not None:
        config["context_window"] = _parse_int(context_env, config["context_window"])
    context_output_env = os.getenv("TRAE_CONTEXT_OUTPUT_LIMIT")
    if context_output_env is not None:
        config["context_output_limit"] = _parse_int(context_output_env, config["context_output_limit"])
    
    # 从配置文件读取（如果存在）
    config_file = Path.home() / ".trae" / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception:
            pass
    
    config["context_window"] = max(1, _parse_int(config.get("context_window"), 50))
    config["context_output_limit"] = max(200, _parse_int(config.get("context_output_limit"), 2000))
    
    return config

