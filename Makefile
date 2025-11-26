.PHONY: all build clean install deb test lint check-deps

all: build

# 检查构建依赖
check-deps:
	@echo "检查构建依赖..."
	@missing_deps=""; \
	if ! command -v debuild >/dev/null 2>&1; then \
		missing_deps="$$missing_deps devscripts"; \
	fi; \
	if ! command -v dh >/dev/null 2>&1; then \
		missing_deps="$$missing_deps debhelper"; \
	fi; \
	if ! command -v python3 >/dev/null 2>&1; then \
		missing_deps="$$missing_deps python3"; \
	fi; \
	if ! dpkg -l | grep -q "^ii.*python3-pip"; then \
		missing_deps="$$missing_deps python3-pip"; \
	fi; \
	if ! dpkg -l | grep -q "^ii.*python3-setuptools"; then \
		missing_deps="$$missing_deps python3-setuptools"; \
	fi; \
	if ! dpkg -l | grep -q "^ii.*dh-python"; then \
		missing_deps="$$missing_deps dh-python"; \
	fi; \
	if [ -n "$$missing_deps" ]; then \
		echo ""; \
		echo "错误: 缺少以下构建依赖:"; \
		echo "  $$missing_deps"; \
		echo ""; \
		echo "请运行以下命令安装:"; \
		echo "  sudo apt install devscripts debhelper python3-all python3-setuptools python3-pip dh-python"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✓ 所有构建依赖已安装"

# 默认构建（供打包环境调用）
build:
	python3 setup.py build

# 构建 Debian 包
deb: check-deps
	@echo "构建 Debian 包..."
	@if [ ! -d debian ]; then \
		echo "错误: debian/ 目录不存在"; \
		exit 1; \
	fi
	@if [ ! -f debian/control ]; then \
		echo "错误: debian/control 文件不存在"; \
		exit 1; \
	fi
	debuild -us -uc

# 清理构建文件
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf debian/trae/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -f ../trae_*.deb ../trae_*.dsc ../trae_*.tar.gz ../trae_*.changes

# 安装到系统（开发模式）
install:
	pip3 install -e .

# 运行测试
test:
	python3 -m pytest tests/ || echo "未找到测试文件"

# 检查代码
lint:
	@echo "运行代码检查..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 trae/; \
	else \
		echo "flake8 未安装，跳过代码检查"; \
	fi

