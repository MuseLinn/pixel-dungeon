#!/usr/bin/env python3
"""成就系统模块"""

from dataclasses import dataclass
from typing import Callable, List, Set, Dict
from enum import Enum, auto


class AchievementTier(Enum):
    """成就等级"""

    BRONZE = auto()  # 铜
    SILVER = auto()  # 银
    GOLD = auto()  # 金
    PLATINUM = auto()  # 白金


@dataclass
class Achievement:
    """成就定义"""

    id: str
    name: str
    description: str
    tier: AchievementTier
    icon: str
    condition: Callable
    secret: bool = False  # 隐藏成就

    def get_tier_style(self) -> str:
        """获取等级样式"""
        styles = {
            AchievementTier.BRONZE: "#CD7F32",  # 铜色
            AchievementTier.SILVER: "#C0C0C0",  # 银色
            AchievementTier.GOLD: "#FFD700",  # 金色
            AchievementTier.PLATINUM: "#E5E4E2",  # 白金
        }
        return styles.get(self.tier, "white")


class AchievementManager:
    """成就管理器"""

    ACHIEVEMENTS = [
        # 探索类
        Achievement(
            "first_blood",
            "初出茅庐",
            "击败第一个敌人",
            AchievementTier.BRONZE,
            "🗡️",
            lambda g: g.stats.get("enemies_killed", 0) >= 1,
        ),
        Achievement(
            "dungeon_crawler",
            "地牢行者",
            "到达第5层",
            AchievementTier.BRONZE,
            "🪜",
            lambda g: g.floor >= 5,
        ),
        Achievement(
            "deep_diver",
            "深渊探险者",
            "到达第10层",
            AchievementTier.SILVER,
            "🕳️",
            lambda g: g.floor >= 10,
        ),
        Achievement(
            "master_explorer",
            "地牢大师",
            "到达第20层",
            AchievementTier.GOLD,
            "👑",
            lambda g: g.floor >= 20,
        ),
        # 战斗类
        Achievement(
            "monster_slayer",
            "怪物猎人",
            "击败50个敌人",
            AchievementTier.BRONZE,
            "⚔️",
            lambda g: g.stats.get("enemies_killed", 0) >= 50,
        ),
        Achievement(
            "mass_murderer",
            "百人斩",
            "击败100个敌人",
            AchievementTier.SILVER,
            "💀",
            lambda g: g.stats.get("enemies_killed", 0) >= 100,
        ),
        Achievement(
            "crit_master",
            "暴击大师",
            "造成一次超过50点的暴击伤害",
            AchievementTier.SILVER,
            "⚡",
            lambda g: g.stats.get("max_crit_damage", 0) >= 50,
        ),
        # 生存类
        Achievement(
            "survivor",
            "幸存者",
            "在生命值低于10时击败敌人",
            AchievementTier.BRONZE,
            "❤️",
            lambda g: g.stats.get("close_call_wins", 0) >= 1,
        ),
        Achievement(
            "tank",
            "钢铁之躯",
            "防御达到20",
            AchievementTier.SILVER,
            "🛡️",
            lambda g: g.player.defense >= 20,
        ),
        Achievement(
            "immortal",
            "不朽者",
            "在一次游戏中恢复超过500生命值",
            AchievementTier.GOLD,
            "✨",
            lambda g: g.stats.get("total_healed", 0) >= 500,
        ),
        # 财富类
        Achievement(
            "collector",
            "收藏家",
            "累积获得500金币",
            AchievementTier.BRONZE,
            "💰",
            lambda g: g.stats.get("total_gold_earned", 0) >= 500,
        ),
        Achievement(
            "millionaire",
            "百万富翁",
            "同时拥有1000金币",
            AchievementTier.SILVER,
            "💎",
            lambda g: g.player.gold >= 1000,
        ),
        # 升级类
        Achievement(
            "power_gamer",
            "力量玩家",
            "攻击力达到50",
            AchievementTier.SILVER,
            "🔥",
            lambda g: g.player.atk >= 50,
        ),
        Achievement(
            "vampire_lord",
            "吸血鬼领主",
            "生命偷取达到50%",
            AchievementTier.GOLD,
            "🧛",
            lambda g: g.player.lifesteal >= 50,
        ),
        # 隐藏成就
        Achievement(
            "pacifist",
            "和平主义者",
            "到达第3层且不击杀任何敌人",
            AchievementTier.GOLD,
            "🕊️",
            lambda g: g.floor >= 3 and g.stats.get("enemies_killed", 0) == 0,
            secret=True,
        ),
        Achievement(
            "speed_runner",
            "速通者",
            "在10分钟内到达第10层",
            AchievementTier.PLATINUM,
            "⏱️",
            lambda g: g.floor >= 10 and g.stats.get("play_time", 0) < 600,
            secret=True,
        ),
    ]

    def __init__(self):
        self.unlocked: Set[str] = set()
        self.new_unlocks: List[Achievement] = []  # 本次游戏新解锁的

    def check(self, game) -> List[Achievement]:
        """检查并解锁新成就"""
        self.new_unlocks = []

        for ach in self.ACHIEVEMENTS:
            if ach.id not in self.unlocked and ach.condition(game):
                self.unlocked.add(ach.id)
                self.new_unlocks.append(ach)

        return self.new_unlocks

    def is_unlocked(self, ach_id: str) -> bool:
        """检查成就是否已解锁"""
        return ach_id in self.unlocked

    def get_progress(self, ach_id: str, game) -> tuple:
        """获取成就进度 (当前, 目标)"""
        progress_map = {
            "monster_slayer": ("enemies_killed", 50),
            "mass_murderer": ("enemies_killed", 100),
            "deep_diver": (None, 10),  # 特殊处理
            "master_explorer": (None, 20),
        }

        if ach_id in progress_map:
            stat_key, target = progress_map[ach_id]
            if stat_key:
                current = game.stats.get(stat_key, 0)
            else:
                current = game.floor
            return (min(current, target), target)

        return (0, 0)

    def get_display_list(self, game) -> List[Dict]:
        """获取用于显示的成就列表"""
        result = []
        for ach in self.ACHIEVEMENTS:
            unlocked = ach.id in self.unlocked

            # 隐藏成就未解锁时显示为 ???
            if ach.secret and not unlocked:
                display_name = "???"
                display_desc = "隐藏成就"
                display_icon = "❓"
            else:
                display_name = ach.name
                display_desc = ach.description
                display_icon = ach.icon

            progress = None
            if not unlocked:
                progress = self.get_progress(ach.id, game)

            result.append(
                {
                    "id": ach.id,
                    "name": display_name,
                    "description": display_desc,
                    "tier": ach.tier,
                    "tier_style": ach.get_tier_style(),
                    "icon": display_icon,
                    "unlocked": unlocked,
                    "progress": progress,
                    "secret": ach.secret,
                }
            )

        # 按解锁状态排序（未解锁在前）
        result.sort(key=lambda x: (x["unlocked"], x["secret"]))
        return result

    def get_unlocked_count(self) -> tuple:
        """获取解锁数量 (当前, 总数)"""
        total = len(self.ACHIEVEMENTS)
        unlocked = len(self.unlocked)
        return (unlocked, total)
