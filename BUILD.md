# 构建和打包指南

## 构建 Debian 包

### ⚠️ 重要：安装构建依赖

在构建之前，**必须先安装以下依赖**：

```bash
sudo apt update
sudo apt install devscripts debhelper python3-all python3-setuptools python3-pip dh-python
```

如果缺少这些依赖，`make deb` 会显示错误并提示您安装。

### 构建步骤

1. **使用 Makefile（推荐）**:
```bash
make deb
```

Makefile 会自动检查依赖，如果缺少会提示您安装。

2. **手动构建**:
```bash
debuild -us -uc
```

构建完成后，`.deb` 文件将生成在父目录中。

### 安装构建的包

```bash
sudo dpkg -i ../trae_0.1.0-1_amd64.deb
```

如果缺少依赖，运行：
```bash
sudo apt-get install -f
```

## 创建 APT 仓库（可选）

如果您想创建自己的 APT 仓库以便通过 `apt install trae` 安装：

### 1. 创建仓库结构

```bash
mkdir -p repo/pool/main/t/trae
mkdir -p repo/dists/stable/main/binary-amd64
```

### 2. 复制 .deb 文件

```bash
cp ../trae_0.1.0-1_amd64.deb repo/pool/main/t/trae/
```

### 3. 生成 Packages 文件

```bash
cd repo
dpkg-scanpackages pool/ > dists/stable/main/binary-amd64/Packages
gzip -k dists/stable/main/binary-amd64/Packages
```

### 4. 生成 Release 文件

```bash
apt-ftparchive release dists/stable/ > dists/stable/Release
```

### 5. 添加仓库到系统

在 `/etc/apt/sources.list.d/trae.list` 中添加：
```
deb [trusted=yes] file:///path/to/repo stable main
```

然后运行：
```bash
sudo apt update
sudo apt install trae
```

## 使用 GitHub Releases

您也可以将 `.deb` 文件上传到 GitHub Releases，用户可以通过以下方式安装：

```bash
wget https://github.com/yourusername/trae/releases/download/v0.1.0/trae_0.1.0-1_amd64.deb
sudo dpkg -i trae_0.1.0-1_amd64.deb
sudo apt-get install -f
```

## 开发安装

对于开发，可以直接安装：

```bash
pip3 install -e .
```

或者使用 Makefile：

```bash
make install
```

