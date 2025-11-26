# Trae 快速开始指南

## 快速安装

### 方法 1: 从 Debian 包安装（推荐）

```bash
# 首先安装构建依赖
sudo apt update
sudo apt install devscripts debhelper python3-all python3-setuptools python3-pip dh-python

# 构建 Debian 包
make deb

# 安装
sudo dpkg -i ../trae_0.1.0_all.deb
sudo apt-get install -f  # 安装依赖
```

**注意**: `make deb` 会自动检查依赖，如果缺少会提示您安装。

### 方法 2: 开发模式安装

```bash
pip3 install -e .
```

## 配置 API 密钥

### 使用环境变量（推荐）

```bash
export TRAE_API_KEY="sk-your-openai-api-key"
export TRAE_PROVIDER="openai"  # 可选: openai, anthropic, qwen/dashscope, local
export TRAE_MODEL="gpt-3.5-turbo"  # 可选
export TRAE_CONTEXT_WINDOW="50"  # 可选: 上下文条数
export TRAE_CONTEXT_OUTPUT_LIMIT="2000"  # 可选: 单条上下文字数限制
```

### 使用命令行参数

```bash
# 只设置 API 密钥
trae --api-key sk-your-key "查询内存使用情况"

# 同时设置 API 密钥和模型
trae --api-key sk-your-key --model gpt-4 "查询内存使用情况"

# 同时设置 API 密钥、提供商和模型
trae --api-key sk-your-key --provider openai --model gpt-4 "查询内存使用情况"
```

### 使用配置文件

创建 `~/.trae/config.json`:

```json
{
  "api_key": "sk-your-api-key",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "context_window": 50,
  "context_output_limit": 2000
}
```

### 管理上下文

- Trae 会自动把每次查询、生成的命令以及部分输出写入 `~/.trae/history.jsonl`，默认保留 50 条。
- 可以通过 `TRAE_CONTEXT_WINDOW` 或 CLI 参数 `--context-window` 调整，例如：

```bash
export TRAE_CONTEXT_WINDOW=20
trae --context-window 25 "结合上一条命令继续处理日志"
```

- 想要彻底清空上下文时，删除该文件即可。
- 如果希望保存更多/更少的命令输出，可设置 `TRAE_CONTEXT_OUTPUT_LIMIT` 或在配置文件中新增 `"context_output_limit": 2000`（单位：字符）。超出限制时会保留输出的开头和结尾，中间以 `...` 连接。

## 安装 LLM 库

根据您使用的 LLM 提供商，安装相应的库：

```bash
# OpenAI
pip3 install openai

# Anthropic (Claude)
pip3 install anthropic

# 或安装所有
pip3 install openai anthropic
```

## 使用示例

```bash
# 基本使用
trae 帮我查询内存使用情况

# 显示文件列表
trae 显示当前目录的文件列表

# 查找文件
trae 查找所有 .log 文件

# 干运行（只显示命令，不执行）
trae --dry-run "查询内存使用情况"

# 自定义上下文窗口
trae --context-window 30 "根据上一条命令继续排查问题"

# 内置技能示例
trae "我的机器是什么配置"            # 离线输出表格
trae "mysql目前有几个数据库"        # 自动提示需要凭据
```

## 使用本地模型（Ollama）

1. 安装并启动 Ollama:

   ```bash
   # 安装 Ollama (参考 https://ollama.ai)
   curl -fsSL https://ollama.ai/install.sh | sh

   # 下载模型
   ollama pull llama2
   ```

1. 配置 Trae:

   ```bash
   export TRAE_PROVIDER="local"
   export TRAE_MODEL="llama2"
   export TRAE_API_KEY="dummy"  # 本地模型不需要真实密钥
   ```

1. 使用:

   ```bash
   trae "查询内存使用情况"
   ```

## 故障排除

### 错误: 未设置 API 密钥

确保设置了 `TRAE_API_KEY` 环境变量或使用 `--api-key` 参数。

### 错误: 未安装 openai 库

运行: `pip3 install openai`

### 命令执行失败

检查生成的命令是否正确，可以使用 `--dry-run` 先查看命令。

### `trae --help` 指向 `/usr/local/bin/trae`

如果曾经通过 `pip install -e .` 安装过 Trae，Shell 里可能缓存了旧的可执行文件路径（通常是 `/usr/local/bin/trae`）。安装 Debian 包后，新的可执行文件位于 `/usr/bin/trae`，但 Bash 仍然尝试执行旧路径，就会出现：

```text
bash: /usr/local/bin/trae: 没有那个文件或目录
```

解决方法：

1. 删除或重命名旧的 `/usr/local/bin/trae`（如果仍然存在）。
1. 在当前 Shell 中执行 `hash -r`（或重新打开一个终端），清除缓存的路径。
1. 使用 `command -v trae` 确认新路径已经指向 `/usr/bin/trae`，然后再运行 `trae --help`。

这样就能确保系统调用到 Debian 包安装的最新版本。

## 下一步

- 查看完整文档: `README.md`
- 查看构建指南: `BUILD.md`
- 查看帮助: `trae --help`

## 卸载

```bash
sudo apt remove trae
```

- hash -r && command -v trae
- 检查命令是否存在：`which trae`（应无输出）
- 检查包是否还在系统中：`dpkg -l | grep trae`（应无输出）
- 检查文件是否被删除：`ls /usr/local/bin/trae`（应提示 "No such file or directory"）
