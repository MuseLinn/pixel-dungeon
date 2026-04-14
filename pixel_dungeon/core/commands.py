#!/usr/bin/env python3
"""命令处理器 - 处理游戏内命令输入"""

from typing import List

from ..config import CONFIG
from ..assets import GAME_ASSETS, CHARACTERS


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
        if partial.startswith("/"):
            partial = partial[1:]
        return [cmd for cmd in self.COMMANDS.keys() if cmd.startswith(partial.lower())]

    def execute(self, cmd_line: str) -> str:
        cmd_line = cmd_line.strip()
        if not cmd_line.startswith("/"):
            return "[yellow]命令必须以 / 开头，例如 /help[/]"
        cmd_line = cmd_line[1:]
        parts = cmd_line.split()
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

        suggestions = [
            c for c in self.COMMANDS.keys() if c.startswith(cmd[0]) and len(c) > 1
        ]
        if suggestions:
            return f"[yellow]未知命令: /{cmd}[/]\n[dim]你是否想输入: /{', /'.join(suggestions[:3])}?\n输入 /help 查看所有命令[/]"
        return f"[yellow]未知命令: /{cmd}[/]\n[dim]输入 /help 查看所有命令[/]"

    def cmd_help(self, args):
        lines = ["📖 可用命令\n"]
        for cmd, desc in self.COMMANDS.items():
            if len(cmd) > 1:
                lines.append(f"  /{cmd} - {desc}")
        lines.append("\n提示: 输入 / 或 Ctrl+X 进入命令模式，按 TAB 自动补全")
        return "\n".join(lines)

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
            except (ValueError, TypeError):
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
        char_map = {
            "default": "default",
            "mage": "mage",
            "rogue": "rogue",
            "paladin": "paladin",
        }
        if args and args[0].lower() in char_map:
            new_char = char_map[args[0].lower()]
            CONFIG.char_set = new_char
            asset = GAME_ASSETS[CHARACTERS[new_char]]
            return f"🎭 切换为 {asset['name']} ({new_char})"
        valid = ", ".join(char_map.keys())
        return f"❌ 用法: /char [{valid}]"

    def cmd_config(self, args):
        return (
            f"📊 当前配置:\n"
            f"  FPS: {CONFIG.fps}\n"
            f"  地图: {CONFIG.map_width}x{CONFIG.map_height}\n"
            f"  光照: {'开启' if CONFIG.lighting else '关闭'}\n"
            f"  粒子: {'开启' if CONFIG.particles else '关闭'}\n"
            f"  角色: {CONFIG.char_set}"
        )

    def cmd_shop(self, args):
        self.game.open_shop()
        return None

    def cmd_heal(self, args):
        if args:
            try:
                amount = int(args[0])
            except (ValueError, TypeError):
                amount = 100
        else:
            amount = 100
        self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + amount)
        return f"❤️ 恢复 {amount} HP"

    def cmd_level(self, args):
        if args:
            try:
                level = int(args[0])
                self.game.player.level = max(1, level)
                return f"📈 等级设置为 {level}"
            except (ValueError, TypeError):
                return "❌ 用法: /level [数字]"
        return f"📊 当前等级: {self.game.player.level}"

    def cmd_gold(self, args):
        if args:
            try:
                amount = int(args[0])
                self.game.player.gold += amount
                return f"💰 获得 {amount} 金币"
            except (ValueError, TypeError):
                return "❌ 用法: /gold [数字]"
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
