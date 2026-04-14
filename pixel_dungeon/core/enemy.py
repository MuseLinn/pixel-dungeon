#!/usr/bin/env python3
"""敌人类模块"""

from dataclasses import dataclass, field
from typing import List, Tuple

from ..assets import get_enemy_asset


@dataclass
class Enemy:
    """敌人实体"""

    enemy_type: str
    name: str
    x: int
    y: int
    hp: int
    max_hp: int
    atk: int
    exp: int
    gold: int

    # 状态效果
    flash: int = field(default=0, repr=False)  # 受击闪烁帧数
    frame: int = field(default=0, repr=False)  # 动画帧

    def animate(self) -> None:
        """更新动画帧"""
        self.frame = (self.frame + 1) % 8
        if self.flash > 0:
            self.flash -= 1

    def get_render_sprite(self) -> Tuple[List[str], str]:
        if self.flash > 0:
            from ..config import CONFIG

            block = ["████"] * CONFIG.tile_height
            return block, "bold white"

        asset = get_enemy_asset(self.enemy_type)
        if self.frame < 4:
            return asset["sprite"], asset["style"]
        else:
            return asset["alt_sprite"], asset["style_alt"]

    def take_damage(self, damage: int) -> None:
        """受到伤害"""
        self.hp = max(0, self.hp - damage)
        self.flash = 3  # 闪烁3帧

    def is_alive(self) -> bool:
        """检查是否存活"""
        return self.hp > 0

    @classmethod
    def create(
        cls,
        enemy_type: str,
        name: str,
        x: int,
        y: int,
        base_hp: int,
        base_atk: int,
        base_exp: int,
        base_gold: int,
        floor: int,
        scale_override: float = None,
    ) -> "Enemy":
        scale = 1 + (floor - 1) * (
            scale_override if scale_override is not None else 0.15
        )
        return cls(
            enemy_type=enemy_type,
            name=name,
            x=x,
            y=y,
            hp=int(base_hp * scale),
            max_hp=int(base_hp * scale),
            atk=int(base_atk * scale),
            exp=int(base_exp * scale),
            gold=int(base_gold * scale),
        )
