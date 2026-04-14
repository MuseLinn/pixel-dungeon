#!/usr/bin/env python3
"""商店系统模块"""

from dataclasses import dataclass
from typing import Callable, List
import random


@dataclass
class ShopItem:
    """商店商品"""

    item_key: str
    name_key: str
    description_key: str
    price: int
    icon: str
    effect: Callable
    repeatable: bool = True  # 是否可以重复购买
    purchased: bool = False

    @property
    def name(self) -> str:
        from ..utils.i18n import _

        return _(self.name_key)

    @property
    def description(self) -> str:
        from ..utils.i18n import _

        return _(self.description_key)

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
            "potion_hp",
            "potion_hp",
            "potion_hp_desc",
            20,
            "♥",
            lambda p: setattr(p, "hp", min(p.max_hp, p.hp + 30)),
            repeatable=True,
        ),
        ShopItem(
            "scroll_power",
            "scroll_power",
            "scroll_power_desc",
            50,
            "⚔",
            lambda p: setattr(p, "atk", p.atk + 2),
            repeatable=True,
        ),
        ShopItem(
            "scroll_body",
            "scroll_body",
            "scroll_body_desc",
            50,
            "♥",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20)
            ),
            repeatable=True,
        ),
        ShopItem(
            "potion_iron",
            "potion_iron",
            "potion_iron_desc",
            40,
            "🛡",
            lambda p: setattr(p, "defense", p.defense + 1),
            repeatable=True,
        ),
        ShopItem(
            "scroll_rage",
            "scroll_rage",
            "scroll_rage_desc",
            60,
            "⚡",
            lambda p: setattr(p, "crit", p.crit + 10),
            repeatable=True,
        ),
        ShopItem(
            "essence_life",
            "essence_life",
            "essence_life_desc",
            100,
            "✦",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 50) or setattr(p, "hp", p.hp + 50)
            ),
            repeatable=True,
        ),
        ShopItem(
            "bomb",
            "bomb",
            "bomb_desc",
            45,
            "💣",
            lambda p: setattr(p, "bomb_charges", getattr(p, "bomb_charges", 0) + 1),
            repeatable=True,
        ),
        ShopItem(
            "scroll_teleport",
            "scroll_teleport",
            "scroll_teleport_desc",
            80,
            "📜",
            lambda p: setattr(p, "teleport_ready", True),
            repeatable=False,
        ),
        ShopItem(
            "potion_invincible",
            "potion_invincible",
            "potion_invincible_desc",
            120,
            "🛡",
            lambda p: setattr(
                p, "invincible_charges", getattr(p, "invincible_charges", 0) + 1
            ),
            repeatable=True,
        ),
        ShopItem(
            "coin_luck",
            "coin_luck",
            "coin_luck_desc",
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
        from ..utils.i18n import _

        if not self.items:
            return False, _("shop_empty")

        item = self.items[self.selected_index]

        if not item.repeatable and item.purchased:
            return False, _("sold_out", item.name)

        if player.gold < item.price:
            return False, _("not_enough_gold", item.price)

        if item.buy(player):
            return True, _("bought", item.name)

        return False, _("buy_failed")

    def get_selected(self) -> ShopItem | None:
        """获取当前选中的商品"""
        if not self.items:
            return None
        return self.items[self.selected_index]
