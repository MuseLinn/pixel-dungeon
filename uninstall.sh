#!/usr/bin/env bash
set -e

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
                   像素地牢

BANNER

echo "==> 卸载 Pixel Dungeon"

if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo "   已删除 $INSTALL_DIR"
else
    echo "   安装目录不存在"
fi

if [ -f "$WRAPPER" ]; then
    rm -f "$WRAPPER"
    echo "   已删除启动器 $WRAPPER"
fi

for rc in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$rc" ]; then
        sed -i '/pixel-dungeon/d' "$rc"
        echo "   已清理 $rc"
    fi
done

echo "==> 卸载完成"
