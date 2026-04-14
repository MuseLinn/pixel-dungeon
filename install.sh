#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/muselinn/pixel-dungeon.git"
INSTALL_DIR="${PIXEL_DUNGEON_HOME:-$HOME/.local/share/pixel-dungeon}"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/pixel-dungeon"

cat <<'BANNER'
    ___ _         _   ___
   | _ (_)_ _____| | |   \ _  _ _ _  __ _ ___ ___ _ _
   |  _/ \ \ / -_) | | |) | || | ' \/ _` / -_) _ \ ' \
   |_| |_/_/_\___|_| |___/ \_,_|_||_\__, \___\___/_||_|
                                      |___/
              P I X E L   D U N G E O N
                   像素地牢 v1.0

BANNER

echo "==> 检查环境..."

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "错误: 未找到 Python，请先安装 Python 3.7+"
    exit 1
fi

PY_VERSION=$($PYTHON_CMD -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>/dev/null)
PY_MAJOR=$(echo "$PY_VERSION" | awk '{print $1}')
PY_MINOR=$(echo "$PY_VERSION" | awk '{print $2}')

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 7 ]; }; then
    echo "错误: Python 版本过低 ($PY_MAJOR.$PY_MINOR)，需要 >= 3.7"
    exit 1
fi

echo "   Python: $PY_MAJOR.$PY_MINOR ($PYTHON_CMD)"

if ! $PYTHON_CMD -c "import rich" >/dev/null 2>&1; then
    echo "==> 安装依赖 rich..."
    pip3 install rich 2>/dev/null || pip install rich 2>/dev/null || {
        echo "错误: 无法自动安装 rich，请手动运行: pip3 install rich"
        exit 1
    }
else
    echo "   rich: 已安装"
fi

echo "==> 安装 Pixel Dungeon 到 $INSTALL_DIR"

if [ -d "$INSTALL_DIR" ]; then
    echo "==> 目录已存在，执行更新 (git pull)..."
    cd "$INSTALL_DIR"
    git pull origin master
else
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

echo "==> 创建启动器..."
mkdir -p "$BIN_DIR"
cat > "$WRAPPER" <<'EOF'
#!/usr/bin/env bash
export PIXEL_DUNGEON_HOME="${PIXEL_DUNGEON_HOME:-$HOME/.local/share/pixel-dungeon}"
cd "$PIXEL_DUNGEON_HOME"
case "$1" in
  update)
    shift
    python3 pixel_dungeon.py --update "$@"
    ;;
  uninstall)
    shift
    python3 pixel_dungeon.py --uninstall "$@"
    ;;
  *)
    python3 pixel_dungeon.py "$@"
    ;;
esac
EOF
chmod +x "$WRAPPER"

if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "==> 添加 $BIN_DIR 到 PATH..."
    SHELL_RC=""
    if [ -n "$BASH_VERSION" ]; then
        SHELL_RC="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        SHELL_RC="$HOME/.zshrc"
    fi
    if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
        echo "export PATH=\"$BIN_DIR:\$PATH\"" >> "$SHELL_RC"
        echo "==> 已写入 $SHELL_RC，请重新加载或重启终端"
    fi
fi

echo "==> 安装完成！"
echo "   启动命令: pixel-dungeon"
echo "   安装目录: $INSTALL_DIR"
