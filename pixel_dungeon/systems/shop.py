#!/usr/bin/env python3
"""商店系统模块"""

from dataclasses import dataclass
from typing import Callable, List
import random


@dataclass
class ShopItem:
    """商店商品"""

    name: str
    description: str
    price: int
    icon: str
    effect: Callable
    repeatable: bool = True  # 是否可以重复购买
    purchased: bool = False

    def buy(self, player) -> bool:
        """购买商品，返回是否成功"""
        if not self.repeatable and self.purchased:
            return False
        if player.gold < self.price:
            return False

        player.gold -= self.price
        self.effect(player)
        if not self.repeatable:
            self.purchased = True
        return True


class Shop:
    """商店管理器"""

    ALL_ITEMS = [
        ShopItem(
            "生命药水",
            "恢复 30 HP",
            20,
            "♥",
            lambda p: setattr(p, "hp", min(p.max_hp, p.hp + 30)),
            repeatable=True,
        ),
        ShopItem(
            "力量卷轴",
            "攻击力 +2",
            50,
            "⚔",
            lambda p: setattr(p, "atk", p.atk + 2),
            repeatable=True,
        ),
        ShopItem(
            "体质卷轴",
            "最大生命 +20",
            50,
            "♥",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20)
            ),
            repeatable=True,
        ),
        ShopItem(
            "铁皮药剂",
            "防御 +1",
            40,
            "🛡",
            lambda p: setattr(p, "defense", p.defense + 1),
            repeatable=True,
        ),
        ShopItem(
            "狂暴卷轴",
            "暴击率 +10%",
            60,
            "⚡",
            lambda p: setattr(p, "crit", p.crit + 10),
            repeatable=True,
        ),
        ShopItem(
            "生命精华",
            "最大生命 +50",
            100,
            "✦",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 50) or setattr(p, "hp", p.hp + 50)
            ),
            repeatable=True,
        ),
        ShopItem(
            "炸弹",
            "下次战斗造成50点爆炸伤害",
            45,
            "💣",
            lambda p: setattr(p, "bomb_charges", getattr(p, "bomb_charges", 0) + 1),
            repeatable=True,
        ),
        ShopItem(
            "传送卷轴",
            "立即传送到出口附近",
            80,
            "📜",
            lambda p: setattr(p, "teleport_ready", True),
            repeatable=False,
        ),
        ShopItem(
            "无敌药水",
            "下一场战斗免疫伤害",
            120,
            "🛡",
            lambda p: setattr(
                p, "invincible_charges", getattr(p, "invincible_charges", 0) + 1
            ),
            repeatable=True,
        ),
        ShopItem(
            "幸运金币",
            "金币获取+20% 持续5层",
            60,
            "🍀",
            lambda p: setattr(
                p, "gold_bonus_floors", getattr(p, "gold_bonus_floors", 0) + 5
            ),
            repeatable=True,
        ),
    ]

    def __init__(self, item_count: int = 5):
        self.item_count = item_count
        self.items: List[ShopItem] = []
        self.selected_index = 0
        self.refresh()

    def refresh(self) -> None:
        """刷新商店商品"""
        self.items = random.sample(
            self.ALL_ITEMS, min(self.item_count, len(self.ALL_ITEMS))
        )
        self.selected_index = 0

    def select_next(self) -> None:
        """选择下一个商品"""
        self.selected_index = (self.selected_index + 1) % len(self.items)

    def select_prev(self) -> None:
        """选择上一个商品"""
        self.selected_index = (self.selected_index - 1) % len(self.items)

    def buy_selected(self, player) -> tuple[bool, str]:
        """购买选中的商品"""
        if not self.items:
            return False, "商店为空"

        item = self.items[self.selected_index]

        if not item.repeatable and item.purchased:
            return False, f"{item.name} 已售罄"

        if player.gold < item.price:
            return False, f"金币不足 (需要 {item.price}G)"

        if item.buy(player):
            return True, f"购买了 {item.name}！"

        return False, "购买失败"

    def get_selected(self) -> ShopItem | None:
        """获取当前选中的商品"""
        if not self.items:
            return None
        return self.items[self.selected_index]
