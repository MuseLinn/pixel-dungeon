#!/usr/bin/env python3
"""升级系统模块"""

from dataclasses import dataclass
from typing import Callable, List
from enum import Enum, auto
import random


class Rarity(Enum):
    """升级稀有度"""

    COMMON = "common"  # 普通
    RARE = "rare"  # 稀有
    EPIC = "epic"  # 史诗
    LEGENDARY = "legendary"  # 传说


@dataclass
class Upgrade:
    """升级选项"""

    name: str
    description: str
    effect: Callable
    rarity: str
    icon: str

    def apply(self, player) -> None:
        """应用升级效果"""
        self.effect(player)

    def get_style(self) -> str:
        """根据稀有度获取样式"""
        styles = {
            "common": "white",
            "rare": "cyan",
            "epic": "magenta",
            "legendary": "yellow",
        }
        return styles.get(self.rarity, "white")


class UpgradePool:
    """升级池管理器"""

    # 稀有度权重
    WEIGHTS = {
        "common": 50,
        "rare": 30,
        "epic": 15,
        "legendary": 5,
    }

    # 所有可用升级
    ALL_UPGRADES = [
        # 普通
        Upgrade(
            "生命强化",
            "最大生命 +20",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20)
            ),
            "common",
            "♥",
        ),
        Upgrade(
            "攻击强化",
            "攻击力 +3",
            lambda p: setattr(p, "atk", p.atk + 3),
            "common",
            "⚔",
        ),
        Upgrade(
            "生命恢复",
            "每回合恢复 +2",
            lambda p: setattr(p, "regen", p.regen + 2),
            "common",
            "✚",
        ),
        Upgrade(
            "铁皮",
            "防御 +2",
            lambda p: setattr(p, "defense", p.defense + 2),
            "common",
            "🛡",
        ),
        # 稀有
        Upgrade(
            "生命偷取",
            "攻击恢复 10%伤害",
            lambda p: setattr(p, "lifesteal", p.lifesteal + 10),
            "rare",
            "♥",
        ),
        Upgrade(
            "暴击",
            "暴击率 +15%",
            lambda p: setattr(p, "crit", p.crit + 15),
            "rare",
            "⚡",
        ),
        Upgrade(
            "狂战士",
            "攻击+5 防御-1",
            lambda p: (
                setattr(p, "atk", p.atk + 5)
                or setattr(p, "defense", max(0, p.defense - 1))
            ),
            "rare",
            "🪓",
        ),
        Upgrade(
            "泰坦",
            "生命+50 攻击-2",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 50)
                or setattr(p, "hp", p.hp + 50)
                or setattr(p, "atk", max(1, p.atk - 2))
            ),
            "rare",
            "🗿",
        ),
        # 史诗
        Upgrade(
            "吸血鬼",
            "吸血 +25%",
            lambda p: setattr(p, "lifesteal", p.lifesteal + 25),
            "epic",
            "🧛",
        ),
        Upgrade(
            "狂怒",
            "暴击率 +30%",
            lambda p: setattr(p, "crit", p.crit + 30),
            "epic",
            "🌀",
        ),
        # 传说
        Upgrade(
            "不朽",
            "生命+100 恢复+5",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 100)
                or setattr(p, "hp", p.hp + 100)
                or setattr(p, "regen", p.regen + 5)
            ),
            "legendary",
            "👑",
        ),
        Upgrade(
            "毁灭者",
            "攻击+15 暴击+20%",
            lambda p: setattr(p, "atk", p.atk + 15) or setattr(p, "crit", p.crit + 20),
            "legendary",
            "☠",
        ),
    ]

    @classmethod
    def get_random_upgrades(cls, count: int = 3) -> List[Upgrade]:
        """获取随机升级选项"""
        # 创建加权池
        weighted = []
        for upgrade in cls.ALL_UPGRADES:
            weight = cls.WEIGHTS.get(upgrade.rarity, 10)
            weighted.extend([upgrade] * weight)

        # 随机选择
        if len(weighted) < count:
            return random.sample(cls.ALL_UPGRADES, min(count, len(cls.ALL_UPGRADES)))

        return random.sample(weighted, count)
