#!/usr/bin/env python3
"""启动画面和覆盖层 UI"""

import os
import time

from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
from rich.live import Live

from ..input_handler import CrossPlatformInputHandler
from ..utils.save_load import SaveManager
from ..utils.i18n import _
from ..utils.theme import get_style
from ..utils.ota import get_version
from ..systems.achievements import AchievementManager
from ..config import CONFIG


def _glitch_text(base: str, frame: int, style: str, glitch_prob: float = 0.12) -> Text:
    import random

    glitch_chars = ["▓", "▒", "░", "█", "▀", "▄", "▌", "▐"]
    result = Text()
    active = glitch_prob if frame % 8 < 4 else 0.02
    for ch in base:
        if ch == " " or random.random() > active:
            result.append(ch, style=style)
        else:
            result.append(random.choice(glitch_chars), style=f"dim {style.split()[-1]}")
    return result


def create_matrix_transition_layout(frame: int, console) -> Layout:
    import random

    total_w = console.width
    total_h = console.height
    matrix_chars = "0123456789ABCDEFｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏｦｧｨｩｪｫｬｭｮｯ"

    total_frames = 22
    progress = min(frame / total_frames, 1.0)
    active_cols = max(2, int(total_w * progress * 1.2))

    occupied = [set() for _ in range(total_w)]
    columns = [[] for _ in range(total_w)]
    for _ in range(active_cols):
        cx = random.randint(0, total_w - 1)
        head_y = random.randint(0, int(total_h * progress) + 2)
        trail_len = random.randint(3, 8)
        for dy in range(trail_len + 1):
            y = head_y - dy
            if 0 <= y < total_h and y not in occupied[cx]:
                occupied[cx].add(y)
                columns[cx].append((y, dy))

    lines = []
    for y in range(total_h):
        line = Text()
        for x in range(total_w):
            cell = None
            for dy in sorted(columns[x]):
                if dy[0] == y:
                    cell = dy[1]
                    break
            if cell is None:
                line.append(" ")
            elif cell == 0:
                line.append(
                    random.choice(matrix_chars),
                    style=get_style("bright_white on green"),
                )
            elif cell == 1:
                line.append(
                    random.choice(matrix_chars), style=get_style("bright_green")
                )
            elif cell <= 3:
                line.append(random.choice(matrix_chars), style=get_style("green"))
            else:
                line.append(random.choice(matrix_chars), style=get_style("dim green"))
        lines.append(line)

    full_text = Text("\n").join(lines)
    layout = Layout(full_text)
    return layout


def create_modern_title(
    frame: int = 0,
    menu_index: int = 0,
    menu_items: list = None,
    saves: list = None,
    update_info: dict = None,
) -> Layout:
    import random

    if menu_items is None:
        menu_items = []
    if saves is None:
        saves = []

    base_logo = [
        "",
        "    ___ _         _   ___",
        "   | _ (_)_ _____| | |   \\ _  _ _ _  __ _ ___ ___ _ _",
        "   |  _/ \\ \\ / -_) | | |) | || | ' \\/ _` / -_) _ \\ ' \\",
        "   |_| |_/_/_\\___|_| |___/ \\_,_|_||_\\__, \\___\\___/_||_|",
        "                                      |___/",
        "",
        "                    P I X E L   D U N G E O N",
        "                         像素地牢 v{}",
        "",
    ]

    glitch_chars = ["▓", "▒", "░", "█", "▀", "▄"]
    pulse = (frame % 20) / 20.0
    glitch_prob = 0.15 if 5 < frame % 20 < 15 else 0.02

    logo_text = Text()
    version = get_version()
    for raw_line in base_logo:
        line = raw_line.format(version)
        for ch in line:
            if ch == " ":
                logo_text.append(" ")
            elif random.random() < glitch_prob:
                gch = random.choice(glitch_chars)
                logo_text.append(gch, style=get_style("dim cyan"))
            elif random.random() < 0.05:
                logo_text.append(ch, style=get_style("dim"))
            else:
                style = "bright_cyan" if pulse > 0.3 else "cyan"
                logo_text.append(ch, style=style)
        logo_text.append("\n")

    if update_info and update_info.get("available"):
        version = update_info.get("version", "")
        notice = f"🎉 {_('update_available', version)}! {_('press_u_to_update')}"
        pad = max(0, 60 - len(notice)) // 2
        logo_text.append(" " * pad + notice + "\n", style=get_style("bold yellow"))

    features = [
        (
            "♛",
            "bright_green",
            _("hero"),
            f"4{_('characters')} {_('hero')}·{_('mage')}·{_('assassin')}·{_('paladin')}",
        ),
        (
            "✦",
            "bright_red",
            "5" + _("enemies"),
            f"{_('slime')}·{_('goblin')}·{_('skeleton')}·{_('orc')}·{_('shadow')}",
        ),
        ("⌂", "bright_cyan", _("infinite_dungeon"), _("roguelike_progression")),
        ("★", "bright_magenta", _("upgrade_system"), "12" + _("abilities_free_build")),
        ("🛡", "bright_yellow", _("shop_system"), _("buy_items_strengthen")),
    ]

    left_content = Text()
    left_content.append(_glitch_text(_("game_features"), frame, "bold yellow", 0.15))
    left_content.append("\n\n", style="")
    for icon, color, title, desc in features:
        left_content.append(f"{icon} ", style=color)
        left_content.append(f"{title}", style="bold")
        left_content.append(f"\n   {desc}\n", style=get_style("dim"))

    menu_content = Text()
    menu_content.append(_glitch_text(_("main_menu"), frame, "bold cyan underline"))
    menu_content.append("\n" + "─" * 16 + "\n", style=get_style("dim"))
    for i, (label, action, enabled) in enumerate(menu_items):
        is_selected = i == menu_index
        prefix = ">>> " if is_selected else "     "
        name_style = (
            f"bold yellow on dark_green"
            if is_selected
            else ("dim" if not enabled else "bold")
        )
        desc_style = "white" if is_selected else ("dim" if not enabled else "dim")
        menu_content.append(f"{prefix}", style=name_style)
        menu_content.append(
            f"{label}\n", style=name_style if is_selected else desc_style
        )

    saves_content = Text()
    saves_content.append(_glitch_text(_("save_slots"), frame, "bold cyan underline"))
    saves_content.append("\n" + "─" * 12 + "\n", style=get_style("dim"))
    for save in saves:
        slot = save.get("slot", 0)
        num = slot + 1
        if save.get("empty"):
            saves_content.append(f" [{num}] ", style=get_style("dim"))
            saves_content.append(f"{_('empty_slot')}\n", style=get_style("dim"))
        elif save.get("error"):
            saves_content.append(f" [{num}] ", style=get_style("red"))
            saves_content.append(f"{_('load_failed')}\n", style=get_style("red"))
        else:
            floor = save.get("floor", 1)
            ts = save.get("timestamp", _("unknown"))
            if len(ts) > 10:
                ts = ts[:10]
            saves_content.append(f" [{num}] ", style=get_style("bold cyan"))
            saves_content.append(f"{_('floor')} {floor}\n", style=get_style("white"))
            saves_content.append(f"      {ts}\n", style=get_style("dim"))

    logo_lines = logo_text.plain.count("\n") + 1
    logo_panel = Panel(
        Align.center(logo_text),
        border_style=get_style("cyan"),
        box=box.DOUBLE if frame % 2 == 0 else box.ROUNDED,
        height=logo_lines + 2,
    )

    left_panel = Panel(
        Align.center(left_content, vertical="middle"),
        border_style=get_style("yellow"),
        box=box.ROUNDED,
        title="[yellow]✨ " + _("game_features") + "[/yellow]",
    )
    menu_panel = Panel(
        Align.center(menu_content, vertical="middle"),
        border_style=get_style("green"),
        box=box.ROUNDED if menu_index != 0 else box.DOUBLE,
        title="[green]🎮 " + _("main_menu") + "[/green]",
        width=28,
    )
    saves_panel = Panel(
        saves_content,
        border_style=get_style("cyan"),
        box=box.ROUNDED,
        title="[cyan]💾 " + _("save_slots") + "[/cyan]",
        width=24,
    )

    info_layout = Layout()
    info_layout.split_row(
        Layout(left_panel, ratio=3),
        Layout(menu_panel, ratio=2),
        Layout(saves_panel, ratio=2),
    )

    info_layout = Layout()
    info_layout.split_row(
        Layout(left_panel, ratio=3),
        Layout(menu_panel, ratio=2),
        Layout(controls_panel, ratio=2),
    )

    content_layout = Layout()
    content_layout.split_column(
        Layout(logo_panel, size=logo_lines + 2),
        Layout(info_layout, ratio=1),
    )

    return content_layout


def create_help_screen(frame: int = 0) -> Layout:
    text = Text()
    text.append(_glitch_text(_("game_help"), frame, "bold green", 0.15))
    text.append("\n\n", style="")
    text.append(_("move_attack") + "\n", style=get_style("white"))
    text.append(_("space_wait") + "\n", style=get_style("white"))
    text.append(_("b_shop") + "\n", style=get_style("white"))
    text.append(_("p_pause") + "\n", style=get_style("white"))
    text.append(_("s_save") + "\n", style=get_style("white"))
    text.append(_("r_restart") + "\n", style=get_style("white"))
    text.append(_("m_menu") + "\n", style=get_style("white"))
    text.append(_("cmd_mode") + "\n", style=get_style("white"))
    text.append(_("q_show_help") + "\n", style=get_style("white"))
    text.append(_("q_quit") + "\n", style=get_style("white"))
    text.append("\n" + _("return_menu_any"), style=get_style("dim"))

    pulse_box = box.DOUBLE if frame % 20 < 10 else box.ROUNDED
    border = "bright_green" if frame % 24 < 12 else "green"

    panel = Panel(
        Align.center(text, vertical="middle"),
        title="[bold green]" + _("help") + "[/bold green]",
        border_style=border,
        box=pulse_box,
        width=50,
        height=16,
    )

    layout = Layout()
    layout.split_column(
        Layout(Text(" "), ratio=1),
        Layout(Align.center(panel, vertical="middle"), size=16),
        Layout(Text(" "), ratio=1),
    )
    return layout


def create_about_screen(frame: int = 0, extra_msg: str = "") -> Layout:
    text = Text()
    text.append(_glitch_text(_("about_pixel_dungeon"), frame, "bold cyan", 0.15))
    text.append("\n\n", style="")
    text.append(_("version") + ": v1.1.0\n", style=get_style("white"))
    text.append(_("author") + ": muselinn & opencode\n", style=get_style("white"))
    text.append(_("github_repo") + "\n", style=get_style("dim cyan"))
    text.append(_("engine") + ": Python + Rich TUI\n", style=get_style("white"))
    if extra_msg:
        text.append(f"\n{extra_msg}\n", style=get_style("bright_yellow"))
    text.append("\n" + _("thanks") + "\n", style=get_style("bright_yellow"))
    text.append("\n" + _("u_check_update"), style=get_style("dim"))

    pulse_box = box.DOUBLE if frame % 20 < 10 else box.ROUNDED
    border = "bright_cyan" if frame % 24 < 12 else "cyan"

    panel = Panel(
        Align.center(text, vertical="middle"),
        title=f"[bold {border}]" + _("about") + f"[/bold {border}]",
        border_style=border,
        box=pulse_box,
        width=46,
        height=15 if extra_msg else 13,
    )

    layout = Layout()
    layout.split_column(
        Layout(Text(" "), ratio=1),
        Layout(Align.center(panel, vertical="middle"), size=(15 if extra_msg else 13)),
        Layout(Text(" "), ratio=1),
    )
    return layout


def create_achievements_screen(frame: int = 0) -> Layout:
    mgr = AchievementManager()
    unlocked, total = mgr.get_unlocked_count()

    text = Text()
    text.append(_glitch_text(_("achievements"), frame, "bold yellow", 0.15))
    text.append("\n\n", style="")

    for ach in mgr.ACHIEVEMENTS:
        is_unlocked = ach.id in mgr.unlocked
        if ach.secret and not is_unlocked:
            display_name = "???"
            display_desc = _("hidden_achievement")
            icon = "❓"
        else:
            display_name = ach.name
            display_desc = ach.description
            icon = ach.icon

        status_icon = "✅" if is_unlocked else "⬜"
        tier_name = str(ach.tier.name)
        text.append(f"{status_icon} {icon} ", style=ach.get_tier_style())
        text.append(f"{display_name}\n", style="bold" if is_unlocked else "dim")
        text.append(f"    {display_desc}\n", style="dim")

    text.append(f"\n{_('achievements_unlocked', unlocked, total)}", style="yellow")
    text.append(f"\n{_('return_menu_any')}", style="dim")

    panel = Panel(
        Align.center(text, vertical="middle"),
        title=f"[bold yellow]{_('achievements')}[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED if frame % 20 < 10 else box.DOUBLE,
        width=60,
        height=26,
    )

    layout = Layout()
    layout.split_column(
        Layout(Text(" "), ratio=1),
        Layout(Align.center(panel, vertical="middle"), size=26),
        Layout(Text(" "), ratio=1),
    )
    return layout


def show_help(live_or_input, frame: int = 0) -> None:
    if hasattr(live_or_input, "update"):
        live_or_input.update(create_help_screen(frame))
        time.sleep(0.1)
    else:
        with Live(screen=True, refresh_per_second=10) as live:
            live.update(create_help_screen(frame))
            while True:
                key = live_or_input.get_key()
                if key:
                    break
                time.sleep(0.05)


def create_settings_screen(frame: int = 0, selected_index: int = 0) -> Layout:
    fps_options = [15, 30, 60]
    fps_index = fps_options.index(CONFIG.fps) if CONFIG.fps in fps_options else 1
    diff_labels = {
        "easy": _("easy"),
        "normal": _("normal"),
        "hard": _("hard"),
    }
    lang_labels = {"zh_CN": "中文", "en_US": "English"}

    theme_labels = {"dark": _("dark"), "light": _("light")}

    items = [
        (
            _("fps"),
            " ".join(
                [
                    f"[{v}]" if i == fps_index else f" {v} "
                    for i, v in enumerate(fps_options)
                ]
            ),
        ),
        (
            _("lighting"),
            "[" + _("on") + "]" if CONFIG.lighting else "[" + _("off") + "]",
        ),
        (
            _("particles"),
            "[" + _("on") + "]" if CONFIG.particles else "[" + _("off") + "]",
        ),
        (_("difficulty"), f"[{diff_labels.get(CONFIG.difficulty, CONFIG.difficulty)}]"),
        ("语言", f"[{lang_labels.get(CONFIG.language, CONFIG.language)}]"),
        (_("theme"), f"[{theme_labels.get(CONFIG.theme, CONFIG.theme)}]"),
        (_("return_main_menu"), ""),
    ]

    text = Text()
    text.append(_glitch_text(_("game_settings"), frame, "bold yellow", 0.15))
    text.append("\n\n", style="")
    for i, (label, value) in enumerate(items):
        is_selected = i == selected_index
        prefix = ">>> " if is_selected else "     "
        line_style = "bold yellow on dark_green" if is_selected else "white"
        text.append(f"{prefix}{label}  ", style=line_style)
        text.append(f"{value}\n", style=line_style)

    pulse_box = box.DOUBLE if frame % 20 < 10 else box.ROUNDED
    border = "bright_yellow" if frame % 24 < 12 else "yellow"

    panel = Panel(
        Align.center(text, vertical="middle"),
        title="[bold yellow]" + _("settings") + "[/bold yellow]",
        border_style=border,
        box=pulse_box,
        width=42,
        height=17,
    )

    layout = Layout()
    layout.split_column(
        Layout(Text(" "), ratio=1),
        Layout(Align.center(panel, vertical="middle"), size=17),
        Layout(Text(" "), ratio=1),
    )
    return layout


def show_title_screen() -> tuple:
    input_handler = CrossPlatformInputHandler()
    input_handler.start()

    save_manager = SaveManager()
    saves = save_manager.list_saves()
    has_save = any(not s.get("empty") and not s.get("error") for s in saves)

    menu_items = [
        (_("start_game"), "start", True),
        (_("continue_game"), "continue", has_save),
        (_("achievements"), "achievements", True),
        (_("settings"), "settings", True),
        (_("help"), "help", True),
        (_("about"), "about", True),
        (_("quit_game"), "quit", True),
    ]
    menu_index = 0

    char_map = {"1": "default", "2": "mage", "3": "rogue", "4": "paladin"}
    selected_char = "default"

    fps_options = [15, 30, 60]
    diff_options = ["easy", "normal", "hard"]

    def _cycle_diff(delta: int) -> None:
        cur = (
            diff_options.index(CONFIG.difficulty)
            if CONFIG.difficulty in diff_options
            else 1
        )
        new_i = (cur + delta) % len(diff_options)
        CONFIG.difficulty = diff_options[new_i]
        CONFIG.save_settings()

    update_info = {"available": False, "version": "", "checked": False}

    def _check_update():
        try:
            from ..utils.ota import check_update_available

            available, version = check_update_available()
            update_info["available"] = available
            update_info["version"] = version
        except Exception:
            pass
        update_info["checked"] = True

    import threading

    threading.Thread(target=_check_update, daemon=True).start()

    try:
        with Live(screen=True, refresh_per_second=10) as live:
            frame = 0
            showing_help = False
            showing_settings = False
            showing_about = False
            showing_achievements = False
            settings_index = 0

            while True:
                frame += 1

                if showing_help:
                    live.update(create_help_screen(frame))
                    key = input_handler.get_key()
                    if key:
                        showing_help = False
                    time.sleep(0.05)
                    continue

                if showing_about:
                    live.update(create_about_screen(frame))
                    key = input_handler.get_key()
                    if key:
                        if key.lower() == "u":
                            from ..utils.ota import check_and_update

                            ok, msg = check_and_update()
                            live.update(create_about_screen(frame, extra_msg=msg))
                            time.sleep(1.5)
                        else:
                            showing_about = False
                    time.sleep(0.05)
                    continue

                if showing_achievements:
                    live.update(create_achievements_screen(frame))
                    key = input_handler.get_key()
                    if key:
                        showing_achievements = False
                    time.sleep(0.05)
                    continue

                if showing_settings:
                    live.update(create_settings_screen(frame, settings_index))
                    key = input_handler.get_key()
                    if key:
                        if key == "UP" or key == "w" or key == "W":
                            settings_index = max(0, settings_index - 1)
                        elif key == "DOWN" or key == "s" or key == "S":
                            settings_index = min(6, settings_index + 1)
                        elif key == "LEFT" or key == "a" or key == "A":
                            if settings_index == 0:
                                cur = (
                                    fps_options.index(CONFIG.fps)
                                    if CONFIG.fps in fps_options
                                    else 1
                                )
                                new_i = max(0, cur - 1)
                                CONFIG.set_fps(fps_options[new_i])
                            elif settings_index == 1:
                                CONFIG.lighting = not CONFIG.lighting
                            elif settings_index == 2:
                                CONFIG.particles = not CONFIG.particles
                            elif settings_index == 3:
                                _cycle_diff(-1)
                            elif settings_index == 4:
                                lang_options = ["zh_CN", "en_US"]
                                cur = (
                                    lang_options.index(CONFIG.language)
                                    if CONFIG.language in lang_options
                                    else 0
                                )
                                new_i = max(0, cur - 1)
                                CONFIG.language = lang_options[new_i]
                                from ..utils.i18n import set_language

                                set_language(CONFIG.language)
                            elif settings_index == 5:
                                theme_options = ["dark", "light"]
                                cur = (
                                    theme_options.index(CONFIG.theme)
                                    if CONFIG.theme in theme_options
                                    else 0
                                )
                                new_i = max(0, cur - 1)
                                CONFIG.theme = theme_options[new_i]
                            CONFIG.save_settings()
                        elif key == "RIGHT" or key == "d" or key == "D":
                            if settings_index == 0:
                                cur = (
                                    fps_options.index(CONFIG.fps)
                                    if CONFIG.fps in fps_options
                                    else 1
                                )
                                new_i = min(len(fps_options) - 1, cur + 1)
                                CONFIG.set_fps(fps_options[new_i])
                            elif settings_index == 1:
                                CONFIG.lighting = not CONFIG.lighting
                            elif settings_index == 2:
                                CONFIG.particles = not CONFIG.particles
                            elif settings_index == 3:
                                _cycle_diff(1)
                            elif settings_index == 4:
                                lang_options = ["zh_CN", "en_US"]
                                cur = (
                                    lang_options.index(CONFIG.language)
                                    if CONFIG.language in lang_options
                                    else 0
                                )
                                new_i = min(len(lang_options) - 1, cur + 1)
                                CONFIG.language = lang_options[new_i]
                                from ..utils.i18n import set_language

                                set_language(CONFIG.language)
                            elif settings_index == 5:
                                theme_options = ["dark", "light"]
                                cur = (
                                    theme_options.index(CONFIG.theme)
                                    if CONFIG.theme in theme_options
                                    else 0
                                )
                                new_i = min(len(theme_options) - 1, cur + 1)
                                CONFIG.theme = theme_options[new_i]
                            CONFIG.save_settings()
                        elif key == "\r" or key == "\n":
                            if settings_index == 0:
                                cur = (
                                    fps_options.index(CONFIG.fps)
                                    if CONFIG.fps in fps_options
                                    else 1
                                )
                                CONFIG.set_fps(
                                    fps_options[(cur + 1) % len(fps_options)]
                                )
                                CONFIG.save_settings()
                            elif settings_index == 1:
                                CONFIG.lighting = not CONFIG.lighting
                                CONFIG.save_settings()
                            elif settings_index == 2:
                                CONFIG.particles = not CONFIG.particles
                                CONFIG.save_settings()
                            elif settings_index == 3:
                                _cycle_diff(1)
                                CONFIG.save_settings()
                            elif settings_index == 4:
                                lang_options = ["zh_CN", "en_US"]
                                cur = (
                                    lang_options.index(CONFIG.language)
                                    if CONFIG.language in lang_options
                                    else 0
                                )
                                new_i = (cur + 1) % len(lang_options)
                                CONFIG.language = lang_options[new_i]
                                from ..utils.i18n import set_language

                                set_language(CONFIG.language)
                                CONFIG.save_settings()
                            elif settings_index == 5:
                                theme_options = ["dark", "light"]
                                cur = (
                                    theme_options.index(CONFIG.theme)
                                    if CONFIG.theme in theme_options
                                    else 0
                                )
                                new_i = (cur + 1) % len(theme_options)
                                CONFIG.theme = theme_options[new_i]
                                CONFIG.save_settings()
                            elif settings_index == 6:
                                showing_settings = False
                        elif key == "\x1b" or key.lower() == "q":
                            showing_settings = False
                    time.sleep(0.05)
                    continue

                layout = create_modern_title(
                    frame, menu_index, menu_items, saves, update_info
                )
                live.update(layout)

                key = input_handler.get_key()
                if key:
                    if key in char_map:
                        selected_char = char_map[key]
                    elif key.lower() == "u":
                        from ..utils.ota import check_and_update

                        ok, msg = check_and_update()
                        update_info["available"] = False
                        live.update(
                            create_modern_title(
                                frame,
                                menu_index,
                                menu_items,
                                saves,
                                {"available": False},
                            )
                        )
                        time.sleep(0.3)
                        live.update(create_about_screen(frame, extra_msg=msg))
                        time.sleep(1.5)
                    elif key in ("1", "2", "3"):
                        slot_idx = int(key) - 1
                        if slot_idx < len(saves) and not saves[slot_idx].get("empty"):
                            for f in range(24):
                                live.update(
                                    create_matrix_transition_layout(
                                        frame=f, console=live.console
                                    )
                                )
                                time.sleep(0.04)
                            return ("continue", selected_char, slot_idx)
                    elif key == "UP" or key == "w" or key == "W":
                        new_index = menu_index - 1
                        while new_index >= 0:
                            if menu_items[new_index][2]:
                                menu_index = new_index
                                break
                            new_index -= 1
                    elif key == "DOWN" or key == "s" or key == "S":
                        new_index = menu_index + 1
                        while new_index < len(menu_items):
                            if menu_items[new_index][2]:
                                menu_index = new_index
                                break
                            new_index += 1
                    elif key == "\r" or key == "\n":
                        action = menu_items[menu_index][1]
                        if action == "help":
                            showing_help = True
                        elif action == "about":
                            showing_about = True
                        elif action == "achievements":
                            showing_achievements = True
                        elif action == "settings":
                            showing_settings = True
                            settings_index = 0
                        elif action == "start":
                            for f in range(24):
                                live.update(
                                    create_matrix_transition_layout(
                                        frame=f,
                                        console=live.console,
                                    )
                                )
                                time.sleep(0.04)
                            return (action, selected_char, 0)
                        elif action == "continue":
                            for f in range(24):
                                live.update(
                                    create_matrix_transition_layout(
                                        frame=f,
                                        console=live.console,
                                    )
                                )
                                time.sleep(0.04)
                            first_slot = 0
                            for s in saves:
                                if not s.get("empty") and not s.get("error"):
                                    first_slot = s.get("slot", 0)
                                    break
                            return (action, selected_char, first_slot)
                        else:
                            return (action, selected_char, 0)
                    elif key == "\x03" or key.lower() == "q":
                        return ("quit", selected_char, 0)

                time.sleep(0.05)
    except KeyboardInterrupt:
        return ("quit", selected_char, 0)
    finally:
        input_handler.stop()
