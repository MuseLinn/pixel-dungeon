#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/muselinn/pixel-dungeon.git"
INSTALL_DIR="${PIXEL_DUNGEON_HOME:-$HOME/.local/share/pixel-dungeon}"
BIN_DIR="$HOME/.local/bin"
WRAPPER="$BIN_DIR/pixel-dungeon"

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
