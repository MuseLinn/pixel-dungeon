"""🎮 Pixel Dungeon - 像素地牢游戏

现代化的 Roguelike TUI 游戏，使用 Rich 库构建。
"""

__version__ = "1.0.0"
__author__ = "Pixel Dungeon Team"

from .config import CONFIG
from .assets import GAME_ASSETS, CHARACTERS

__all__ = ["CONFIG", "GAME_ASSETS", "CHARACTERS"]
