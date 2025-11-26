# Trae 安装指南

## 通过 apt 安装（推荐方法）

### 前提条件

要使用 `apt install trae`，您需要：

1. **构建 Debian 包**:
```bash
cd /path/to/trae
make deb
```

2. **创建 APT 仓库**（可选）:
   参考 `BUILD.md` 中的"创建 APT 仓库"部分

3. **或者直接安装 .deb 文件**:
```bash
sudo dpkg -i ../trae_0.1.0-1_amd64.deb
sudo apt-get install -f
```

### 从 APT 仓库安装

如果您已经设置了 APT 仓库：

```bash
sudo apt update
sudo apt install trae
```

## 开发安装

### 使用 pip

```bash
pip3 install -e .
```

### 使用 Makefile

```bash
make install
```

## 配置

安装后，需要配置 LLM API 密钥：

```bash
export TRAE_API_KEY="your-api-key"
```

或创建配置文件 `~/.trae/config.json`:

```json
{
  "api_key": "your-api-key",
  "provider": "openai",
  "model": "gpt-3.5-turbo"
}
```

## 验证安装

```bash
trae --help
```

应该显示帮助信息。

## 安装 LLM 库

根据您使用的 LLM 提供商：

```bash
# OpenAI
pip3 install openai

# Anthropic
pip3 install anthropic

# 或全部安装
pip3 install -r requirements.txt
```

## 卸载

### 通过 apt 卸载

```bash
sudo apt remove trae
```

### 通过 pip 卸载

```bash
pip3 uninstall trae
```

## 故障排除

### 命令未找到

确保 `/usr/bin/trae` 存在且可执行：
```bash
which trae
ls -l /usr/bin/trae
```

### 权限问题

如果遇到权限问题：
```bash
sudo chmod +x /usr/bin/trae
```

### Python 模块未找到

确保 Python 包已正确安装：
```bash
python3 -c "import trae; print(trae.__version__)"
```

