#!/usr/bin/env python3
"""玩家类模块"""

from dataclasses import dataclass, field
from typing import List, Tuple

from ..assets import get_player_asset


@dataclass
class Player:
    """玩家实体"""

    x: int = 1
    y: int = 1
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    defense: int = 0
    level: int = 1
    exp: int = 0
    exp_next: int = 50
    gold: int = 0
    crit: int = 0  # 暴击率百分比
    lifesteal: int = 0  # 生命偷取百分比
    regen: int = 0  # 每回合恢复

    # 动画相关
    frame: int = field(default=0, repr=False)
    char_set: str = "default"

    @classmethod
    def create(cls, char_set: str = "default") -> "Player":
        """创建指定类型的玩家角色"""
        asset = get_player_asset(char_set)
        return cls(
            hp=asset["hp"],
            max_hp=asset["hp"],
            atk=asset["atk"],
            defense=asset["defense"],
            crit=asset["crit"],
            lifesteal=asset["lifesteal"],
            regen=asset["regen"],
            char_set=char_set,
        )

    def animate(self) -> None:
        """更新动画帧"""
        self.frame = (self.frame + 1) % 40

    def get_render_sprite(self) -> Tuple[List[str], str]:
        asset = get_player_asset(self.char_set)
        if self.frame < 20:
            return asset["sprite"], asset["style"]
        else:
            return asset["alt_sprite"], asset["style_alt"]

    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际伤害值"""
        # 防御减伤公式
        if self.defense > 0:
            damage = max(1, int(damage * (1 - self.defense / (self.defense + 10))))

        self.hp = max(0, self.hp - damage)
        return damage

    def heal(self, amount: int) -> int:
        """恢复生命，返回实际恢复值"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp

    def add_exp(self, amount: int) -> bool:
        """增加经验，返回是否升级"""
        self.exp += amount
        if self.exp >= self.exp_next:
            return True
        return False

    def level_up(self) -> None:
        """升级"""
        self.exp -= self.exp_next
        self.exp_next = int(self.exp_next * 1.5)
        self.level += 1
        self.max_hp += 10
        self.hp += 10
        self.atk += 2

    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.hp > 0

    def regen_hp(self) -> int:
        """生命恢复，返回实际恢复值"""
        if self.regen > 0 and self.hp < self.max_hp:
            return self.heal(self.regen)
        return 0

    def get_hp_percent(self) -> float:
        """获取生命值百分比"""
        return self.hp / self.max_hp if self.max_hp > 0 else 0

    def get_exp_percent(self) -> float:
        """获取经验值百分比"""
        return self.exp / self.exp_next if self.exp_next > 0 else 0
