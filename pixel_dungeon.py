#!/usr/bin/env python3
import random
import time
import sys
import os
import math
import select
import tty
import termios
import argparse
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
from enum import Enum, auto

from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.console import Console, Group
from rich.text import Text
from rich.align import Align
from rich import box

console = Console()


class CONFIG:
    fps = 30
    map_width = 30
    map_height = 12
    view_distance = 8
    particle_limit = 30
    lighting = True
    particles = True
    animations = True
    char_set = "default"


GAME_ASSETS = {
    "player_default": {"char": "♛", "name": "勇者", "style": "bold bright_green"},
    "player_mage": {"char": "⚚", "name": "法师", "style": "bold bright_cyan"},
    "player_rogue": {"char": "⚔", "name": "刺客", "style": "bold bright_red"},
    "player_paladin": {"char": "⚕", "name": "圣骑", "style": "bold bright_yellow"},
    "enemy_slime": {"char": "○", "name": "史莱姆", "style": "green"},
    "enemy_goblin": {"char": "ʘ", "name": "哥布林", "style": "yellow"},
    "enemy_skeleton": {"char": "☠", "name": "骷髅", "style": "white"},
    "enemy_orc": {"char": "Ω", "name": "兽人", "style": "red"},
    "enemy_shadow": {"char": "✦", "name": "暗影", "style": "magenta"},
    "wall": {"char": "█", "name": "墙壁", "style": "bright_black"},
    "floor": {"char": "·", "name": "地面", "style": "dim white"},
    "potion": {"char": "♥", "name": "生命药水", "style": "bright_green"},
    "gold": {"char": "◆", "name": "金币", "style": "bright_yellow"},
    "exit": {"char": "⌂", "name": "出口", "style": "bright_cyan"},
}

CHARACTERS = {
    "default": "player_default",
    "mage": "player_mage",
    "rogue": "player_rogue",
    "paladin": "player_paladin",
}


class TileType(Enum):
    EMPTY = auto()
    WALL = auto()
    EXIT = auto()
    POTION = auto()
    GOLD = auto()


@dataclass
class Particle:
    x: float
    y: float
    char: str
    style: str
    life: int
    dx: float = 0
    dy: float = 0
    grav: float = 0.02

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += self.grav
        self.life -= 1
        return self.life > 0


@dataclass
class FloatingText:
    x: int
    y: int
    text: str
    style: str
    life: int
    max_life: int = 0  # 用于计算透明度
    dy: float = -0.15
    
    def __post_init__(self):
        if self.max_life == 0:
            self.max_life = self.life

    def update(self):
        self.y += self.dy
        self.life -= 1
        return self.life > 0
    
    def get_alpha_style(self):
        """根据生命值返回带透明度的样式"""
        alpha = self.life / self.max_life if self.max_life > 0 else 1.0
        if alpha > 0.7:
            return f"bold {self.style}"
        elif alpha > 0.3:
            return self.style
        else:
            return f"dim {self.style}"


@dataclass
class Enemy:
    enemy_type: str
    name: str
    x: int
    y: int
    hp: int
    max_hp: int
    atk: int
    exp: int
    gold: int
    flash: int = 0
    frame: int = 0

    def animate(self):
        self.frame = (self.frame + 1) % 20
        if self.flash > 0:
            self.flash -= 1

    def get_render(self):
        asset = GAME_ASSETS.get(self.enemy_type, GAME_ASSETS["enemy_slime"])
        char = asset["char"]
        if self.flash > 0:
            return char, "bold white on red"
        if self.frame < 10:
            return char, f"bold {asset['style']}"
        return char, asset["style"]


@dataclass
class Player:
    x: int = 1
    y: int = 1
    hp: int = 100
    max_hp: int = 100
    atk: int = 10
    level: int = 1
    exp: int = 0
    exp_next: int = 50
    gold: int = 0
    kills: int = 0
    floor: int = 1
    regen: int = 0
    lifesteal: int = 0
    crit: int = 0
    defense: int = 0
    flash: int = 0
    frame: int = 0
    play_time: float = 0  # 游戏时长（秒）
    enemy_kills: Dict[str, int] = None  # 各类型敌人击杀统计

    def __post_init__(self):
        if self.enemy_kills is None:
            self.enemy_kills = {}

    @classmethod
    def create(cls, char_type: str = "default"):
        """根据角色类型创建玩家"""
        configs = {
            "default": {"hp": 100, "atk": 10, "defense": 0, "crit": 0, "lifesteal": 0, "regen": 0},
            "mage": {"hp": 80, "atk": 15, "defense": 0, "crit": 10, "lifesteal": 0, "regen": 1},
            "rogue": {"hp": 85, "atk": 12, "defense": 0, "crit": 20, "lifesteal": 5, "regen": 0},
            "paladin": {"hp": 130, "atk": 8, "defense": 2, "crit": 0, "lifesteal": 0, "regen": 1},
        }
        c = configs.get(char_type, configs["default"])
        return cls(
            hp=c["hp"], max_hp=c["hp"], atk=c["atk"],
            defense=c["defense"], crit=c["crit"], lifesteal=c["lifesteal"], regen=c["regen"]
        )

    def animate(self):
        self.frame = (self.frame + 1) % 12
        if self.flash > 0:
            self.flash -= 1

    def get_render(self):
        char_key = CHARACTERS.get(CONFIG.char_set, "player_default")
        asset = GAME_ASSETS[char_key]
        char = asset["char"]
        if self.flash > 0:
            return char, "bold white on red"
        if self.frame < 6:
            return char, asset["style"]
        return char, asset["style"].replace("bright_", "")


@dataclass
@dataclass
class ShopItem:
    """商店物品"""
    name: str
    desc: str
    price: int
    icon: str
    effect: callable
    one_time: bool = False  # 是否一次性物品（如血瓶可重复购买）


class Shop:
    """商店系统"""
    ITEMS = [
        ShopItem("生命药水", "恢复 30 HP", 20, "♥", 
                 lambda p: setattr(p, "hp", min(p.max_hp, p.hp + 30)), False),
        ShopItem("力量卷轴", "攻击力 +2", 50, "⚔",
                 lambda p: setattr(p, "atk", p.atk + 2), False),
        ShopItem("体质卷轴", "最大生命 +20", 50, "♥",
                 lambda p: setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20), False),
        ShopItem("铁皮药剂", "防御 +1", 40, "🛡",
                 lambda p: setattr(p, "defense", p.defense + 1), False),
        ShopItem("狂暴卷轴", "暴击率 +10%", 60, "⚡",
                 lambda p: setattr(p, "crit", p.crit + 10), False),
    ]


@dataclass
class Upgrade:
    name: str
    desc: str
    effect: callable
    rarity: str
    icon: str

    def get_style(self):
        return {
            "common": "white",
            "rare": "bright_cyan",
            "epic": "bright_magenta",
            "legendary": "bright_yellow",
        }.get(self.rarity, "white")

    def get_rarity_name(self):
        return {
            "common": "普通",
            "rare": "稀有",
            "epic": "史诗",
            "legendary": "传说",
        }.get(self.rarity, "普通")


class CommandHandler:
    COMMANDS = {
        "help": "显示帮助信息",
        "h": "显示帮助信息(简写)",
        "quit": "退出游戏",
        "q": "退出游戏(简写)",
        "fps": "设置帧率 用法: /fps [15-60]",
        "light": "开关光照 用法: /light [on|off]",
        "particle": "开关粒子 用法: /particle [on|off]",
        "char": "切换角色 用法: /char [default|mage|rogue|paladin]",
        "config": "显示当前配置",
        "shop": "打开商店",
        "heal": "恢复生命(调试)",
        "level": "设置等级(调试)",
        "gold": "添加金币(调试)",
        "god": "无敌模式(调试)",
        "killall": "消灭所有敌人(调试)",
        "next": "进入下一层(调试)",
    }

    def __init__(self, game):
        self.game = game

    def get_suggestions(self, partial: str) -> List[str]:
        if not partial:
            return list(self.COMMANDS.keys())[:8]
        return [cmd for cmd in self.COMMANDS.keys() if cmd.startswith(partial.lower())]

    def execute(self, cmd_line: str) -> str:
        parts = cmd_line.strip().split()
        if not parts:
            return None
        cmd = parts[0].lower()
        args = parts[1:]

        handlers = {
            "help": self.cmd_help,
            "h": self.cmd_help,
            "quit": self.cmd_quit,
            "q": self.cmd_quit,
            "fps": self.cmd_fps,
            "light": self.cmd_light,
            "particle": self.cmd_particle,
            "char": self.cmd_char,
            "config": self.cmd_config,
            "shop": self.cmd_shop,
            "heal": self.cmd_heal,
            "level": self.cmd_level,
            "gold": self.cmd_gold,
            "god": self.cmd_god,
            "killall": self.cmd_killall,
            "next": self.cmd_next,
        }

        if cmd in handlers:
            return handlers[cmd](args)
        
        # 容错设计：提供相似命令建议
        suggestions = [c for c in self.COMMANDS.keys() if c.startswith(cmd[0]) and len(c) > 1]
        if suggestions:
            return f"[yellow]未知命令: /{cmd}[/]\n[dim]你是否想输入: /{', /'.join(suggestions[:3])}?\n输入 /help 查看所有命令[/]"
        else:
            return f"[yellow]未知命令: /{cmd}[/]\n[dim]输入 /help 查看所有命令[/]"

    def cmd_help(self, args):
        help_text = "[bold yellow]📖 可用命令[/]\n\n"
        for cmd, desc in self.COMMANDS.items():
            if len(cmd) > 1:
                help_text += f"  [bright_cyan]/{cmd}[/] - {desc}\n"
        help_text += "\n[dim]提示: 输入 / 后按 TAB 自动补全[/]"
        return help_text

    def cmd_quit(self, args):
        self.game.running = False
        return "👋 退出游戏"

    def cmd_fps(self, args):
        if args:
            try:
                fps = int(args[0])
                if 10 <= fps <= 60:
                    CONFIG.fps = fps
                    return f"✅ 帧率设置为 {fps} FPS"
                return "⚠️ 帧率应在 10-60 之间"
            except:
                return "❌ 用法: /fps [10-60]"
        return f"📊 当前帧率: {CONFIG.fps} FPS"

    def cmd_light(self, args):
        if args:
            CONFIG.lighting = args[0].lower() in ("on", "true", "1", "yes")
        state = "✅ 开启" if CONFIG.lighting else "❌ 关闭"
        return f"💡 光照效果: {state}"

    def cmd_particle(self, args):
        if args:
            CONFIG.particles = args[0].lower() in ("on", "true", "1", "yes")
        state = "✅ 开启" if CONFIG.particles else "❌ 关闭"
        return f"✨ 粒子效果: {state}"

    def cmd_char(self, args):
        if args:
            char_name = args[0].lower()
            if char_name in CHARACTERS:
                CONFIG.char_set = char_name
                asset = GAME_ASSETS[CHARACTERS[char_name]]
                return f"🎭 切换为 [{asset['style']}]{asset['name']} {asset['char']}[/]"
            return f"❌ 可用角色: {', '.join(CHARACTERS.keys())}"
        current = GAME_ASSETS[CHARACTERS[CONFIG.char_set]]
        others = []
        for k, v in CHARACTERS.items():
            if k != CONFIG.char_set:
                asset = GAME_ASSETS[v]
                others.append(f"{k}: {asset['name']}{asset['char']}")
        return f"🎭 当前: {current['name']}{current['char']}\n可用: {', '.join(others)}"

    def cmd_config(self, args):
        current = GAME_ASSETS[CHARACTERS[CONFIG.char_set]]
        return f"""[bold cyan]⚙️ 当前配置[/]

角色: {current["name"]} {current["char"]}
FPS: {CONFIG.fps}
光照: {"✅ 开启" if CONFIG.lighting else "❌ 关闭"}
粒子: {"✅ 开启" if CONFIG.particles else "❌ 关闭"}
地图: {CONFIG.map_width}x{CONFIG.map_height}
"""

    def cmd_shop(self, args):
        self.game.open_shop()
        return None  # 消息在 open_shop 中已添加

    def cmd_heal(self, args):
        if args:
            amount = int(args[0])
            self.game.player.hp = min(
                self.game.player.max_hp, self.game.player.hp + amount
            )
            return f"💚 恢复 {amount} 生命值"
        self.game.player.hp = self.game.player.max_hp
        return "💚 生命值回满"

    def cmd_level(self, args):
        if args:
            level = int(args[0])
            self.game.player.level = max(1, level)
            return f"📈 等级设置为 {level}"
        return f"📊 当前等级: {self.game.player.level}"

    def cmd_gold(self, args):
        if args:
            amount = int(args[0])
            self.game.player.gold += amount
            return f"💰 获得 {amount} 金币"
        return f"💰 当前金币: {self.game.player.gold}"

    def cmd_god(self, args):
        self.game.player.max_hp = 9999
        self.game.player.hp = 9999
        self.game.player.atk = 999
        self.game.player.defense = 99
        self.game.player.crit = 100
        return "🌟 无敌模式开启！"

    def cmd_killall(self, args):
        count = len(self.game.enemies)
        self.game.enemies.clear()
        return f"💀 消灭了 {count} 个敌人"

    def cmd_next(self, args):
        self.game.next_floor()
        return "🚪 进入下一层"


class Game:
    def __init__(self):
        self.player = Player.create(CONFIG.char_set)
        self.map = []
        self.light = []
        self.enemies = []
        self.messages = []
        self.particles = []
        self.floats = []
        self.state = "playing"
        self.upgrades = []
        self.sel_upgrade = 0
        self.turn = 0
        self.frame = 0
        self.shake = 0
        self.running = True
        self.cmd_mode = False
        self.cmd_buffer = ""
        self.cmd_suggestions = []
        self.show_help = False
        self.paused = False  # 暂停状态
        self.shop_open = False  # 商店是否打开
        self.shop_items = []  # 当前商店商品
        self.shop_sel = 0  # 商店选中项
        self.start_time = time.time()  # 游戏开始时间
        self.commands = CommandHandler(self)
        self.init_map()

    def init_map(self):
        w, h = CONFIG.map_width, CONFIG.map_height
        self.map = [[TileType.EMPTY for _ in range(w)] for _ in range(h)]
        self.light = [[1.0 for _ in range(w)] for _ in range(h)]

        for x in range(w):
            self.map[0][x] = TileType.WALL
            self.map[h - 1][x] = TileType.WALL
        for y in range(h):
            self.map[y][0] = TileType.WALL
            self.map[y][w - 1] = TileType.WALL

        for _ in range(10):
            x, y = random.randint(2, w - 3), random.randint(2, h - 3)
            self.map[y][x] = TileType.WALL

        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if 0 <= 1 + dy < h and 0 <= 1 + dx < w:
                    self.map[1 + dy][1 + dx] = TileType.EMPTY

        self.map[random.randint(h // 2, h - 2)][random.randint(w // 2, w - 2)] = (
            TileType.EXIT
        )
        self.spawn_enemies()
        self.spawn_items()

    def spawn_enemies(self):
        w, h = CONFIG.map_width, CONFIG.map_height
        count = 2 + self.player.floor
        self.enemies = []
        enemy_types = [
            ("enemy_slime", "史莱姆", 15, 5, 10, 5),
            ("enemy_goblin", "哥布林", 25, 8, 15, 8),
            ("enemy_skeleton", "骷髅", 20, 10, 20, 10),
            ("enemy_orc", "兽人", 40, 12, 30, 15),
            ("enemy_shadow", "暗影", 30, 15, 40, 20),
        ]
        for _ in range(count):
            for _ in range(50):
                x, y = random.randint(1, w - 2), random.randint(1, h - 2)
                if (
                    self.map[y][x] == TileType.EMPTY
                    and abs(x - self.player.x) > 4
                    and abs(y - self.player.y) > 4
                ):
                    available = enemy_types[
                        : min(2 + self.player.floor // 2, len(enemy_types))
                    ]
                    e_type, name, hp, atk, exp, gold = random.choice(available)
                    scale = 1 + (self.player.floor - 1) * 0.15
                    self.enemies.append(
                        Enemy(
                            e_type,
                            name,
                            x,
                            y,
                            int(hp * scale),
                            int(hp * scale),
                            int(atk * scale),
                            int(exp * scale),
                            int(gold * scale),
                        )
                    )
                    break

    def spawn_items(self):
        w, h = CONFIG.map_width, CONFIG.map_height
        for _ in range(3):
            for _ in range(30):
                x, y = random.randint(1, w - 2), random.randint(1, h - 2)
                if self.map[y][x] == TileType.EMPTY:
                    self.map[y][x] = TileType.POTION
                    break
        for _ in range(5):
            for _ in range(30):
                x, y = random.randint(1, w - 2), random.randint(1, h - 2)
                if self.map[y][x] == TileType.EMPTY:
                    self.map[y][x] = TileType.GOLD
                    break

    def update_light(self):
        """更新光照 - 平滑渐变效果"""
        if not CONFIG.lighting:
            for y in range(CONFIG.map_height):
                for x in range(CONFIG.map_width):
                    self.light[y][x] = 1.0
            return
        
        px, py = self.player.x, self.player.y
        vd = CONFIG.view_distance
        
        for y in range(CONFIG.map_height):
            for x in range(CONFIG.map_width):
                # 欧几里得距离
                dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                
                if dist <= vd:
                    # 平滑的二次衰减
                    # 中心最亮(1.0)，边缘渐暗
                    ratio = dist / vd
                    light = 1.0 - (ratio ** 1.5) * 0.7
                    
                    # 添加微弱的闪烁效果（只在较暗区域）
                    if light < 0.6 and random.random() < 0.05:
                        light += 0.05
                    
                    self.light[y][x] = max(0.15, light)
                else:
                    # 视野外保持微弱可见
                    self.light[y][x] = 0.08

    def spawn_particles(self, x, y, count, chars, styles):
        if not CONFIG.particles:
            return
        count = min(count, 5)
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            vel = random.uniform(0.05, 0.2)
            self.particles.append(
                Particle(
                    x + random.uniform(-0.2, 0.2),
                    y + random.uniform(-0.2, 0.2),
                    random.choice(chars),
                    random.choice(styles),
                    random.randint(5, 10),
                    math.cos(angle) * vel * 0.2,
                    math.sin(angle) * vel * 0.15 - 0.05,
                )
            )

    def spawn_float(self, x, y, text, style):
        # 缩短浮动文字显示时间，避免遮挡
        # 限制文字长度，避免占用过多空间
        short_text = text[:4] if len(text) > 4 else text
        self.floats.append(FloatingText(x, y, short_text, style, 10))

    def get_upgrades(self):
        pool = [
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
                "铁皮",
                "防御 +2",
                lambda p: setattr(p, "defense", p.defense + 2),
                "common",
                "🛡",
            ),
            Upgrade(
                "狂战士",
                "攻击+5 防御-1",
                lambda p: setattr(p, "atk", p.atk + 5) or setattr(p, "defense", max(0, p.defense - 1)),
                "rare",
                "🪓",
            ),
            Upgrade(
                "泰坦",
                "生命+50 攻击-2",
                lambda p: setattr(p, "max_hp", p.max_hp + 50) or setattr(p, "hp", p.hp + 50) or setattr(p, "atk", max(1, p.atk - 2)),
                "rare",
                "🗿",
            ),
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
            Upgrade(
                "不朽",
                "生命+100 恢复+5",
                lambda p: setattr(p, "max_hp", p.max_hp + 100) or setattr(p, "hp", p.hp + 100) or setattr(p, "regen", p.regen + 5),
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
        weights = {"common": 50, "rare": 30, "epic": 15, "legendary": 5}
        weighted = []
        for u in pool:
            weighted.extend([u] * weights[u.rarity])
        self.upgrades = random.sample(weighted, 3)
        self.sel_upgrade = 0

    def apply_upgrade(self, idx):
        u = self.upgrades[idx]
        u.effect(self.player)
        self.add_msg(f"获得: {u.name}！", "cyan", "success")
        self.spawn_particles(
            self.player.x, self.player.y, 8, ["✦", "★"], ["yellow", "cyan"]
        )
        self.state = "playing"

    def check_level(self):
        if self.player.exp >= self.player.exp_next:
            self.player.exp -= self.player.exp_next
            self.player.level += 1
            self.player.exp_next = int(self.player.exp_next * 1.5)
            self.player.max_hp += 10
            self.player.hp += 10
            self.player.atk += 2
            self.shake = 2
            self.spawn_particles(
                self.player.x, self.player.y, 12, ["★", "✦"], ["yellow", "cyan"]
            )
            self.add_msg(f"升级到 {self.player.level} 级！", "yellow", "success")
            self.get_upgrades()
            self.state = "upgrading"

    def add_msg(self, msg, style="white", msg_type="info"):
        """添加消息 - 带分类和优先级
        
        msg_type: info, success, warning, danger, system
        """
        # 根据消息类型设置持续时间
        type_config = {
            "info": 150,
            "success": 200,
            "warning": 180,
            "danger": 250,
            "system": 120,
        }
        
        duration = type_config.get(msg_type, 150)
        
        self.messages.append((msg, style, duration, msg_type))
        if len(self.messages) > 8:
            self.messages.pop(0)

    def update_msgs(self):
        """更新消息 - 递减生命周期"""
        new_messages = []
        for msg_data in self.messages:
            if len(msg_data) == 4:
                msg, style, life, msg_type = msg_data
            else:
                msg, style, life = msg_data
                msg_type = "info"
            
            if life > 0:
                new_messages.append((msg, style, life - 1, msg_type))
        self.messages = new_messages

    def move(self, dx, dy):
        nx, ny = self.player.x + dx, self.player.y + dy
        if nx < 0 or nx >= CONFIG.map_width or ny < 0 or ny >= CONFIG.map_height:
            return
        tile = self.map[ny][nx]
        if tile == TileType.WALL:
            self.shake = 1
            return
        for e in self.enemies:
            if e.x == nx and e.y == ny:
                self.attack(e)
                return
        self.player.x, self.player.y = nx, ny
        if tile == TileType.EXIT:
            self.next_floor()
        elif tile == TileType.POTION:
            heal = 30
            self.player.hp = min(self.player.max_hp, self.player.hp + heal)
            self.map[ny][nx] = TileType.EMPTY
            asset = GAME_ASSETS["potion"]
            self.spawn_particles(nx, ny, 5, [asset["char"]], ["green"])
            self.spawn_float(nx, ny, f"+{heal}", "green")
            self.add_msg(f"恢复 {heal} 生命", "green", "success")
        elif tile == TileType.GOLD:
            g = random.randint(5, 15)
            self.player.gold += g
            self.map[ny][nx] = TileType.EMPTY
            asset = GAME_ASSETS["gold"]
            self.spawn_particles(nx, ny, 4, [asset["char"]], ["yellow"])
            self.spawn_float(nx, ny, f"+{g}", "yellow")
            self.add_msg(f"获得 {g} 金币", "yellow", "success")
        self.end_turn()

    def attack(self, enemy):
        dmg = self.player.atk
        is_crit = random.randint(1, 100) <= self.player.crit
        if is_crit:
            dmg *= 2
        dmg = max(1, dmg)
        enemy.hp -= dmg
        enemy.flash = 2
        crit_txt = " 暴击!" if is_crit else ""
        self.add_msg(f"对{enemy.name}造成{dmg}伤害{crit_txt}", "white", "info")
        self.shake = 1 if is_crit else 0
        self.spawn_particles(enemy.x, enemy.y, 5, ["✦", "*"], ["red", "yellow"])
        self.spawn_float(
            enemy.x, enemy.y - 1, str(dmg), "red" if is_crit else "dark_red"
        )
        if self.player.lifesteal > 0:
            heal = int(dmg * self.player.lifesteal / 100)
            if heal > 0:
                self.player.hp = min(self.player.max_hp, self.player.hp + heal)
        if enemy.hp <= 0:
            self.add_msg(f"击败 {enemy.name}！+{enemy.exp}经验", "green", "success")
            asset = GAME_ASSETS.get(enemy.enemy_type)
            if asset:
                self.spawn_particles(
                    enemy.x, enemy.y, 8, [asset["char"]], ["red", "white"]
                )
            self.spawn_float(enemy.x, enemy.y, "KO!", "white")
            self.player.exp += enemy.exp
            self.player.gold += enemy.gold
            self.player.kills += 1
            # 统计各类型敌人击杀数
            enemy_key = enemy.enemy_type.replace("enemy_", "")
            self.player.enemy_kills[enemy_key] = self.player.enemy_kills.get(enemy_key, 0) + 1
            self.enemies.remove(enemy)
            self.check_level()
        else:
            self.enemy_attack(enemy)
        self.end_turn()

    def enemy_attack(self, enemy):
        # 新防御公式: 伤害减免率 = defense / (defense + 10)
        # 这样防御有边际递减，但永远不会完全无敌
        defense_factor = self.player.defense / (self.player.defense + 10) if self.player.defense > 0 else 0
        dmg = max(1, int(enemy.atk * (1 - defense_factor)))
        self.player.hp -= dmg
        self.player.flash = 2
        self.add_msg(f"受到{enemy.name}{dmg}点伤害", "red", "danger")
        self.spawn_particles(self.player.x, self.player.y, 4, ["!", "✦"], ["red"])
        self.spawn_float(self.player.x, self.player.y - 1, str(dmg), "red")
        if self.player.hp <= 0:
            self.state = "game_over"

    def next_floor(self):
        self.player.floor += 1
        self.add_msg(f"进入第 {self.player.floor} 层！", "cyan", "system")
        asset = GAME_ASSETS["exit"]
        self.spawn_particles(
            self.player.x, self.player.y, 8, [asset["char"]], ["cyan", "blue"]
        )
        self.player.x, self.player.y = 1, 1
        self.init_map()

    def wait(self):
        self.add_msg("等待...", "dim", "info")
        self.end_turn()

    def open_shop(self):
        """打开商店"""
        self.shop_open = True
        self.shop_sel = 0
        # 随机生成3-5个商品
        self.shop_items = random.sample(Shop.ITEMS, min(len(Shop.ITEMS), random.randint(3, 5)))
        self.add_msg("欢迎光临商店！", "yellow", "system")

    def close_shop(self):
        """关闭商店"""
        self.shop_open = False
        self.shop_items = []

    def buy_item(self, idx):
        """购买物品"""
        if idx < 0 or idx >= len(self.shop_items):
            return False
        item = self.shop_items[idx]
        if self.player.gold >= item.price:
            self.player.gold -= item.price
            item.effect(self.player)
            self.add_msg(f"购买 {item.name} (-{item.price}G)", "green", "success")
            self.spawn_particles(self.player.x, self.player.y, 6, [item.icon], ["yellow"])
            return True
        else:
            self.add_msg(f"金币不足！需要 {item.price}G", "red", "warning")
            return False

    def toggle_pause(self):
        """切换暂停状态"""
        self.paused = not self.paused
        if self.paused:
            self.add_msg("游戏已暂停 (P继续)", "yellow", "system")
        else:
            self.add_msg("游戏继续", "green", "success")

    def end_turn(self):
        self.turn += 1
        # 更新游戏时间
        self.player.play_time = time.time() - self.start_time
        if self.player.regen > 0 and self.player.hp < self.player.max_hp:
            old = self.player.hp
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.regen)
            if self.player.hp > old and self.turn % 2 == 0:
                self.spawn_particles(self.player.x, self.player.y, 3, ["+"], ["green"])
        for e in self.enemies:
            dx = self.player.x - e.x
            dy = self.player.y - e.y
            dist = abs(dx) + abs(dy)
            if dist == 1:
                self.enemy_attack(e)
            elif dist <= 5 and random.random() < 0.2:
                mx = 1 if dx > 0 else -1 if dx < 0 else 0
                my = 1 if dy > 0 else -1 if dy < 0 else 0
                if abs(dx) < abs(dy):
                    mx, my = 0, my
                nx, ny = e.x + mx, e.y + my
                if (
                    0 <= nx < CONFIG.map_width
                    and 0 <= ny < CONFIG.map_height
                    and self.map[ny][nx] != TileType.WALL
                    and not any(
                        en.x == nx and en.y == ny for en in self.enemies if en != e
                    )
                    and not (nx == self.player.x and ny == self.player.y)
                ):
                    e.x, e.y = nx, ny

    def update_cmd_suggestions(self):
        if self.cmd_mode and self.cmd_buffer:
            self.cmd_suggestions = self.commands.get_suggestions(self.cmd_buffer)
        else:
            self.cmd_suggestions = []

    def update_animations(self):
        self.player.animate()
        for e in self.enemies:
            e.animate()
        if self.shake > 0:
            self.shake -= 1
        self.particles = [p for p in self.particles if p.update()]
        if len(self.particles) > CONFIG.particle_limit:
            self.particles = self.particles[-CONFIG.particle_limit :]
        self.floats = [f for f in self.floats if f.update()]
        self.update_msgs()
        self.update_light()
        self.update_cmd_suggestions()


class InputHandler:
    def __init__(self):
        self.old = None

    def start(self):
        try:
            self.old = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())
        except:
            pass

    def stop(self):
        if self.old:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old)

    def get_key(self):
        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == "\x1b":
                seq = (
                    sys.stdin.read(2)
                    if select.select([sys.stdin], [], [], 0)[0]
                    else ""
                )
                if seq == "[A":
                    return "UP"
                if seq == "[B":
                    return "DOWN"
                if seq == "[C":
                    return "RIGHT"
                if seq == "[D":
                    return "LEFT"
            if key == "\t":
                return "TAB"
            return key
        return None


def get_bar(current, max_val, width=10, color=None):
    ratio = current / max_val if max_val > 0 else 0
    filled = int(ratio * width)
    empty = width - filled
    if color is None:
        if ratio > 0.6:
            color = "green"
        elif ratio > 0.3:
            color = "yellow"
        else:
            color = "red"
    bar = f"[{'█' * filled}{'░' * empty}]"
    return f"[{color}]{bar}[/][white]{current}[/]"


def get_light_style(style: str, light: float) -> str:
    """根据光照强度调整样式"""
    if light < 0.3:
        # 黑暗区域 - 降低亮度
        return f"dim {style.replace('bright_', '').replace('bold ', '')}"
    elif light < 0.6:
        # 阴影区域 - 移除 bright 前缀
        return style.replace('bright_', '').replace('bold ', '')
    elif light < 0.9:
        # 微暗区域
        return style.replace('bright_', '')
    return style


def render_map(game):
    """渲染游戏地图 - 优化版本"""
    # 收集浮动文字和粒子（单字符显示，避免错位）
    float_chars = {}
    for f in game.floats:
        fx, fy = int(f.x), int(f.y)
        if 0 <= fy < CONFIG.map_height and 0 <= fx < CONFIG.map_width:
            # 只取第一个字符，避免多字符导致的错位
            char = f.text[0] if f.text else ""
            float_chars[(fx, fy)] = (char, f.get_alpha_style())
    
    # 收集粒子
    part_chars = {}
    for p in game.particles:
        px, py = int(p.x), int(p.y)
        if 0 <= py < CONFIG.map_height and 0 <= px < CONFIG.map_width:
            part_chars[(px, py)] = (p.char, p.style)
    
    # 收集敌人位置
    enemy_pos = {(e.x, e.y): e for e in game.enemies}
    
    lines = []
    for y in range(CONFIG.map_height):
        row = Text()
        for x in range(CONFIG.map_width):
            light = game.light[y][x] if CONFIG.lighting else 1.0
            tile = game.map[y][x]
            
            # 决定显示什么字符
            char = "·"
            style = "dim white"
            
            # 优先级：玩家 > 敌人 > 浮动文字 > 粒子 > 地图元素
            if game.player.x == x and game.player.y == y:
                char, style = game.player.get_render()
            elif (x, y) in enemy_pos:
                char, style = enemy_pos[(x, y)].get_render()
            elif (x, y) in float_chars and light > 0.3:
                # 浮动文字只在有光照时显示
                char, style = float_chars[(x, y)]
            elif (x, y) in part_chars and light > 0.3:
                char, style = part_chars[(x, y)]
            else:
                # 地图元素
                if tile == TileType.WALL:
                    char = "█"
                    style = "bright_black"
                elif tile == TileType.EXIT:
                    char = GAME_ASSETS["exit"]["char"]
                    style = GAME_ASSETS["exit"]["style"]
                elif tile == TileType.POTION:
                    char = GAME_ASSETS["potion"]["char"]
                    style = GAME_ASSETS["potion"]["style"]
                elif tile == TileType.GOLD:
                    char = GAME_ASSETS["gold"]["char"]
                    style = GAME_ASSETS["gold"]["style"]
            
            # 应用光照效果
            if CONFIG.lighting:
                style = get_light_style(style, light)
            
            row.append(Text(char, style=style))
            row.append(" ")  # 每个格子后加空格
        lines.append(row)
    return Group(*lines)


def create_compact_stats(game):
    """创建紧凑状态栏（用于窄终端模式）"""
    p = game.player
    text = Text()
    
    # 紧凑显示关键信息
    text.append(f"Lv{p.level} ", style="yellow")
    text.append(f"HP:{p.hp}/{p.max_hp} ", style="green" if p.hp > p.max_hp * 0.3 else "red")
    text.append(f"ATK:{p.atk} ", style="red")
    text.append(f"G:{p.gold}", style="yellow")
    
    hp_ratio = p.hp / p.max_hp
    border_color = "green" if hp_ratio > 0.6 else "yellow" if hp_ratio > 0.3 else "red"
    
    return Panel(
        Align.center(text),
        border_style=border_color,
        box=box.ROUNDED,
        padding=(0, 0),
    )


def create_stats(game):
    """创建状态面板 - 优化版"""
    p = game.player
    char_key = CHARACTERS[CONFIG.char_set]
    asset = GAME_ASSETS[char_key]
    
    # 根据血量决定边框颜色（视觉反馈）
    hp_ratio = p.hp / p.max_hp
    if hp_ratio > 0.6:
        border_color = "green"
        hp_style = "green"
    elif hp_ratio > 0.3:
        border_color = "yellow"
        hp_style = "yellow"
    else:
        border_color = "red"
        hp_style = "red bold blink"  # 低血量时闪烁警告
    
    # 使用更紧凑的表格
    table = Table(show_header=False, box=None, padding=(0, 0), expand=True)
    table.add_column(style="white", width=3, justify="right")
    table.add_column()
    
    # 主要属性
    table.add_row("Lv", f"[yellow bold]{p.level}[/]")
    table.add_row("HP", f"[{hp_style}]{p.hp}/{p.max_hp}[/{hp_style}]")
    table.add_row("ATK", f"[red bold]{p.atk}[/]")
    table.add_row("EXP", f"[cyan]{p.exp}/{p.exp_next}[/]")
    table.add_row("G", f"[yellow bold]{p.gold}[/]")
    
    # 次要属性 - 单行显示
    sub_stats = Text()
    sub_stats.append(f"DEF:{p.defense}", style="dim")
    sub_stats.append("  ")
    sub_stats.append(f"REG:{p.regen}", style="dim")
    sub_stats.append("  ")
    sub_stats.append(f"LS:{p.lifesteal}%", style="dim")
    sub_stats.append("  ")
    sub_stats.append(f"CRT:{p.crit}%", style="dim")
    
    return Panel(
        Group(table, Text(), sub_stats),
        title=f"{asset['char']} {asset['name']}",
        title_align="center",
        border_style=border_color,
        box=box.ROUNDED,
        height=11,
    )


def create_legend_panel():
    """创建图例面板 - 优化版"""
    # 使用 Text 构建更灵活的布局
    text = Text()
    
    # 第一行：敌人图例
    enemies = [
        (GAME_ASSETS["enemy_slime"], "史莱姆"),
        (GAME_ASSETS["enemy_goblin"], "哥布林"),
        (GAME_ASSETS["enemy_skeleton"], "骷髅"),
    ]
    for asset, name in enemies:
        text.append(asset["char"], style=asset["style"])
        text.append(f"{name} ", style="dim")
    text.append("\n")
    
    # 第二行：更多敌人
    enemies2 = [
        (GAME_ASSETS["enemy_orc"], "兽人"),
        (GAME_ASSETS["enemy_shadow"], "暗影"),
    ]
    for asset, name in enemies2:
        text.append(asset["char"], style=asset["style"])
        text.append(f"{name} ", style="dim")
    text.append("\n\n")
    
    # 物品图例
    items = [
        (GAME_ASSETS["potion"], "血瓶"),
        (GAME_ASSETS["gold"], "金币"),
        (GAME_ASSETS["exit"], "出口"),
        (GAME_ASSETS["wall"], "墙"),
        (GAME_ASSETS["floor"], "地"),
    ]
    for i, (asset, name) in enumerate(items):
        if i > 0 and i % 3 == 0:
            text.append("\n")
        text.append(asset["char"], style=asset["style"])
        text.append(f"{name} ", style="dim")
    
    return Panel(
        text,
        title="图例",
        title_align="center",
        border_style="dim",
        box=box.ROUNDED,
        height=5,
    )


def create_log(game):
    """创建日志面板 - 优化版"""
    text = Text()
    
    # 图标映射
    type_icons = {
        "info": "",
        "success": "✓ ",
        "warning": "⚠ ",
        "danger": "✗ ",
        "system": "ℹ ",
    }
    
    # 显示最近的消息
    for msg_data in game.messages[-5:]:
        if len(msg_data) == 4:
            msg, style, life, msg_type = msg_data
        else:
            msg, style, life = msg_data
            msg_type = "info"
        
        # 根据剩余生命周期调整透明度
        max_life = {"danger": 250, "success": 200, "warning": 180, "system": 120}.get(msg_type, 150)
        alpha = life / max_life if max_life > 0 else 1.0
        
        icon = type_icons.get(msg_type, "")
        
        if alpha > 0.6:
            text.append(f"{icon}{msg}\n", style=f"bold {style}")
        elif alpha > 0.3:
            text.append(f"{icon}{msg}\n", style=style)
        else:
            text.append(f"{icon}{msg}\n", style=f"dim {style}")
    
    # 命令模式提示
    if game.cmd_mode:
        text.append("\n> ", style="yellow")
        text.append(game.cmd_buffer)
        if game.cmd_suggestions:
            text.append("\n")
            for i, sugg in enumerate(game.cmd_suggestions[:4]):
                if i > 0:
                    text.append(" ", style="dim")
                text.append(f"/{sugg}", style="dim bright_cyan")
    else:
        # 底部快捷提示
        text.append("\n")
        hints = [
            ("?", "帮助"),
            ("/", "命令"),
            ("B", "商店"),
            ("P", "暂停"),
        ]
        for key, desc in hints:
            text.append(f"{key}", style="dim yellow")
            text.append(f"{desc} ", style="dim")
    
    return Panel(
        text, 
        title="日志", 
        title_align="center", 
        border_style="cyan", 
        box=box.ROUNDED, 
        height=8
    )


def render_game(game):
    """渲染游戏界面 - 提取为函数方便复用"""
    term_width = console.width
    term_height = console.height
    
    # 地图区域宽度 = 地图格子数 * 2 (字符+空格) + 边框
    map_content_width = CONFIG.map_width * 2
    map_panel_width = map_content_width + 4  # 加上边框
    
    # 计算侧边栏可用空间
    side_width = term_width - map_panel_width - 2
    
    main_layout = Layout()
    
    # 如果终端太窄，只显示地图
    if side_width < 30:
        # 窄终端模式 - 状态栏在地图下方
        map_layout = Layout()
        map_layout.split_column(
            Layout(Panel(
                render_map(game),
                title=f"第 {game.player.floor} 层",
                title_align="center",
                border_style="cyan",
                box=box.ROUNDED,
                padding=(0, 0),
            ), ratio=term_height - 9),
            Layout(create_compact_stats(game), size=3),
            Layout(create_log(game), size=6),
        )
        main_layout = map_layout
    else:
        # 正常布局
        top = Layout()
        top.split_row(
            Layout(name="map", ratio=map_panel_width),
            Layout(name="side", ratio=side_width)
        )

        # 根据玩家状态改变边框颜色（反馈机制）
        hp_ratio = game.player.hp / game.player.max_hp
        if hp_ratio > 0.6:
            border_color = "cyan"  # 健康
        elif hp_ratio > 0.3:
            border_color = "yellow"  # 警告
        else:
            border_color = "red"  # 危险

        map_panel = Panel(
            render_map(game),
            title=f"第 {game.player.floor} 层",
            title_align="center",
            border_style=border_color,
            box=box.ROUNDED,
            padding=(0, 0),
        )
        top["map"].update(map_panel)

        side = Layout()
        if game.show_help:
            side.update(create_help_panel())
        else:
            side.split_column(
                Layout(create_stats(game), size=14),
                Layout(create_legend_panel()),
            )
        top["side"].update(side)

        bottom = Layout()
        bottom.update(create_log(game))

        main_layout.split_column(
            Layout(top, ratio=term_height - 7),
            Layout(bottom, size=7)
        )

    # 覆盖层处理（升级、游戏结束、商店、暂停）
    if game.state == "upgrading":
        up = create_upgrade(game)
        if up:
            # 创建覆盖层布局
            overlay_layout = Layout()
            overlay_layout.split_column(
                Layout(),
                Layout(Align.center(up, vertical="middle"), size=20),
                Layout(),
            )
            main_layout = overlay_layout

    elif game.state == "game_over":
        go = create_gameover(game)
        if go:
            overlay_layout = Layout()
            overlay_layout.split_column(
                Layout(),
                Layout(Align.center(go, vertical="middle"), size=16),
                Layout(),
            )
            main_layout = overlay_layout
    
    elif game.shop_open:
        shop = create_shop(game)
        if shop:
            overlay_layout = Layout()
            overlay_layout.split_column(
                Layout(),
                Layout(Align.center(shop, vertical="middle"), size=16),
                Layout(),
            )
            main_layout = overlay_layout
    
    elif game.paused:
        pause = create_pause_overlay()
        if pause:
            overlay_layout = Layout()
            overlay_layout.split_column(
                Layout(),
                Layout(Align.center(pause, vertical="middle"), size=7),
                Layout(),
            )
            main_layout = overlay_layout
    
    return main_layout


def create_shop(game):
    """创建商店界面"""
    if not game.shop_open:
        return None
    
    text = Text()
    text.append("💰 金币: ", style="bold yellow")
    text.append(f"{game.player.gold}\n\n", style="yellow")
    
    for i, item in enumerate(game.shop_items):
        prefix = "> " if i == game.shop_sel else "  "
        can_afford = game.player.gold >= item.price
        price_color = "green" if can_afford else "red"
        text.append(f"{prefix}[{i + 1}] ", style="white")
        text.append(f"{item.icon} {item.name}", style="bold")
        text.append(f" - {item.price}G\n", style=price_color)
        text.append(f"      {item.desc}\n", style="dim white")
    
    # 底部提示
    text.append("\n")
    text.append("W/S", style="dim")
    text.append("选择 ", style="dim")
    text.append("Enter", style="dim")
    text.append("购买 ", style="dim")
    text.append("1-3", style="dim")
    text.append("快捷购买 ", style="dim")
    text.append("ESC", style="dim")
    text.append("关闭", style="dim")
    
    return Panel(
        Align.center(text, vertical="middle"),
        title="商店",
        title_align="center",
        border_style="yellow",
        box=box.DOUBLE,
        width=45,
        height=14,
    )


def create_pause_overlay():
    """创建暂停覆盖层"""
    text = Text()
    text.append("\n⏸ 暂停\n\n", style="bold yellow")
    text.append("按 ", style="dim")
    text.append("P", style="dim yellow")
    text.append(" 继续游戏", style="dim")
    return Panel(
        Align.center(text, vertical="middle"),
        title="[bold yellow]PAUSED[/]",
        border_style="yellow",
        box=box.DOUBLE,
        width=28,
        height=7,
    )


def create_help_panel():
    text = Text()
    text.append("控制\n", style="bold")
    text.append("WASD/方向键 移动\n")
    text.append("空格 等待恢复\n")
    text.append("1-3 选择升级\n")
    text.append("B 打开商店\n")
    text.append("P 暂停游戏\n")
    text.append("Q 退出\n\n")
    text.append("命令\n", style="bold")
    text.append("/char 换角色\n")
    text.append("/fps 设帧率\n")
    text.append("/config 看配置\n")
    text.append("/shop 打开商店")
    return Panel(
        text, title="帮助", title_align="center", border_style="yellow", box=box.ROUNDED, height=15
    )


def create_upgrade(game):
    """创建升级界面 - 优化版"""
    if game.state != "upgrading":
        return None
    
    # 主升级选择区
    upgrade_text = Text()
    upgrade_text.append("升级！\n\n", style="bold yellow")
    for i, u in enumerate(game.upgrades):
        prefix = "> " if i == game.sel_upgrade else "  "
        color = u.get_style()
        text_style = "bold" if i == game.sel_upgrade else ""
        upgrade_text.append(f"{prefix}[{i + 1}] ", style="white")
        upgrade_text.append(f"{u.icon} {u.name}", style=f"{text_style} {color}")
        upgrade_text.append(f" [{u.get_rarity_name()}]\n", style=f"dim {color}")
        upgrade_text.append(f"      {u.desc}\n", style="dim white")
    
    # 当前属性区
    p = game.player
    stats_text = Text()
    stats_text.append("当前属性\n\n", style="bold cyan")
    stats_text.append(f"HP:   {p.hp}/{p.max_hp}\n", style="green")
    stats_text.append(f"ATK:  {p.atk}\n", style="red")
    stats_text.append(f"DEF:  {p.defense}\n", style="dim")
    stats_text.append(f"REG:  {p.regen}\n", style="dim")
    stats_text.append(f"LS:   {p.lifesteal}%\n", style="dim")
    stats_text.append(f"CRT:  {p.crit}%", style="dim")
    
    # 使用 Group 而不是 Layout，避免布局问题
    from rich.console import Group
    content = Group(
        Text(),  # 空行
        upgrade_text,
        Text("\n" + "─" * 50 + "\n", style="dim"),
        stats_text,
        Text(),  # 空行
        Text("WASD/方向键切换, Enter/1-3确认", style="dim"),
    )
    
    return Panel(
        Align.center(content, vertical="middle"),
        title="选择能力",
        title_align="center",
        border_style="yellow",
        box=box.DOUBLE,
        width=60,
        height=18,
    )


def create_gameover(game):
    p = game.player
    # 计算评分
    score = p.floor * 100 + p.kills * 10 + p.level * 50 + p.gold
    if p.kills > 0:
        rating = "⭐⭐⭐ SSS" if score > 2000 else "⭐⭐⭐ SS" if score > 1500 else "⭐⭐⭐ S" if score > 1000 else "⭐⭐ A" if score > 500 else "⭐ B" if score > 200 else "C"
    else:
        rating = "F"
    
    # 游戏时长格式化
    minutes = int(p.play_time // 60)
    seconds = int(p.play_time % 60)
    time_str = f"{minutes}分{seconds}秒"
    
    text = Text()
    text.append("GAME OVER\n\n", style="bold red")
    text.append(f"评分: {rating}\n\n", style="bold yellow")
    
    # 使用表格形式展示数据
    text.append(f"  到达层数:  {p.floor}\n", style="white")
    text.append(f"  击杀敌人:  {p.kills}\n", style="white")
    text.append(f"  角色等级:  {p.level}\n", style="white")
    text.append(f"  获得金币:  {p.gold}\n", style="white")
    text.append(f"  游戏时长:  {time_str}\n\n", style="white")
    
    # 敌人击杀详情
    if p.enemy_kills:
        text.append("击杀统计:\n", style="dim")
        enemy_names = {"slime": "史莱姆", "goblin": "哥布林", "skeleton": "骷髅", "orc": "兽人", "shadow": "暗影"}
        for enemy, count in sorted(p.enemy_kills.items()):
            name = enemy_names.get(enemy, enemy)
            text.append(f"  {name}: {count}  ", style="dim")
        text.append("\n\n")
    
    text.append("按任意键退出", style="dim")
    
    return Panel(
        Align.center(text, vertical="middle"),
        title="[bold red]游戏结束[/]",
        border_style="red",
        box=box.DOUBLE,
        width=38,
        height=16,
    )


def create_modern_title(frame=0):
    """创建现代化的启动界面"""
    term_width = console.width
    term_height = console.height
    
    # 动态标题动画
    chars = ["█", "▓", "▒", "░"]
    char = chars[frame % len(chars)]
    
    # Logo ASCII艺术
    logo_lines = [
        "",
        f"    {char*4}  {char*4}  {char*4}  {char*4}  {char*3}   {char*3}  {char*4}   {char*4}  {char*3} ",
        f"    {char*2}  {char*2}  {char*2}      {char*2}  {char*2}  {char*2}  {char*2}     {char*2}  {char*2}  {char*2} {char*2}",
        f"    {char*4}  {char*2}  {char*4}  {char*4}  {char*2} {char*2} {char*2}  {char*3}   {char*3}  {char*2}  {char*2}",
        f"    {char*2}  {char*2}  {char*2}      {char*2}  {char*2}  {char*2}  {char*2}     {char*2}  {char*2} {char*2} ",
        f"    {char*4}  {char*4}  {char*4}  {char*2}   {char*3}   {char*3}  {char*4}   {char*4}  {char*2}  {char*2}",
        "",
        "                    P I X E L   D U N G E O N",
        "                         像素地牢 v1.0",
        "",
    ]
    
    # 特性列表
    features = [
        ("♛", "bright_green", "4种角色", "勇者·法师·刺客·圣骑"),
        ("✦", "bright_red", "5种敌人", "史莱姆·哥布林·骷髅·兽人·暗影"),
        ("⌂", "bright_cyan", "无限地牢", "层层递进的Roguelike体验"),
        ("★", "bright_magenta", "升级系统", "12种能力自由搭配"),
        ("🛡", "bright_yellow", "商店系统", "购买道具强化角色"),
    ]
    
    # 操作说明
    controls = [
        ("WASD", "移动攻击"),
        ("空格", "等待恢复"),
        ("1-3", "选择升级"),
        ("B", "打开商店"),
        ("P", "暂停游戏"),
        ("/", "命令模式"),
        ("?", "帮助面板"),
    ]
    
    # 构建布局
    left_content = Text()
    left_content.append("游戏特色\n", style="bold yellow underline")
    left_content.append("─" * 20 + "\n", style="dim")
    for icon, color, title, desc in features:
        left_content.append(f"{icon} ", style=color)
        left_content.append(f"{title}", style="bold")
        left_content.append(f"\n   {desc}\n", style="dim")
    
    right_content = Text()
    right_content.append("操作指南\n", style="bold cyan underline")
    right_content.append("─" * 20 + "\n", style="dim")
    for key, action in controls:
        right_content.append(f"{key:>6}", style="bold white on dark_blue")
        right_content.append(f"  {action}\n", style="white")
    
    # 角色预览
    char_content = Text()
    char_content.append("选择角色 ", style="bold")
    char_content.append("(按数字切换)\n\n", style="dim")
    chars_preview = [
        ("1", "♛", "bright_green", "勇者", "平衡型"),
        ("2", "⚚", "bright_cyan", "法师", "高攻低防"),
        ("3", "⚔", "bright_red", "刺客", "暴击型"),
        ("4", "⚕", "bright_yellow", "圣骑", "坦克型"),
    ]
    for num, icon, color, name, desc in chars_preview:
        char_content.append(f"[{num}] ", style="dim")
        char_content.append(f"{icon}", style=f"bold {color}")
        char_content.append(f" {name:6}", style="bold")
        char_content.append(f" {desc}\n", style="dim")
    
    # 创建面板
    logo_text = Text("\n".join(logo_lines), style="cyan")
    logo_panel = Panel(
        Align.center(logo_text),
        border_style="cyan",
        box=box.DOUBLE if frame % 2 == 0 else box.ROUNDED,
    )
    
    left_panel = Panel(left_content, border_style="yellow", box=box.ROUNDED, title="[yellow]✨ 特色[/]")
    right_panel = Panel(right_content, border_style="cyan", box=box.ROUNDED, title="[cyan]⌨ 操作[/]")
    char_panel = Panel(char_content, border_style="green", box=box.ROUNDED, title="[green]🎭 角色[/]", width=30)
    
    # 底部提示
    footer = Text()
    footer.append("\n  按 ", style="dim")
    footer.append("任意键", style="bold yellow")
    footer.append(" 开始游戏  ·  ", style="dim")
    footer.append("--help", style="dim cyan")
    footer.append(" 查看帮助", style="dim")
    
    # 组合布局
    info_layout = Layout()
    info_layout.split_row(
        Layout(left_panel, ratio=2),
        Layout(right_panel, ratio=2),
        Layout(char_panel, ratio=1),
    )
    
    content_layout = Layout()
    content_layout.split_column(
        Layout(logo_panel, size=len(logo_lines) + 2),
        Layout(info_layout),
    )
    
    main_layout = Layout()
    main_layout.split_column(
        Layout(content_layout),
        Layout(footer, size=2),
    )
    
    return main_layout


def show_title_screen():
    """现代化的启动界面"""
    input_handler = InputHandler()
    input_handler.start()
    
    try:
        with Live(screen=True, refresh_per_second=10) as live:
            frame = 0
            while True:
                frame += 1
                layout = create_modern_title(frame)
                live.update(layout)
                
                # 检查按键
                key = input_handler.get_key()
                if key:
                    break
                
                time.sleep(0.1)
    except KeyboardInterrupt:
        # 优雅处理Ctrl+C
        pass
    finally:
        input_handler.stop()
        console.clear()


def main():
    parser = argparse.ArgumentParser(description="Pixel Dungeon - 像素地牢")
    parser.add_argument("--fps", type=int, default=30, help="帧率 (10-60)")
    parser.add_argument("--no-light", action="store_true", help="关闭光照")
    parser.add_argument("--no-particle", action="store_true", help="关闭粒子")
    parser.add_argument(
        "--char",
        type=str,
        default="default",
        choices=["default", "mage", "rogue", "paladin"],
        help="选择角色",
    )
    parser.add_argument("--skip-title", action="store_true", help="跳过标题画面")
    args = parser.parse_args()

    CONFIG.fps = max(10, min(60, args.fps))
    CONFIG.lighting = not args.no_light
    CONFIG.particles = not args.no_particle
    CONFIG.char_set = args.char

    if not args.skip_title:
        show_title_screen()

    game = Game()
    game.add_msg("♛ 欢迎来到像素地牢！", "cyan")
    game.add_msg("○史莱姆 ʘ哥布林 ☠骷髅 Ω兽人 ✦暗影", "dim")
    game.add_msg("♥血瓶 ◆金币 ⌂出口", "dim")

    input_handler = InputHandler()
    input_handler.start()
    frame_time = 1.0 / CONFIG.fps

    try:
        with Live(console=console, refresh_per_second=CONFIG.fps, screen=True) as live:
            last = time.time()
            while game.running:
                now = time.time()
                elapsed = now - last
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
                last = time.time()
                game.frame += 1
                game.update_animations()

                key = input_handler.get_key()
                if key:
                    # 处理暂停状态（除了P键外其他按键无效）
                    if game.paused:
                        if key in ("p", "P"):
                            game.toggle_pause()
                        continue
                    
                    # 处理商店状态
                    if game.shop_open:
                        if key == "\x1b":  # ESC关闭商店
                            game.close_shop()
                        elif key == "\r":  # 回车购买选中项
                            if game.shop_sel < len(game.shop_items):
                                game.buy_item(game.shop_sel)
                        elif key == "1" and len(game.shop_items) > 0:
                            game.buy_item(0)
                        elif key == "2" and len(game.shop_items) > 1:
                            game.buy_item(1)
                        elif key == "3" and len(game.shop_items) > 2:
                            game.buy_item(2)
                        elif key in ("w", "W") or key == "UP":
                            game.shop_sel = (game.shop_sel - 1) % len(game.shop_items)
                        elif key in ("s", "S") or key == "DOWN":
                            game.shop_sel = (game.shop_sel + 1) % len(game.shop_items)
                        continue
                    
                    if game.cmd_mode:
                        if key == "\r":
                            result = game.commands.execute(game.cmd_buffer)
                            if result:
                                game.add_msg(result, "yellow")
                            game.cmd_buffer = ""
                            game.cmd_suggestions = []
                        elif key == "\x7f":
                            game.cmd_buffer = game.cmd_buffer[:-1]
                        elif key == "\x1b":
                            game.cmd_buffer = ""
                            game.cmd_mode = False
                        elif key == "TAB":
                            if game.cmd_suggestions:
                                game.cmd_buffer = game.cmd_suggestions[0]
                        elif len(key) == 1 and key.isprintable():
                            game.cmd_buffer += key
                    elif game.state == "playing":
                        if key in ("q", "Q"):
                            # 退出确认（容错设计）
                            game.add_msg("按 Q 再次确认退出，或其他键取消", "yellow", "warning")
                            live.update(render_game(game))
                            
                            # 等待确认
                            confirm_key = None
                            while confirm_key is None:
                                confirm_key = input_handler.get_key()
                                if confirm_key is None:
                                    time.sleep(0.05)
                            
                            if confirm_key in ("q", "Q"):
                                break
                            else:
                                game.add_msg("取消退出", "dim", "info")
                        elif key == "?":
                            game.show_help = not game.show_help
                        elif key == "/":
                            game.cmd_mode = True
                            game.cmd_buffer = ""
                        elif key in ("b", "B"):
                            game.open_shop()
                        elif key in ("p", "P"):
                            game.toggle_pause()
                        elif key in ("w", "W") or key == "UP":
                            game.move(0, -1)
                        elif key in ("s", "S") or key == "DOWN":
                            game.move(0, 1)
                        elif key in ("a", "A") or key == "LEFT":
                            game.move(-1, 0)
                        elif key in ("d", "D") or key == "RIGHT":
                            game.move(1, 0)
                        elif key == " ":
                            game.wait()
                    elif game.state == "upgrading":
                        if key == "\r":  # 回车确认选中项
                            game.apply_upgrade(game.sel_upgrade)
                        elif key == "1":
                            game.apply_upgrade(0)
                        elif key == "2":
                            game.apply_upgrade(1)
                        elif key == "3":
                            game.apply_upgrade(2)
                        elif key in ("w", "W") or key == "UP":
                            game.sel_upgrade = (game.sel_upgrade - 1) % 3
                        elif key in ("s", "S") or key == "DOWN":
                            game.sel_upgrade = (game.sel_upgrade + 1) % 3
                    elif game.state == "game_over":
                        time.sleep(0.3)
                        break

                # 渲染游戏界面
                main_layout = render_game(game)
                live.update(main_layout)

    except KeyboardInterrupt:
        # 优雅处理Ctrl+C
        pass
    finally:
        input_handler.stop()
        console.clear()
        console.print("[bold green]👋 感谢游玩像素地牢！[/]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # 全局Ctrl+C处理
        console.clear()
        console.print("[dim]👋 已退出游戏[/]")
        sys.exit(0)
