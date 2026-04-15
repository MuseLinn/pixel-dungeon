#!/usr/bin/env python3
"""渲染模块 - 所有UI渲染函数"""

import math
from typing import List, Tuple, Optional

from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

from ..config import CONFIG
from ..assets import GAME_ASSETS, TileType, get_tile_asset
from ..utils.i18n import _
from ..utils.theme import get_style


class Renderer:
    def __init__(self, console):
        self.console = console

    @staticmethod
    def get_bar(val: int, max_val: int, width: int = 20) -> Tuple[str, int]:
        if max_val <= 0:
            return "░" * width, 0
        ratio = val / max_val
        filled = int(width * ratio)
        bar = "█" * filled + "░" * (width - filled)
        return bar, filled

    @staticmethod
    def get_light_style(base_style: str, light: float) -> str:
        if light >= 0.8:
            return base_style
        elif light >= 0.5:
            return f"dim {base_style}"
        elif light >= 0.2:
            return f"dim {base_style}"
        else:
            return get_style("dim black")

    def get_viewport(self, game) -> Tuple[int, int, int, int]:
        tile_w = CONFIG.tile_width
        tile_h = CONFIG.tile_height
        bottom_h = 6

        main_h = self.console.height - bottom_h
        map_avail_h = main_h - 2
        map_avail_w = int(self.console.width * 0.75) - 2

        vp_w = max(map_avail_w // tile_w, 8)
        vp_h = max(map_avail_h // tile_h, 6)

        px, py = game.player.x, game.player.y

        x1 = px - vp_w // 2
        y1 = py - (vp_h - 1) // 2
        x2 = x1 + vp_w
        y2 = y1 + vp_h

        return x1, y1, x2, y2

    def _get_tile_sprite(
        self, game, x: int, y: int, light: float
    ) -> Tuple[List[str], str]:
        if 0 <= x < CONFIG.map_width and 0 <= y < CONFIG.map_height:
            px, py = game.player.x, game.player.y
            if x == px and y == py:
                sprite, style = game.player.get_render_sprite()
            else:
                enemy = game.get_enemy_at(x, y)
                if enemy and enemy.is_alive():
                    sprite, style = enemy.get_render_sprite()
                else:
                    tile = game.map[y][x]
                    asset = get_tile_asset(tile)
                    sprite = asset["sprite"]
                    style = asset["style"]
            style = self.get_light_style(style, light)
            return [row for row in sprite], style
        else:
            void = ["░" * CONFIG.tile_width] * CONFIG.tile_height
            return void, get_style("dim black")

    def create_map_panel(self, game) -> Panel:
        tile_w = CONFIG.tile_width
        tile_h = CONFIG.tile_height
        x1, y1, x2, y2 = self.get_viewport(game)

        particle_map = {}
        for p in game.particles.particles:
            tx, ty = int(p.x), int(p.y)
            if (tx, ty) not in particle_map:
                particle_map[(tx, ty)] = p

        text_map = {}
        for t in game.particles.texts:
            tx, ty = int(t.x), int(t.y)
            if (tx, ty) not in text_map:
                text_map[(tx, ty)] = t

        lines = []
        px, py = game.player.x, game.player.y

        for ly in range(y1, y2):
            row_texts = [Text() for _ in range(tile_h)]

            for lx in range(x1, x2):
                in_bounds = 0 <= lx < CONFIG.map_width and 0 <= ly < CONFIG.map_height

                if CONFIG.lighting and in_bounds:
                    dist = math.sqrt((lx - px) ** 2 + (ly - py) ** 2)
                    if dist <= CONFIG.view_distance:
                        light = max(0.2, 1.0 - (dist / CONFIG.view_distance) * 0.4)
                    else:
                        light = 0
                else:
                    light = 1.0 if not CONFIG.lighting and in_bounds else 0

                sprite_rows, style = self._get_tile_sprite(game, lx, ly, light)
                sprite_rows = list(sprite_rows)

                if hasattr(game, "transition_timer") and game.transition_timer > 0:
                    import random

                    progress = 1.0 - (game.transition_timer / 25.0)
                    vp_w = x2 - x1
                    vp_h = y2 - y1
                    max_dist = math.sqrt((vp_w / 2) ** 2 + (vp_h / 2) ** 2) + 2
                    td = math.sqrt((lx - px) ** 2 + (ly - py) ** 2)
                    if td > progress * max_dist:
                        gch = random.choice(
                            [
                                "▓",
                                "▒",
                                "░",
                                "█",
                                "▀",
                                "▄",
                                "▌",
                                "▐",
                                "▖",
                                "▗",
                                "▘",
                                "▙",
                                "▚",
                                "▛",
                                "▜",
                                "▝",
                                "▞",
                                "▟",
                            ]
                        )
                        sprite_rows = [gch * tile_w for _ in range(tile_h)]
                        style = random.choice(["dim cyan", "dim blue", "dim magenta"])

                if (
                    hasattr(game, "menu_transition_timer")
                    and game.menu_transition_timer > 0
                ):
                    import random

                    progress = 1.0 - (game.menu_transition_timer / 20.0)
                    vp_w = x2 - x1
                    vp_h = y2 - y1
                    max_dist = math.sqrt((vp_w / 2) ** 2 + (vp_h / 2) ** 2) + 2
                    td = math.sqrt((lx - px) ** 2 + (ly - py) ** 2)
                    direction = getattr(game, "menu_transition_type", "out")
                    show_glitch = (
                        td > (1.0 - progress) * max_dist
                        if direction == "out"
                        else td < progress * max_dist
                    )
                    if show_glitch:
                        gch = random.choice(
                            [
                                "▓",
                                "▒",
                                "░",
                                "█",
                                "▀",
                                "▄",
                                "▌",
                                "▐",
                                "▖",
                                "▗",
                                "▘",
                                "▙",
                                "▚",
                                "▛",
                                "▜",
                                "▝",
                                "▞",
                                "▟",
                            ]
                        )
                        sprite_rows = [gch * tile_w for _ in range(tile_h)]
                        style = random.choice(["dim cyan", "dim blue", "dim magenta"])

                if light > 0 and in_bounds:
                    p = particle_map.get((lx, ly))
                    if p:
                        mid_row = tile_h // 2
                        mid_col = tile_w // 2
                        row = list(sprite_rows[mid_row])
                        if mid_col < len(row):
                            row[mid_col] = p.char
                        sprite_rows[mid_row] = "".join(row)
                        style = self.get_light_style(get_style(p.style), light)

                    t = text_map.get((lx, ly))
                    if t:
                        text = t.text[:tile_w]
                        row = list(sprite_rows[0])
                        for i, ch in enumerate(text):
                            if i < len(row):
                                row[i] = ch
                        sprite_rows[0] = "".join(row)
                        style = self.get_light_style(
                            get_style(t.get_alpha_style()), light
                        )

                for i in range(tile_h):
                    row_texts[i].append(sprite_rows[i], style=style)

            lines.extend(row_texts)

        main_h = self.console.height - 6
        panel_content_h = main_h - 2
        content_h = (y2 - y1) * tile_h
        pad_top = (panel_content_h - content_h) // 2
        pad_bottom = panel_content_h - content_h - pad_top

        padded_lines = (
            [Text() for _ in range(pad_top)]
            + lines
            + [Text() for _ in range(pad_bottom)]
        )
        map_text = Text("\n").join(padded_lines)

        return Panel(
            map_text,
            title=f"[bold cyan]{_('floor_transition', game.floor).strip()}[/bold cyan]",
            border_style=get_style("cyan"),
            box=box.ROUNDED,
            padding=(0, 0),
            height=main_h,
        )

    def create_minimap_panel(self, game) -> Panel:
        mm_text = Text()
        px, py = game.player.x, game.player.y
        x1, y1, x2, y2 = self.get_viewport(game)

        max_mm_w = 28
        max_mm_h = 12

        scale_x = max(1, math.ceil(CONFIG.map_width / max_mm_w))
        scale_y = max(1, math.ceil(CONFIG.map_height / max_mm_h))

        mm_w = (CONFIG.map_width + scale_x - 1) // scale_x
        mm_h = (CONFIG.map_height + scale_y - 1) // scale_y

        for my in range(mm_h):
            for mx in range(mm_w):
                tx1 = mx * scale_x
                ty1 = my * scale_y
                tx2 = min(tx1 + scale_x, CONFIG.map_width)
                ty2 = min(ty1 + scale_y, CONFIG.map_height)

                explored = False
                has_wall = False
                has_exit = False
                has_potion = False
                has_gold = False
                dominant = TileType.EMPTY

                for ty in range(ty1, ty2):
                    for tx in range(tx1, tx2):
                        if game.explored_map[ty][tx]:
                            explored = True
                            tile = game.map[ty][tx]
                            if tile == TileType.WALL:
                                has_wall = True
                            elif tile == TileType.EXIT:
                                has_exit = True
                            elif tile == TileType.POTION:
                                has_potion = True
                            elif tile == TileType.GOLD:
                                has_gold = True
                            elif tile == TileType.EMPTY:
                                dominant = TileType.EMPTY

                cx = tx1 + scale_x / 2
                cy = ty1 + scale_y / 2
                in_viewport = x1 <= cx < x2 and y1 <= cy < y2
                is_player = (tx1 <= px < tx2) and (ty1 <= py < ty2)

                if not explored:
                    char = "·"
                    style = "dim black"
                elif is_player:
                    char = "♛"
                    style = "bright_green"
                elif in_viewport:
                    if has_wall:
                        char = "█"
                        style = "bright_black"
                    elif has_exit:
                        char = "⌂"
                        style = "bright_cyan"
                    elif has_potion:
                        char = "♥"
                        style = "bright_red"
                    elif has_gold:
                        char = "◆"
                        style = "bright_yellow"
                    else:
                        char = "·"
                        style = "white"
                else:
                    if has_wall:
                        char = "▓"
                        style = "dim"
                    elif has_exit:
                        char = "⌂"
                        style = "dim cyan"
                    elif has_potion:
                        char = "♥"
                        style = "dim red"
                    elif has_gold:
                        char = "◆"
                        style = "dim yellow"
                    else:
                        char = "·"
                        style = "dim"

                mm_text.append(char, style=style)
            mm_text.append("\n")

        return Panel(
            mm_text,
            title=f"[bold cyan]{_('map')}[/bold cyan]",
            border_style=get_style("cyan"),
            box=box.ROUNDED,
            padding=(0, 0),
            height=12,
        )

    def create_stats_panel(self, game) -> Panel:
        p = game.player

        text = Text()
        sprite, _style = p.get_render_sprite()
        text.append(f"{sprite[0]} ", style=get_style("bright_green"))
        text.append(
            f"Lv.{p.level}{_('level_suffix')}\n", style=get_style("bold yellow")
        )

        hp_bar, hp_filled = self.get_bar(p.hp, p.max_hp, 14)
        text.append("生命 ", style=get_style("red"))
        text.append(f"{p.hp}/{p.max_hp} ")
        text.append(hp_bar[:hp_filled], style=get_style("red"))
        text.append(hp_bar[hp_filled:] + "\n")

        exp_bar, exp_filled = self.get_bar(p.exp, p.exp_next, 14)
        text.append("经验 ", style=get_style("cyan"))
        text.append(f"{p.exp}/{p.exp_next} ")
        text.append(exp_bar[:exp_filled], style=get_style("cyan"))
        text.append(exp_bar[exp_filled:] + "\n")

        text.append(
            f"攻{p.atk} 防{p.defense} 暴{p.crit}% 吸{p.lifesteal}% 恢{p.regen} 金{p.gold}G\n",
            style=get_style("white"),
        )

        return Panel(
            text,
            title="[bold green]状态[/bold green]",
            border_style=get_style("green"),
            box=box.ROUNDED,
            padding=(0, 1),
            height=6,
        )

    def create_log_panel(self, game, height: int) -> Panel:
        log_text = Text()
        content_h = max(height - 2, 1)
        actual_count = min(content_h, len(game.messages))

        for msg, style, msg_type in game.messages[-content_h:]:
            if msg_type == "combat":
                prefix = "⚔ "
            elif msg_type == "item":
                prefix = "♦ "
            elif msg_type == "level":
                prefix = "⬆ "
            elif msg_type == "shop":
                prefix = "💰 "
            elif msg_type == "achievement":
                prefix = "🏆 "
            else:
                prefix = "• "

            log_text.append(f"{prefix}{msg}\n", style=get_style(style))

        return Panel(
            log_text,
            title="[bold yellow]日志[/bold yellow]",
            border_style=get_style("yellow"),
            box=box.ROUNDED,
            height=height,
        )

    def create_legend_panel(self) -> Panel:
        table = Table(show_header=False, box=None, padding=(0, 2), expand=False)
        for _i in range(6):
            table.add_column()

        def cell(icon: str, style: str, name: str) -> Text:
            t = Text()
            t.append(icon, style=style)
            t.append(f" {name}")
            return t

        table.add_row(
            cell("♛", "bright_green", _("hero")),
            cell("⚚", "bright_cyan", _("mage")),
            cell("⚔", "bright_red", _("assassin")),
            cell("⚕", "bright_yellow", _("paladin")),
            cell("◉", "green", _("slime")),
            cell("◓", "yellow", _("goblin")),
        )
        table.add_row(
            cell("☠", "white", _("skeleton")),
            cell("◈", "red", _("orc")),
            cell("◐", "magenta", _("shadow")),
            cell("♥", "bright_red", _("potion")),
            cell("◆", "bright_yellow", _("gold")),
            cell("⌂", "bright_cyan", _("exit")),
        )
        table.add_row(
            cell("▓", "bright_black", _("wall")),
            Text(
                "WASD移动 B商店 P暂停 S存档 R重启 M菜单 ?帮助 /命令",
                style=get_style("dim"),
            ),
            Text(),
            Text(),
            Text(),
            Text(),
        )

        return Panel(
            table,
            border_style=get_style("dim"),
            box=box.ROUNDED,
            padding=(0, 1),
            height=5,
        )

    def create_help_panel(self) -> Panel:
        text = Text()
        text.append(f"{_('game_help')}\n\n", style=get_style("bold yellow"))
        text.append(f"{_('move_attack')}\n", style=get_style("white"))
        text.append(f"{_('space_wait')}\n", style=get_style("white"))
        text.append(f"{_('b_shop')}\n", style=get_style("white"))
        text.append(f"{_('p_pause')}\n", style=get_style("white"))
        text.append(f"{_('cmd_mode')}\n", style=get_style("white"))
        text.append(f"{_('q_show_help')}\n", style=get_style("white"))
        text.append(f"{_('q_quit')}\n", style=get_style("white"))

        return Panel(
            text,
            title=f"[bold yellow]{_('help')}[/bold yellow]",
            border_style=get_style("yellow"),
            box=box.ROUNDED,
            height=12,
        )

    def create_upgrade_panel(self, game, frame: int = 0) -> Panel:
        rarity_colors = {
            "common": "white",
            "rare": "bright_cyan",
            "epic": "bright_magenta",
            "legendary": "bright_yellow",
        }
        rarity_panel_styles = {
            "common": ("white", "bright_black"),
            "rare": ("bright_cyan", "cyan"),
            "epic": ("bright_magenta", "magenta"),
            "legendary": ("bright_yellow", "yellow"),
        }

        selected_upgrade = game.upgrades[game.sel_upgrade] if game.upgrades else None
        sel_rarity = selected_upgrade.rarity if selected_upgrade else "common"
        panel_main, panel_dim = rarity_panel_styles.get(sel_rarity, ("white", "dim"))

        text = Text()
        text.append(
            self._glitch_text(_("upgrade_choice"), frame, f"bold {panel_main}", 0.15)
        )
        text.append("\n\n", style="")

        for i, upgrade in enumerate(game.upgrades[:3]):
            num = i + 1
            color = rarity_colors.get(upgrade.rarity, "white")
            is_selected = i == game.sel_upgrade
            sel_prefix = ">>> " if is_selected else "    "
            text.append(
                f"{sel_prefix}",
                style=f"bold {panel_main} on dark_green" if is_selected else "",
            )
            text.append(f"[{num}] ", style=f"bold {panel_main}")
            text.append(self._glitch_text(upgrade.name, frame, f"bold {color}", 0.08))
            text.append("\n", style="")
            text.append(f"    {upgrade.description}\n", style=get_style("dim"))
            text.append("\n", style="")

        text.append(_("choose_upgrade"), style=get_style("dim"))

        pulse_box = box.DOUBLE if frame % 20 < 10 else box.ROUNDED
        border = panel_main if frame % 24 < 12 else panel_dim

        return Panel(
            Align.center(text, vertical="middle"),
            title=f"[bold {panel_main}]{_('upgrade')}[/bold {panel_main}]",
            border_style=border,
            box=pulse_box,
            width=46,
            height=18,
        )

    def create_shop_panel(self, game) -> Panel:
        text = Text()
        text.append(f"{_('shop')}\n\n", style=get_style("bold yellow"))

        items = game.shop.items
        for i, item in enumerate(items):
            num = i + 1
            sel_marker = "▶ " if i == game.shop.selected_index else "  "
            text.append(f"{sel_marker}[{num}] ", style=get_style("bold yellow"))
            text.append(f"{item.name} ", style=get_style("bold white"))
            text.append(f"({item.price}G)\n", style=get_style("yellow"))
            text.append(f"    {item.description}\n", style=get_style("dim"))

        text.append("\n")
        text.append(
            f"{_('ws_switch')}  {_('enter_buy')}  {_('esc_close')}",
            style=get_style("dim"),
        )

        return Panel(
            text,
            title=f"[bold yellow]{_('shop')}[/bold yellow]",
            border_style=get_style("yellow"),
            box=box.ROUNDED,
            height=20,
        )

    def create_gameover_panel(self, game) -> Panel:
        p = game.player

        text = Text()
        text.append("\n")
        text.append(f"💀 {_('game_over')} 💀\n\n", style=get_style("bold red"))
        text.append(f"{_('reached_floor', game.floor)}\n", style=get_style("yellow"))
        text.append(f"{_('final_level')}: {p.level}\n", style=get_style("cyan"))
        text.append(
            f"{_('enemies_killed')}: {game.stats.get('enemies_killed', 0)}\n",
            style=get_style("red"),
        )
        text.append(
            f"{_('gold_earned')}: {game.stats.get('total_gold_earned', 0)}G\n",
            style=get_style("yellow"),
        )
        text.append("\n")
        text.append(f"{_('r_restart_m_menu_q_quit')}", style=get_style("dim"))

        return Panel(
            Align.center(text, vertical="middle"),
            title=f"[bold red]{_('game_over')}[/bold red]",
            border_style=get_style("red"),
            box=box.DOUBLE,
            width=40,
            height=13,
        )

    def _glitch_text(
        self, base: str, frame: int, style: str, glitch_prob: float = 0.12
    ) -> Text:
        import random

        glitch_chars = ["▓", "▒", "░", "█", "▀", "▄", "▌", "▐"]
        result = Text()
        active = glitch_prob if frame % 8 < 4 else 0.02
        for ch in base:
            if ch == " " or random.random() > active:
                result.append(ch, style=style)
            else:
                result.append(
                    random.choice(glitch_chars), style=f"dim {style.split()[-1]}"
                )
        return result

    def create_pause_panel(self, frame: int = 0) -> Panel:
        text = Text()
        text.append(self._glitch_text(_("game_paused"), frame, "bold yellow", 0.18))
        text.append("\n\n", style="")
        text.append(f"{_('p_resume')}\n", style=get_style("white"))
        text.append(f"{_('s_save_game')}\n", style=get_style("white"))
        text.append(f"{_('r_restart_game')}\n", style=get_style("white"))
        text.append(f"{_('m_return_menu')}\n", style=get_style("white"))
        text.append(f"{_('q_quit_game')}\n", style=get_style("white"))

        pulse_box = box.DOUBLE if frame % 30 < 15 else box.ROUNDED
        border = "bright_yellow" if frame % 40 < 20 else "yellow"

        return Panel(
            Align.center(text, vertical="middle"),
            title=f"[bold yellow]{_('game_paused')}[/bold yellow]",
            border_style=border,
            box=pulse_box,
            width=30,
            height=10,
        )

    def create_transition_panel(self, game, frame: int = 0) -> Panel:
        import random

        base = (
            game.transition_text
            if hasattr(game, "transition_text")
            else _("teleporting")
        )
        glitch_chars = ["▓", "▒", "░", "█", "▀", "▄", "▌", "▐"]
        glitch_prob = 0.25 if frame % 8 < 4 else 0.05

        line = Text()
        for ch in base:
            if random.random() < glitch_prob:
                line.append(random.choice(glitch_chars), style=get_style("dim cyan"))
            else:
                style = "bright_cyan" if frame % 6 < 3 else "cyan"
                line.append(ch, style=style)

        return Panel(
            Align.center(line, vertical="middle"),
            border_style=get_style("cyan"),
            box=box.DOUBLE if frame % 4 < 2 else box.ROUNDED,
            width=max(len(base) + 6, 20),
            height=5,
        )

    def render_game(self, game) -> Layout:
        layout = Layout()

        map_panel = self.create_map_panel(game)

        legend_h = 6
        stats_h = 6
        minimap_h = 12
        log_h = max(self.console.height - legend_h - stats_h - minimap_h, 4)
        log_panel = self.create_log_panel(game, log_h)

        right_layout = Layout()
        right_layout.split_column(
            Layout(self.create_stats_panel(game), size=stats_h),
            Layout(self.create_minimap_panel(game), size=minimap_h),
            Layout(log_panel, size=log_h),
        )

        main = Layout()
        main.split_row(
            Layout(map_panel, ratio=3),
            Layout(right_layout, ratio=1),
        )

        bottom = Layout(self.create_legend_panel(), size=6)

        layout.split_column(
            Layout(main, ratio=1),
            Layout(bottom, size=6),
        )

        return layout

    def _modal_layout(self, panel) -> Layout:
        total_h = self.console.height
        h = panel.height or 14
        spacer = max(1, (total_h - h) // 2)

        layout = Layout()
        layout.split_column(
            Layout(size=spacer),
            Layout(Align.center(panel, vertical="middle"), size=h),
            Layout(size=spacer),
        )
        return layout

    def render_with_upgrade(self, game, frame: int = 0) -> Layout:
        return self._modal_layout(self.create_upgrade_panel(game, frame))

    def render_with_shop(self, game) -> Layout:
        return self._modal_layout(self.create_shop_panel(game))

    def render_with_pause(self, frame: int = 0) -> Layout:
        return self._modal_layout(self.create_pause_panel(frame))

    def render_with_gameover(self, game) -> Layout:
        return self._modal_layout(self.create_gameover_panel(game))

    def render_with_transition(self, game, frame: int = 0) -> Layout:
        return self.render_game(game)

    def render_with_menu_transition(
        self, game, frame: int = 0, direction: str = "out"
    ) -> Layout:
        return self.render_game(game)

    def render_with_command_overlay(
        self, game, cmd_buffer: str = "", suggestions: list = None
    ) -> Layout:
        from rich.align import Align

        layout = self.render_game(game)

        text = Text()
        text.append(f"{_('cmd_mode_overlay')}  ", style=get_style("bold yellow"))
        text.append("/", style=get_style("dim"))
        text.append(cmd_buffer, style=get_style("white"))

        if suggestions:
            text.append("  ", style=get_style("dim"))
            for i, sugg in enumerate(suggestions[:3]):
                if i > 0:
                    text.append(" ", style=get_style("dim"))
                text.append(f"/{sugg}", style=get_style("dim cyan"))

        overlay = Panel(
            text,
            border_style=get_style("yellow"),
            box=box.ROUNDED,
            height=3,
        )

        cmd_layout = Layout()
        cmd_layout.split_column(
            Layout(layout, ratio=1),
            Layout(overlay, size=3),
        )

        return cmd_layout
