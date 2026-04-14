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

    name_key: str
    description_key: str
    effect: Callable
    rarity: str
    icon: str

    @property
    def name(self) -> str:
        from ..utils.i18n import _

        return _(self.name_key)

    @property
    def description(self) -> str:
        from ..utils.i18n import _

        return _(self.description_key)

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

    ALL_UPGRADES = [
        Upgrade(
            "hp_boost",
            "hp_boost_desc",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20)
            ),
            "common",
            "♥",
        ),
        Upgrade(
            "atk_boost",
            "atk_boost_desc",
            lambda p: setattr(p, "atk", p.atk + 3),
            "common",
            "⚔",
        ),
        Upgrade(
            "regen_boost",
            "regen_boost_desc",
            lambda p: setattr(p, "regen", p.regen + 2),
            "common",
            "✚",
        ),
        Upgrade(
            "iron_skin",
            "iron_skin_desc",
            lambda p: setattr(p, "defense", p.defense + 2),
            "common",
            "🛡",
        ),
        Upgrade(
            "agility",
            "agility_desc",
            lambda p: setattr(p, "dodge", getattr(p, "dodge", 0) + 10),
            "common",
            "🏃",
        ),
        Upgrade(
            "poison_weapon",
            "poison_weapon_desc",
            lambda p: setattr(p, "poison_atk", getattr(p, "poison_atk", 0) + 3),
            "common",
            "🐍",
        ),
        Upgrade(
            "life_steal",
            "life_steal_desc",
            lambda p: setattr(p, "lifesteal", p.lifesteal + 10),
            "rare",
            "♥",
        ),
        Upgrade(
            "crit_boost",
            "crit_boost_desc",
            lambda p: setattr(p, "crit", p.crit + 15),
            "rare",
            "⚡",
        ),
        Upgrade(
            "berserker",
            "berserker_desc",
            lambda p: (
                setattr(p, "atk", p.atk + 5)
                or setattr(p, "defense", max(0, p.defense - 1))
            ),
            "rare",
            "🪓",
        ),
        Upgrade(
            "titan",
            "titan_desc",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 50)
                or setattr(p, "hp", p.hp + 50)
                or setattr(p, "atk", max(1, p.atk - 2))
            ),
            "rare",
            "🗿",
        ),
        Upgrade(
            "double_strike",
            "double_strike_desc",
            lambda p: setattr(p, "double_hit", getattr(p, "double_hit", 0) + 25),
            "rare",
            "⚔️",
        ),
        Upgrade(
            "thorns_armor",
            "thorns_armor_desc",
            lambda p: setattr(p, "thorns", getattr(p, "thorns", 0) + 15),
            "rare",
            "🌵",
        ),
        Upgrade(
            "vampire",
            "vampire_desc",
            lambda p: setattr(p, "lifesteal", p.lifesteal + 25),
            "epic",
            "🧛",
        ),
        Upgrade(
            "fury", "fury_desc", lambda p: setattr(p, "crit", p.crit + 30), "epic", "🌀"
        ),
        Upgrade(
            "soul_drain",
            "soul_drain_desc",
            lambda p: setattr(p, "soul_drain", True),
            "epic",
            "💀",
        ),
        Upgrade(
            "thunder_strike",
            "thunder_strike_desc",
            lambda p: setattr(p, "crit_mult", getattr(p, "crit_mult", 2.0) + 1.0),
            "epic",
            "⚡",
        ),
        Upgrade(
            "immortal",
            "immortal_desc",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 100)
                or setattr(p, "hp", p.hp + 100)
                or setattr(p, "regen", p.regen + 5)
            ),
            "legendary",
            "👑",
        ),
        Upgrade(
            "destroyer",
            "destroyer_desc",
            lambda p: setattr(p, "atk", p.atk + 15) or setattr(p, "crit", p.crit + 20),
            "legendary",
            "☠",
        ),
        Upgrade(
            "time_walker",
            "time_walker_desc",
            lambda p: setattr(p, "dodge", getattr(p, "dodge", 0) + 30),
            "legendary",
            "🌌",
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
