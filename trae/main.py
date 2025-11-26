#!/usr/bin/env python3
"""
Trae 主程序 - 自然语言 Linux 命令执行工具
"""
import sys
import subprocess
import argparse
from typing import Optional
from trae.agent import CommandAgent
from trae.config import get_config


def main():
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="Trae - 使用自然语言执行 Linux 命令",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  trae 帮我查询内存使用情况
  trae 显示当前目录的文件列表
  trae 查找所有 .log 文件
        """
    )
    
    parser.add_argument(
        "query",
        nargs="*",
        help="自然语言查询"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只显示生成的命令，不执行"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="LLM API 密钥（可选，也可通过环境变量 TRAE_API_KEY 设置）"
    )
    
    parser.add_argument(
        "--provider",
        type=str,
        default=None,
        help="LLM 提供商（openai, anthropic, qwen/dashscope, local，默认从配置读取）"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="指定使用的 LLM 模型（默认从配置读取）"
    )
    
    parser.add_argument(
        "--context-window",
        type=int,
        default=None,
        help="上下文条数（默认 50）"
    )
    
    args = parser.parse_args()
    
    # 如果没有提供查询，显示帮助
    if not args.query:
        parser.print_help()
        sys.exit(0)
    
    query = " ".join(args.query)
    
    # 获取配置
    config = get_config()
    if args.api_key:
        config["api_key"] = args.api_key
    if args.provider:
        config["provider"] = args.provider
    if args.model:
        config["model"] = args.model
    if args.context_window is not None:
        if args.context_window < 1:
            print("错误: --context-window 必须大于等于 1", file=sys.stderr)
            sys.exit(1)
        config["context_window"] = args.context_window
    
    # 检查 API 密钥
    if not config.get("api_key"):
        print("错误: 未设置 API 密钥。请通过 --api-key 参数或环境变量 TRAE_API_KEY 设置。", file=sys.stderr)
        print("提示: 支持的 LLM 提供商包括 OpenAI、Anthropic、Qwen、本地模型等。", file=sys.stderr)
        sys.exit(1)
    
    try:
        agent = CommandAgent(config)
        print(f"理解中: {query}")
        plan = agent.plan_interaction(query)

        if not plan:
            print("错误: 无法生成有效的行动计划", file=sys.stderr)
            sys.exit(1)

        if plan.intent == "chat_reply":
            reply = plan.response or plan.explanation or "（无可用回复）"
            print(f"\n{reply}")
            agent.record_interaction(query, "[chat]", reply)
            return

        if plan.intent == "ask_clarification":
            message = plan.explanation or "我需要更多信息才能继续。"
            print(f"\n{message}")
            agent.record_interaction(query, "[clarification]", message)
            return

        if plan.intent != "run_command":
            print(f"错误: 无法识别的意图 {plan.intent}", file=sys.stderr)
            sys.exit(1)

        if not plan.command:
            print("错误: 规划结果缺少命令", file=sys.stderr)
            sys.exit(1)

        if plan.explanation:
            print(f"\n行动规划: {plan.explanation}")

        print(f"\n生成的命令: {plan.command}")

        if args.dry_run:
            agent.record_interaction(query, plan.command, "[dry-run]")
            print("\n[干运行模式 - 命令未执行]")
            return

        if agent.is_dangerous_command(plan.command):
            response = input("\n警告: 此命令可能具有危险性。是否继续执行? (y/N): ")
            if response.lower() != 'y':
                print("已取消执行")
                sys.exit(0)

        print("\n执行中...\n")
        result = agent.execute_command(plan.command)

        log_output = None
        if result.returncode == 0:
            if result.stdout:
                print(result.stdout)
                log_output = result.stdout
        else:
            if result.stderr:
                print(result.stderr, file=sys.stderr)
                log_output = result.stderr or result.stdout
            agent.record_interaction(query, plan.command, log_output)
            sys.exit(result.returncode)

        summary = agent.summarize_result(query, plan, result)
        if summary:
            print(f"\n总结: {summary}")
            log_output = f"{summary}\n\n{log_output}".strip() if log_output else summary

        agent.record_interaction(query, plan.command, log_output)
            
    except KeyboardInterrupt:
        print("\n\n已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

