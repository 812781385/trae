# Trae

Trae 是一个强大的 Linux 命令行工具，允许您使用自然语言执行 Linux 命令。只需用自然语言描述您想要执行的操作，Trae 会理解您的意图，生成相应的 Linux 命令，并自动执行。

## 功能特性

- 🤖 **智能理解**: 使用大语言模型（LLM）理解自然语言查询
- ⚡ **自动执行**: 自动生成并执行 Linux 命令
- 🛡️ **安全保护**: 内置危险命令检测，防止误操作
- 🔌 **多 LLM 支持**: 支持 OpenAI、Anthropic (Claude) 和本地模型（Ollama）
- 🧠 **上下文记忆**: 自动携带最近 50 条交互记录，可按需调整
- 🧩 **内置技能**: 常见问题（机器配置、数据库凭据提示等）无需调用 LLM，离线快速响应
- 📦 **易于安装**: 可通过 `apt install trae` 安装

## 安装

### 通过 apt 安装（推荐）

```bash
sudo apt update
sudo apt install trae
```

### 从源码安装

```bash
git clone https://github.com/yourusername/trae.git
cd trae
pip install -e .
```

## 配置

### 设置 API 密钥

Trae 需要 LLM API 密钥才能工作。您可以通过以下方式设置：

1. **环境变量**（推荐）:

```bash
export TRAE_API_KEY="your-api-key-here"
export TRAE_PROVIDER="openai"  # 可选: openai, anthropic, qwen/dashscope, local
export TRAE_MODEL="gpt-3.5-turbo"  # 可选
export TRAE_CONTEXT_WINDOW="50"  # 可选: 上下文条数
export TRAE_CONTEXT_OUTPUT_LIMIT="2000"  # 可选: 单条上下文的最大字符数
```

1. **命令行参数**:

```bash
# 只设置 API 密钥
trae --api-key your-api-key-here "查询内存使用情况"

# 同时设置 API 密钥和模型
trae --api-key your-api-key-here --model gpt-4 "查询内存使用情况"

# 同时设置 API 密钥、提供商和模型
trae --api-key your-api-key-here --provider openai --model gpt-4 "查询内存使用情况"
```

1. **配置文件**:

创建 `~/.trae/config.json`:

```json
{
  "api_key": "your-api-key-here",
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "context_window": 50,
  "context_output_limit": 2000
}
```

### 上下文记忆

- Trae 会把最近的查询、生成的命令和部分输出保存到 `~/.trae/history.jsonl`。
- 默认保留 50 条记录，可通过以下方式自定义：
  - 环境变量：`export TRAE_CONTEXT_WINDOW=20`
  - CLI 参数：`trae --context-window 30 "查看磁盘空间"`
  - 配置文件字段：`"context_window": 30`
- 默认会为每条记录保留约 2000 个字符的输出，超出部分会保留开头与结尾并在中间插入 `...`，可通过 `TRAE_CONTEXT_OUTPUT_LIMIT` 或配置文件的 `"context_output_limit"` 调整。
- 如需重置上下文，删除 `~/.trae/history.jsonl` 即可。

### 内置技能

- **系统配置**：当查询“我的机器是什么配置”等问题时，Trae 会自动运行本地 Python 脚本整理 CPU、内存、GPU、磁盘等信息，并以表格形式输出。
- **数据库凭据提醒**：如果请求诸如“mysql 目前有几个数据库”，Trae 会优先提示需要提供 MySQL 连接信息，而不是盲目尝试连接。
- 技能优先级高于 LLM，可在离线环境下保证更可靠的回答。未来可以根据需要继续扩展。

### 支持的 LLM 提供商

- **OpenAI**: 需要安装 `openai` 库 (`pip install openai`)
- **Anthropic (Claude)**: 需要安装 `anthropic` 库 (`pip install anthropic`)
- **Qwen (阿里云 DashScope)**: 需要安装 `dashscope` 库 (`pip install dashscope`)
- **本地模型 (Ollama)**: 需要运行 Ollama 服务

## 使用方法

### 基本用法

```bash
# 查询内存使用情况
trae 帮我查询内存使用情况

# 显示文件列表
trae 显示当前目录的文件列表

# 查找文件
trae 查找所有 .log 文件

# 查看系统信息
trae 显示系统信息

# 内置技能示例
trae "我的机器是什么配置"
trae "mysql目前有几个数据库"
```

### 高级选项

```bash
# 只显示生成的命令，不执行（干运行）
trae --dry-run "查询内存使用情况"

# 指定 API 密钥
trae --api-key sk-xxx "查询内存使用情况"

# 同时指定 API 密钥和模型
trae --api-key sk-xxx --model gpt-4 "查询内存使用情况"

# 同时指定 API 密钥、提供商和模型
trae --api-key sk-xxx --provider openai --model gpt-4 "查询内存使用情况"

# 使用 Qwen 模型
trae --api-key sk-your-dashscope-key --provider qwen --model qwen-max "查询内存使用情况"

# 调整上下文窗口
trae --context-window 25 "连续查询最近一次命令的执行情况"
```

## 示例

```bash
$ trae 帮我查询内存使用情况
理解中: 帮我查询内存使用情况

生成的命令: free -h

执行中...

              total        used        free      shared  buff/cache   available
Mem:           16Gi       4.2Gi       8.1Gi       234Mi       3.7Gi        11Gi
Swap:         2.0Gi          0B       2.0Gi
```

## 安全特性

Trae 内置了危险命令检测机制，会警告您可能危险的命令（如 `rm -rf /`、格式化磁盘等），并在执行前要求确认。

## 开发

### 项目结构

```text
trae/
├── trae/
│   ├── __init__.py
│   ├── main.py          # 主入口
│   ├── agent.py         # 命令生成和执行代理
│   ├── llm_client.py    # LLM 客户端
│   └── config.py        # 配置管理
├── debian/              # Debian 打包文件
├── setup.py
├── requirements.txt
└── README.md
```

### 构建 Debian 包

#### 重要：首先安装构建依赖

```bash
sudo apt update
sudo apt install devscripts debhelper python3-all python3-setuptools python3-pip dh-python
```

**使用 Makefile 构建（推荐）**:

```bash
make deb
```

Makefile 会自动检查依赖，如果缺少会提示您安装。

**手动构建**:

```bash
debuild -us -uc
```

**安装生成的包**:

```bash
sudo dpkg -i ../trae_0.1.0-1_amd64.deb
sudo apt-get install -f  # 安装缺失的依赖
```

更多详细信息请查看 [BUILD.md](BUILD.md)

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 支持

如有问题，请访问 [GitHub Issues](https://github.com/yourusername/trae/issues)
