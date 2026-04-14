#!/usr/bin/env python3
"""
Pixel Dungeon 异常定义模块
"""


class GameException(Exception):
    """游戏基础异常"""

    pass


class TerminalRestoreError(GameException):
    """终端恢复失败"""

    pass


class ValidationError(GameException):
    """输入验证失败"""

    pass


class SaveLoadError(GameException):
    """保存/加载失败"""

    pass


class AchievementError(GameException):
    """成就系统错误"""

    pass
