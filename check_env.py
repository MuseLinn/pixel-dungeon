#!/usr/bin/env python3
"""
🎮 Pixel Dungeon 环境检测工具
现在调用 launcher.py 显示现代化的TUI界面
"""

import sys
import os

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.join(script_dir, "launcher.py")
    
    if os.path.exists(launcher_path):
        # 执行启动器
        os.execv(sys.executable, [sys.executable, launcher_path] + sys.argv[1:])
    else:
        print("错误：未找到 launcher.py")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(0)
