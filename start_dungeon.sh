#!/bin/bash
# 像素地牢启动脚本 - 使用现代化的TUI启动器

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python3"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 启动TUI启动器
exec python3 launcher.py "$@"
