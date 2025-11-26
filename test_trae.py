#!/usr/bin/env python3
"""
简单的测试脚本 - 用于验证 Trae 基本功能
"""
import sys
import os
import tempfile
import shutil
import atexit

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from trae.config import get_config
from trae.agent import CommandAgent
from trae.history import ContextManager
from trae.skills import SkillManager, SystemInfoSkill, MysqlInfoSkill, FollowupAnalysisSkill


_TEST_TMPDIR = tempfile.mkdtemp(prefix="trae-test-")
atexit.register(lambda: shutil.rmtree(_TEST_TMPDIR, ignore_errors=True))


def _history_path(filename: str) -> str:
    return os.path.join(_TEST_TMPDIR, filename)


def test_config():
    """测试配置加载"""
    print("测试配置加载...")
    config = get_config()
    assert isinstance(config, dict)
    assert "provider" in config
    assert "model" in config
    print("✓ 配置加载正常")


def test_agent_init():
    """测试代理初始化"""
    print("测试代理初始化...")
    config = get_config()
    # 使用虚拟 API 密钥进行测试
    config["api_key"] = "test-key"
    config["context_history_path"] = _history_path("agent_init.jsonl")
    agent = CommandAgent(config)
    assert agent is not None
    print("✓ 代理初始化正常")


def test_dangerous_command_detection():
    """测试危险命令检测"""
    print("测试危险命令检测...")
    config = get_config()
    config["api_key"] = "test-key"
    config["context_history_path"] = _history_path("dangerous_commands.jsonl")
    agent = CommandAgent(config)
    
    dangerous_commands = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs.ext4 /dev/sda1",
    ]
    
    safe_commands = [
        "ls -la",
        "cat file.txt",
        "echo hello",
    ]
    
    for cmd in dangerous_commands:
        assert agent.is_dangerous_command(cmd), f"应该检测到危险命令: {cmd}"
    
    for cmd in safe_commands:
        assert not agent.is_dangerous_command(cmd), f"不应该标记为危险: {cmd}"
    
    print("✓ 危险命令检测正常")


def test_context_manager():
    """测试上下文管理器"""
    print("测试上下文管理器...")
    history_file = _history_path("context.jsonl")
    manager = ContextManager(max_entries=2, history_file=history_file, output_limit=200)
    
    assert manager.load() == []
    
    manager.add_entry("查询1", "cmd1", "输出1")
    manager.add_entry("查询2", "cmd2", "输出2")
    manager.add_entry("查询3", "cmd3", "输出3")
    
    history = manager.load()
    assert len(history) == 2
    assert history[0]["query"] == "查询2"
    assert history[-1]["command"] == "cmd3"
    assert history[-1]["output"].endswith("输出3")
    
    long_text = "a" * 600
    manager.add_entry("查询4", "cmd4", long_text)
    history = manager.load()
    assert history[-1]["query"] == "查询4"
    truncated = history[-1]["output"]
    assert "\n...\n" in truncated
    assert truncated.startswith(long_text[:100])
    assert truncated.endswith(long_text[-100:])
    
    print("✓ 上下文管理器正常")


def test_skills():
    """测试技能系统"""
    print("测试技能系统...")
    history = [{
        "query": "查询内存使用情况",
        "command": "free -h",
        "output": "               total        used        free      shared  buff/cache   available\n内存：       62Gi       5.7Gi        12Gi        30Mi        44Gi        56Gi\n交换：      2.0Gi       1.0Mi       2.0Gi"
    }]
    manager = SkillManager([SystemInfoSkill(), MysqlInfoSkill(), FollowupAnalysisSkill()])
    
    system_cmd = manager.handle("我的机器是什么配置", history)
    assert system_cmd and system_cmd.intent == "run_command"
    assert "python3 - <<'PY'" in system_cmd.command
    
    mysql_cmd = manager.handle("mysql目前有几个数据库", history)
    assert mysql_cmd and mysql_cmd.intent == "chat_reply"
    assert "MySQL 的连接信息" in mysql_cmd.response

    capacity_cmd = manager.handle("62.63 GB对于我来说够用吗", history)
    assert capacity_cmd and capacity_cmd.intent == "chat_reply"
    assert "是否“够用”" in capacity_cmd.response

    explain_cmd = manager.handle("分析什么意思", history)
    assert explain_cmd and explain_cmd.intent == "chat_reply"
    assert "输出摘要" in explain_cmd.response
    
    action_cmd = manager.handle("你执行了什么操作？", history)
    assert action_cmd and action_cmd.intent == "chat_reply"
    assert "上一条命令" in action_cmd.response
    
    print("✓ 技能系统正常")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("Trae 功能测试")
    print("=" * 50)
    print()
    
    try:
        test_config()
        test_agent_init()
        test_dangerous_command_detection()
        test_context_manager()
        test_skills()
        
        print()
        print("=" * 50)
        print("所有测试通过！")
        print("=" * 50)
        print()
        print("注意: 这些是基本功能测试。")
        print("要测试完整的 LLM 集成，需要设置有效的 API 密钥。")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

