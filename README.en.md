# Trae

> Natural-language operations co-pilot for Linux terminals, equipped with built-in skills, dangerous command guards, and a complete Debian packaging toolchain.

Trae lets you describe the desired outcome in Chinese or English, then plans and executes safe shell commands automatically. Key outputs are written back to a rolling history so follow-up questions like “what did you just run?” always work.

- Prefer Chinese docs? See [`README.md`](README.md).
- Need the short version? Check [`QUICKSTART.md`](QUICKSTART.md).
- Packaging workflow lives in [`BUILD.md`](BUILD.md).

---

## Table of Contents

1. [Highlights](#highlights)  
2. [Architecture](#architecture)  
3. [Installation](#installation)  
4. [Quick Start](#quick-start)  
5. [CLI Flags](#cli-flags)  
6. [Configuration & ENV](#configuration--env)  
7. [LLM Providers](#llm-providers)  
8. [Skills & Safety](#skills--safety)  
9. [Context Memory](#context-memory)  
10. [Build & Release](#build--release)  
11. [Testing](#testing)  
12. [Troubleshooting](#troubleshooting)  
13. [Project Layout](#project-layout)  
14. [Contributing](#contributing)  
15. [License](#license)

---

## Highlights

- 🤖 **LLM-powered planner** – turns natural language into an actionable plan plus shell command.
- 🧩 **Built-in skills first** – common requests such as “What’s my hardware config?” or “Remind me about MySQL creds” run offline without hitting an LLM.
- ⚙️ **Auto execution** – plans with intent `run_command` are executed automatically, optionally followed by an LLM summary.
- 🛡️ **Safety rails** – regex-based detector blocks dangerous commands (`rm -rf /`, `dd if=...`, `mkfs`, pipes to `sh`, etc.) and asks for confirmation.
- 🧠 **Context memory** – last 50 interactions are persisted and truncated intelligently for follow-up questions.
- 🔌 **Provider-agnostic** – ships with clients for OpenAI, Anthropic, Qwen/DashScope, and local Ollama.
- 📦 **Production tooling** – Debian packaging assets, Makefile dependency checks, `setup.py`, man page, and smoke tests.

---

## Architecture

| Module | Responsibility |
| --- | --- |
| `trae/main.py` | CLI entry point that parses args, loads config, invokes `CommandAgent`. |
| `trae/agent.py` | Orchestrates skill routing, LLM planning, command execution, summarization, history logging. |
| `trae/llm_client.py` | Unified `generate()` interface for multiple providers. |
| `trae/skills.py` | Built-in deterministic skills (system info, MySQL reminder, follow-up analysis). |
| `trae/history.py` | JSONL context manager with output truncation and rotation. |
| `debian/` | Packaging controls, maintainer scripts, man page. |
| `test_trae.py` | LLM-free smoke tests for config, skills, history, safety checks. |

Process overview:

```text
Natural language -> skill matcher?
    └─ yes: return SkillResult
    └─ no: build planning prompt -> LLM JSON plan -> safety gate -> execute -> optional summary -> persist history
```

---

## Installation

### 1. PPA / apt (recommended)

```bash
sudo add-apt-repository ppa:wangrui9527/trae
sudo apt update
sudo apt install trae
```

### 2. Build Debian package from source

See `QUICKSTART.md` for the full walkthrough.

```bash
sudo apt update
sudo apt install devscripts debhelper python3-all python3-setuptools python3-pip dh-python

git clone https://github.com/812781385/trae.git
cd trae
make deb
sudo dpkg -i ../trae_0.1.0_all.deb
sudo apt-get install -f
```

### 3. Developer mode

```bash
git clone https://github.com/812781385/trae.git
cd trae
pip3 install -e .[openai]     # add anthropic/qwen/all extras as needed
```

> `pip install -e .` installs the Python package only; Debian artifacts are produced via `make deb`.

---

## Quick Start

```bash
# Query memory usage
trae help me check memory usage

# Dry run (show command only)
trae --dry-run "list *.log under current directory"

# Built-in system info skill
trae "what is my machine configuration"

# Ask about last action
trae "what command did you just run"
```

Typical output:

```text
Understanding: help me check memory usage

Plan: run free -h to inspect memory utilization

Command: free -h

Running...
(command output)

Summary: The host has 16Gi RAM with roughly 4Gi in use.
```

---

## CLI Flags

| Flag | Description |
| --- | --- |
| `query` | Required natural-language description (spaces allowed). |
| `--dry-run` | Print the generated command/plan without executing. |
| `--api-key` | Override API key for this invocation. |
| `--provider` | LLM provider: `openai`, `anthropic`, `qwen`, `dashscope`, `local`. |
| `--model` | Model name (`gpt-4o-mini`, `claude-3-sonnet`, `qwen-max`, `llama2`, ...). |
| `--context-window` | Override history size (>=1). |

Priority: CLI args > environment variables > config file defaults.

---

## Configuration & ENV

### Environment variables

```bash
export TRAE_API_KEY="sk-xxx"
export TRAE_PROVIDER="qwen"              # openai / anthropic / qwen / dashscope / local
export TRAE_MODEL="qwen3-max"
export TRAE_CONTEXT_WINDOW="50"
export TRAE_CONTEXT_OUTPUT_LIMIT="2000"
export TRAE_HISTORY_PATH="$HOME/.trae/history.jsonl"   # optional
export TRAE_DEBUG=1                                    # verbose logs
```

### Config file

`~/.trae/config.json`:

```json
{
  "api_key": "sk-xxx",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "context_window": 50,
  "context_output_limit": 2000,
  "command_timeout": 30,
  "ollama_url": "http://localhost:11434/api/generate"
}
```

### CLI override example

```bash
trae --provider qwen --model qwen-max --api-key sk-dashscope "check disk usage"
```

---

## LLM Providers

| Provider | Dependency | Notes |
| --- | --- | --- |
| OpenAI | `pip install openai` | Chat Completions API for GPT‑3.5/4/4o families. |
| Anthropic | `pip install anthropic` | Claude Messages API. |
| Qwen / DashScope | `pip install dashscope` | AliCloud DashScope API; set provider to `qwen` or `dashscope`. |
| Local (Ollama) | `pip install requests` | Calls `POST /api/generate` on local Ollama; API key can be dummy. |

Extend `LLMClient` to add more vendors.

---

## Skills & Safety

### Built-in skills

- **SystemInfoSkill** – prints CPU/RAM/GPU/disk info with a local Python snippet.
- **MysqlInfoSkill** – intercepts MySQL-related questions and asks for credentials instead of guessing.
 - **FollowupAnalysisSkill** – handles “Is 64 GB enough?”, “What was the previous command?”, “Explain that output.” using recent history.

Skills fire before any LLM call, guaranteeing deterministic answers offline.

### Dangerous command guard

- Blocks patterns containing `rm -rf`, `dd if=`, `mkfs`, `fdisk`, redirection to `/dev/`, or piping into `sh`/`bash`.
- Prompts `Continue? (y/N)`; default is cancel.

---

## Context Memory

- Persisted in `~/.trae/history.jsonl` (configurable path).
- Each entry stores `query`, `command`, and truncated `output`.
- `context_window` controls max entries; `context_output_limit` trims long outputs by keeping the head & tail separated by `...`.
- Delete the file or set a new path to reset the conversation history.

---

## Build & Release

All packaging scripts target Debian/Ubuntu.

1. **Check dependencies**

   ```bash
   make check-deps
   ```

2. **Build package**

   ```bash
   make deb            # wraps debuild -us -uc
   ```

3. **Clean artifacts**

   ```bash
   make clean
   ```

4. **Developer helpers**

   ```bash
   make install        # pip3 install -e .
   make lint           # flake8 trae/
   make test           # placeholder – runs pytest tests/
   ```

Generated `.deb` files appear one directory above the repo (e.g., `../trae_0.1.0-1_amd64.deb`).

---

## Testing

`test_trae.py` verifies:

- Config loading (`get_config`)
- Agent initialization & dangerous command detection
- Context trimming logic
- Skill routing behavior

Run:

```bash
python3 test_trae.py
```

Additional suites can be added under `tests/` and executed with `pytest`.

---

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Error: missing API key` | Set `TRAE_API_KEY` or pass `--api-key`. |
| `ModuleNotFoundError: openai` | Install the matching provider library (`pip install openai`, etc.). |
| `bash: /usr/local/bin/trae: No such file` | Run `hash -r` or open a new shell after installing the Debian package so PATH cache refreshes (see `QUICKSTART.md`). |
| Command timeout/failure | Inspect CLI output / `~/.trae/history.jsonl`, enable `TRAE_DEBUG=1`, retry. |
| `git push` blocked | Configure proxy/certificates or switch to SSH. |

Refer to `QUICKSTART.md` and `BUILD.md` for extended troubleshooting.

---

## Project Layout

```text
trae/
├── README.md / README.en.md
├── QUICKSTART.md
├── BUILD.md
├── INSTALL.md / PROJECT_STRUCTURE.md / ...
├── Makefile
├── requirements.txt
├── setup.py
├── trae/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── llm_client.py
│   ├── config.py
│   ├── history.py
│   └── skills.py
├── debian/
├── trae.1
└── test_trae.py
```

---

## Contributing

- Issues & PRs are welcome: <https://github.com/812781385/trae/issues>  
- Please include use cases, repro steps, and logs.  
- Interested in adding new skills or providers? Study `SkillManager` and `LLMClient`.

---

## License

Trae is released under the [Apache License 2.0](LICENSE). Unless stated otherwise, contributions are licensed under the same terms.

---

Happy hacking! 🎉

