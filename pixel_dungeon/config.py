#!/usr/bin/env python3
"""全局配置模块"""

import json
from pathlib import Path

SETTINGS_PATH = Path.home() / ".pixel_dungeon" / "settings.json"


class CONFIG:
    """游戏全局配置"""

    # 性能设置
    fps: int = 30  # 帧率
    map_width: int = 80  # 地图宽度
    map_height: int = 40  # 地图高度
    view_distance: int = 14  # 视野距离
    particle_limit: int = 30  # 粒子数量上限

    tile_width: int = 6
    tile_height: int = 3

    # 功能开关
    lighting: bool = True  # 光照效果开关
    particles: bool = True  # 粒子效果开关
    animations: bool = True  # 动画开关

    # 游戏设置
    char_set: str = "default"  # 当前角色
    difficulty: str = "normal"
    language: str = "zh_CN"

    # 游戏平衡性
    enemy_scale_per_floor: float = 0.15  # 每层敌人强度增长
    exp_to_level_multiplier: float = 1.5  # 升级所需经验倍数

    @classmethod
    def set_fps(cls, value: int) -> bool:
        """设置帧率，返回是否成功"""
        if 10 <= value <= 60:
            cls.fps = value
            return True
        return False

    @classmethod
    def toggle_lighting(cls) -> bool:
        """切换光照效果"""
        cls.lighting = not cls.lighting
        return cls.lighting

    @classmethod
    def toggle_particles(cls) -> bool:
        """切换粒子效果"""
        cls.particles = not cls.particles
        return cls.particles

    @classmethod
    def set_char(cls, char_name: str) -> bool:
        """设置角色，返回是否成功"""
        from .assets import CHARACTERS

        if char_name in CHARACTERS:
            cls.char_set = char_name
            return True
        return False

    @classmethod
    def get_config_dict(cls) -> dict:
        return {
            "fps": cls.fps,
            "map_width": cls.map_width,
            "map_height": cls.map_height,
            "view_distance": cls.view_distance,
            "particle_limit": cls.particle_limit,
            "lighting": cls.lighting,
            "particles": cls.particles,
            "animations": cls.animations,
            "char_set": cls.char_set,
            "difficulty": cls.difficulty,
            "language": cls.language,
        }

    @classmethod
    def load_settings(cls) -> None:
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cls.fps = data.get("fps", cls.fps)
                cls.lighting = data.get("lighting", cls.lighting)
                cls.particles = data.get("particles", cls.particles)
                cls.animations = data.get("animations", cls.animations)
                diff = data.get("difficulty", cls.difficulty)
                if diff in ("easy", "normal", "hard"):
                    cls.difficulty = diff
                lang = data.get("language", cls.language)
                if lang in ("zh_CN", "en_US"):
                    cls.language = lang
            except Exception:
                pass

    @classmethod
    def save_settings(cls) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fps": cls.fps,
                    "lighting": cls.lighting,
                    "particles": cls.particles,
                    "animations": cls.animations,
                    "difficulty": cls.difficulty,
                    "language": cls.language,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
