#!/usr/bin/env python3
"""保存/加载系统模块"""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict


@dataclass
class SaveData:
    """保存数据结构"""

    version: str = "1.0"
    timestamp: str = ""
    floor: int = 1
    map_seed: int = 0
    difficulty: str = "normal"
    player_data: Dict = field(default_factory=dict)
    game_stats: Dict = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SaveData":
        """从字典创建"""
        return cls(**data)


class SaveManager:
    """保存管理器"""

    SAVE_DIR = Path.home() / ".pixel_dungeon" / "saves"
    MAX_SLOTS = 3

    def __init__(self):
        self._ensure_save_dir()

    def _ensure_save_dir(self) -> None:
        """确保保存目录存在"""
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_save_path(self, slot: int) -> Path:
        """获取保存文件路径"""
        return self.SAVE_DIR / f"save_{slot}.json"

    def save(self, game, slot: int = 0) -> bool:
        """保存游戏"""
        if not 0 <= slot < self.MAX_SLOTS:
            return False

        try:
            from ..config import CONFIG

            save_data = SaveData(
                timestamp=datetime.now().isoformat(),
                floor=game.floor,
                map_seed=game.map_seed
                if hasattr(game, "map_seed") and game.map_seed is not None
                else 0,
                difficulty=CONFIG.difficulty,
                player_data=self._serialize_player(game.player),
                game_stats=game.stats,
                achievements=list(game.achievements.unlocked)
                if hasattr(game, "achievements")
                else [],
            )

            save_path = self._get_save_path(slot)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data.to_dict(), f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            from .i18n import _

            print(f"{_('save_failed')}: {e}")
            return False

    def load(self, game, slot: int = 0) -> bool:
        """加载游戏"""
        save_path = self._get_save_path(slot)

        if not save_path.exists():
            return False

        try:
            with open(save_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            save_data = SaveData.from_dict(data)

            # 恢复游戏状态
            game.floor = save_data.floor
            game.map_seed = save_data.map_seed
            from ..config import CONFIG

            diff = save_data.difficulty
            if diff in ("easy", "normal", "hard"):
                CONFIG.difficulty = diff
            self._deserialize_player(game.player, save_data.player_data)
            game.stats = save_data.game_stats

            # 恢复成就
            if hasattr(game, "achievements"):
                game.achievements.unlocked = set(save_data.achievements)

            return True
        except Exception as e:
            from .i18n import _

            print(f"{_('load_failed')}: {e}")
            return False

    def list_saves(self) -> List[Dict]:
        """列出所有存档"""
        saves = []
        for i in range(self.MAX_SLOTS):
            save_path = self._get_save_path(i)
            if save_path.exists():
                try:
                    with open(save_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    from .i18n import _

                    saves.append(
                        {
                            "slot": i,
                            "floor": data.get("floor", 1),
                            "timestamp": data.get("timestamp", _("unknown")),
                            "version": data.get("version", "1.0"),
                            "game_stats": data.get("game_stats", {}),
                            "player_data": data.get("player_data", {}),
                        }
                    )
                except:
                    saves.append({"slot": i, "error": True})
            else:
                saves.append({"slot": i, "empty": True})
        return saves

    def delete(self, slot: int) -> bool:
        """删除存档"""
        save_path = self._get_save_path(slot)
        try:
            if save_path.exists():
                save_path.unlink()
            return True
        except Exception as e:
            from .i18n import _

            print(f"{_('delete_save_failed')}: {e}")
            return False

    def exists(self, slot: int) -> bool:
        """检查存档是否存在"""
        return self._get_save_path(slot).exists()

    def _serialize_player(self, player) -> Dict:
        return {
            "x": player.x,
            "y": player.y,
            "hp": player.hp,
            "max_hp": player.max_hp,
            "atk": player.atk,
            "defense": player.defense,
            "level": player.level,
            "exp": player.exp,
            "exp_next": player.exp_next,
            "gold": player.gold,
            "crit": player.crit,
            "lifesteal": player.lifesteal,
            "regen": player.regen,
            "char_set": player.char_set,
            "dodge": getattr(player, "dodge", 0),
            "poison_atk": getattr(player, "poison_atk", 0),
            "double_hit": getattr(player, "double_hit", 0),
            "thorns": getattr(player, "thorns", 0),
            "soul_drain": getattr(player, "soul_drain", False),
            "crit_mult": getattr(player, "crit_mult", 2.0),
            "bomb_charges": getattr(player, "bomb_charges", 0),
            "invincible_charges": getattr(player, "invincible_charges", 0),
            "gold_bonus_floors": getattr(player, "gold_bonus_floors", 0),
        }

    def _deserialize_player(self, player, data: Dict) -> None:
        player.x = data.get("x", 1)
        player.y = data.get("y", 1)
        player.hp = data.get("hp", 100)
        player.max_hp = data.get("max_hp", 100)
        player.atk = data.get("atk", 10)
        player.defense = data.get("defense", 0)
        player.level = data.get("level", 1)
        player.exp = data.get("exp", 0)
        player.exp_next = data.get("exp_next", 50)
        player.gold = data.get("gold", 0)
        player.crit = data.get("crit", 0)
        player.lifesteal = data.get("lifesteal", 0)
        player.regen = data.get("regen", 0)
        player.char_set = data.get("char_set", "default")
        player.dodge = data.get("dodge", 0)
        player.poison_atk = data.get("poison_atk", 0)
        player.double_hit = data.get("double_hit", 0)
        player.thorns = data.get("thorns", 0)
        player.soul_drain = data.get("soul_drain", False)
        player.crit_mult = data.get("crit_mult", 2.0)
        player.bomb_charges = data.get("bomb_charges", 0)
        player.invincible_charges = data.get("invincible_charges", 0)
        player.gold_bonus_floors = data.get("gold_bonus_floors", 0)
