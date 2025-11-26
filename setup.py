"""
Trae 安装脚本
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="trae",
    version="0.1.0",
    description="自然语言 Linux 命令执行工具",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Trae Team",
    author_email="trae@example.com",
    url="https://github.com/yourusername/trae",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    extras_require={
        "openai": ["openai>=1.0.0"],
        "anthropic": ["anthropic>=0.18.0"],
        "qwen": ["dashscope>=1.17.0"],
        "dashscope": ["dashscope>=1.17.0"],
        "all": ["openai>=1.0.0", "anthropic>=0.18.0", "dashscope>=1.17.0"],
    },
    entry_points={
        "console_scripts": [
            "trae=trae.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
)

