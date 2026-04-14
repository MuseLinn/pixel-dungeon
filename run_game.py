#!/usr/bin/env python3
"""
🎮 Pixel Dungeon - 像素地牢
新的模块化启动脚本
"""

import sys
import os

# 将当前目录添加到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixel_dungeon.__main__ import main

if __name__ == "__main__":
    main()
