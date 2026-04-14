#!/usr/bin/env python3
"""命令处理器 - 处理游戏内命令输入"""

from typing import List

from ..config import CONFIG
from ..assets import GAME_ASSETS, CHARACTERS
from ..utils.i18n import _


class CommandHandler:
    COMMANDS = {
        "help": _("cmd_help_desc"),
        "h": _("cmd_help_short_desc"),
        "quit": _("cmd_quit_desc"),
        "q": _("cmd_quit_short_desc"),
        "fps": _("cmd_fps_desc"),
        "light": _("cmd_light_desc"),
        "particle": _("cmd_particle_desc"),
        "char": _("cmd_char_desc"),
        "config": _("cmd_config_desc"),
        "shop": _("cmd_shop_desc"),
        "heal": _("cmd_heal_desc"),
        "level": _("cmd_level_desc"),
        "gold": _("cmd_gold_desc"),
        "god": _("cmd_god_desc"),
        "killall": _("cmd_killall_desc"),
        "next": _("cmd_next_desc"),
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
            return f"[yellow]{_('cmd_must_start_with_slash')}[/]"
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
            return f"[yellow]{_('unknown_cmd', cmd)}[/]\n[dim]{_('did_you_mean', ', /'.join(suggestions[:3]))}\n{_('type_help_for_commands')}[/]"
        return (
            f"[yellow]{_('unknown_cmd', cmd)}[/]\n[dim]{_('type_help_for_commands')}[/]"
        )

    def cmd_help(self, args):
        lines = [f"📖 {_('available_commands')}\n"]
        for cmd, desc in self.COMMANDS.items():
            if len(cmd) > 1:
                lines.append(f"  /{cmd} - {desc}")
        lines.append(f"\n{_('cmd_mode_hint')}")
        return "\n".join(lines)

    def cmd_quit(self, args):
        self.game.running = False
        return f"👋 {_('quit_game')}"

    def cmd_fps(self, args):
        if args:
            try:
                fps = int(args[0])
                if 10 <= fps <= 60:
                    CONFIG.fps = fps
                    return f"✅ {_('set_fps', fps)}"
                return "⚠️ " + _("fps_range_error")
            except (ValueError, TypeError):
                return "❌ " + _("fps_usage")
        return f"📊 {_('current_fps', CONFIG.fps)}"

    def cmd_light(self, args):
        if args:
            CONFIG.lighting = args[0].lower() in ("on", "true", "1", "yes")
        state = "✅ " + _("on") if CONFIG.lighting else "❌ " + _("off")
        return f"💡 {_('lighting')}: {state}"

    def cmd_particle(self, args):
        if args:
            CONFIG.particles = args[0].lower() in ("on", "true", "1", "yes")
        state = "✅ " + _("on") if CONFIG.particles else "❌ " + _("off")
        return f"✨ {_('particles')}: {state}"

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
            from ..utils.i18n import _

            asset = GAME_ASSETS[CHARACTERS[new_char]]
            char_name = _(asset.get("name_key", asset.get("name", new_char)))
            return f"🎭 {_('switched_to', char_name)} ({new_char})"
        valid = ", ".join(char_map.keys())
        return f"❌ {_('char_usage', valid)}"

    def cmd_config(self, args):
        from ..utils.i18n import _

        return (
            f"📊 {_('current_config')}:\n"
            f"  {_('fps')}: {CONFIG.fps}\n"
            f"  {_('map')}: {CONFIG.map_width}x{CONFIG.map_height}\n"
            f"  {_('lighting')}: {(_('on') if CONFIG.lighting else _('off'))}\n"
            f"  {_('particles')}: {(_('on') if CONFIG.particles else _('off'))}\n"
            f"  {_('character')}: {CONFIG.char_set}"
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
        return f"❤️ {_('healed_hp', amount)}"

    def cmd_level(self, args):
        if args:
            try:
                level = int(args[0])
                self.game.player.level = max(1, level)
                return f"📈 {_('set_level', level)}"
            except (ValueError, TypeError):
                return "❌ " + _("level_usage")
        return f"📊 {_('current_level', self.game.player.level)}"

    def cmd_gold(self, args):
        if args:
            try:
                amount = int(args[0])
                self.game.player.gold += amount
                return f"💰 {_('got_gold_cmd', amount)}"
            except (ValueError, TypeError):
                return "❌ " + _("gold_usage")
        return f"💰 {_('current_gold', self.game.player.gold)}"

    def cmd_god(self, args):
        self.game.player.max_hp = 9999
        self.game.player.hp = 9999
        self.game.player.atk = 999
        self.game.player.defense = 99
        self.game.player.crit = 100
        return "🌟 " + _("god_mode_on")

    def cmd_killall(self, args):
        count = len(self.game.enemies)
        self.game.enemies.clear()
        return f"💀 {_('killed_enemies', count)}"

    def cmd_next(self, args):
        self.game.next_floor()
        return "🚪 " + _("next_floor_cmd")
