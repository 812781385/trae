# Trae 项目结构

```
trae/
├── trae/                    # 主 Python 包
│   ├── __init__.py          # 包初始化
│   ├── main.py              # CLI 入口点
│   ├── agent.py             # 命令生成和执行代理
│   ├── llm_client.py        # LLM 客户端（支持多种提供商）
│   └── config.py            # 配置管理
│
├── debian/                   # Debian 打包文件
│   ├── control              # 包元数据和依赖
│   ├── rules                # 构建规则
│   ├── changelog            # 版本变更日志
│   ├── copyright            # 版权信息
│   ├── compat               # debhelper 兼容版本
│   ├── postinst             # 安装后脚本
│   ├── trae.install        # 安装文件列表
│   └── trae.manpages       # 手册页配置
│
├── setup.py                  # Python 安装脚本
├── requirements.txt          # Python 依赖
├── Makefile                 # 构建辅助脚本
├── trae.1                  # 手册页源文件
│
├── README.md                # 项目说明
├── BUILD.md                 # 构建指南
├── QUICKSTART.md            # 快速开始指南
├── PROJECT_STRUCTURE.md     # 本文件
│
├── test_trae.py            # 测试脚本
└── .gitignore               # Git 忽略文件
```

## 核心组件说明

### trae/main.py
- CLI 入口点
- 参数解析
- 用户交互
- 错误处理

### trae/agent.py
- `CommandAgent`: 核心代理类
  - 规划与意图识别 (`plan_interaction`)
  - 执行命令 (`execute_command`)
  - 危险命令检测 (`is_dangerous_command`)

### trae/llm_client.py
- `LLMClient`: LLM 客户端基类
  - 支持 OpenAI
  - 支持 Anthropic (Claude)
  - 支持本地模型 (Ollama)

### trae/config.py
- 配置管理
- 支持环境变量
- 支持配置文件 (`~/.trae/config.json`)

## 构建流程

1. **开发**: 使用 `pip install -e .` 进行开发安装
2. **打包**: 使用 `make deb` 或 `debuild -us -uc` 构建 Debian 包
3. **安装**: 使用 `dpkg -i` 安装生成的 `.deb` 文件

## 依赖关系

```
trae
├── Python 3.8+
├── requests (必需)
├── openai (可选，用于 OpenAI)
├── anthropic (可选，用于 Claude)
└── 系统依赖 (通过 apt 安装)
```

## 安装路径

安装后文件位置：
- `/usr/bin/trae` - 可执行文件
- `/usr/lib/python3/dist-packages/trae/` - Python 包
- `/usr/share/man/man1/trae.1.gz` - 手册页
- `~/.trae/config.json` - 用户配置文件

