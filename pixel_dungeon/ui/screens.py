#!/usr/bin/env python3
"""启动画面和覆盖层 UI"""

import time

from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
from rich.live import Live

from ..input_handler import CrossPlatformInputHandler
from ..utils.save_load import SaveManager
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


def create_menu_transition_layout(frame: int, console, direction: str = "in") -> Layout:
    import random
    import math

    total_w = console.width
    total_h = console.height
    cx = total_w // 2
    cy = total_h // 2
    max_dist = math.sqrt(cx**2 + cy**2) + 2
    progress = frame / 15.0

    lines = []
    for y in range(total_h):
        line = Text()
        for x in range(total_w):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if direction == "in":
                show_glitch = dist > progress * max_dist
            else:
                show_glitch = dist < (1.0 - progress) * max_dist
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
                line.append(
                    gch, style=random.choice(["dim cyan", "dim blue", "dim magenta"])
                )
            else:
                line.append(" ", style="black")
        lines.append(line)

    full_text = Text("\n").join(lines)
    layout = Layout(full_text)
    return layout


def create_modern_title(
    frame: int = 0, menu_index: int = 0, has_save: bool = False
) -> Layout:
    import random

    base_logo = [
        "",
        "    ___ _         _   ___",
        "   | _ (_)_ _____| | |   \\ _  _ _ _  __ _ ___ ___ _ _",
        "   |  _/ \\ \\ / -_) | | |) | || | ' \\/ _` / -_) _ \\ ' \\",
        "   |_| |_/_/_\\___|_| |___/ \\_,_|_||_\\__, \\___\\___/_||_|",
        "                                      |___/",
        "",
        "                    P I X E L   D U N G E O N",
        "                         像素地牢 v1.0",
        "",
    ]

    glitch_chars = ["▓", "▒", "░", "█", "▀", "▄"]
    pulse = (frame % 20) / 20.0
    glitch_prob = 0.15 if 5 < frame % 20 < 15 else 0.02

    logo_text = Text()
    for line in base_logo:
        for ch in line:
            if ch == " ":
                logo_text.append(" ")
            elif random.random() < glitch_prob:
                gch = random.choice(glitch_chars)
                logo_text.append(gch, style="dim cyan")
            elif random.random() < 0.05:
                logo_text.append(ch, style="dim")
            else:
                style = "bright_cyan" if pulse > 0.3 else "cyan"
                logo_text.append(ch, style=style)
        logo_text.append("\n")

    features = [
        ("♛", "bright_green", "4种角色", "勇者·法师·刺客·圣骑"),
        ("✦", "bright_red", "5种敌人", "史莱姆·哥布林·骷髅·兽人·暗影"),
        ("⌂", "bright_cyan", "无限地牢", "层层递进的Roguelike体验"),
        ("★", "bright_magenta", "升级系统", "12种能力自由搭配"),
        ("🛡", "bright_yellow", "商店系统", "购买道具强化角色"),
    ]

    left_content = Text()
    left_content.append("游戏特色\n", style="bold yellow underline")
    left_content.append("─" * 20 + "\n", style="dim")
    for icon, color, title, desc in features:
        left_content.append(f"{icon} ", style=color)
        left_content.append(f"{title}", style="bold")
        left_content.append(f"\n   {desc}\n", style="dim")

    menu_items = [
        ("开始游戏", "start", True),
        ("继续游戏", "continue", has_save),
        ("游戏帮助", "help", True),
        ("退出游戏", "quit", True),
    ]

    menu_content = Text()
    menu_content.append("主菜单\n", style="bold cyan underline")
    menu_content.append("─" * 16 + "\n", style="dim")
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

    controls = [
        ("WASD/↑↓", "选择"),
        ("Enter", "确认"),
        ("Q", "退出"),
    ]

    controls_content = Text()
    controls_content.append("操作\n", style="bold cyan underline")
    controls_content.append("─" * 12 + "\n", style="dim")
    for key, action in controls:
        controls_content.append(f"{key:>8}", style="bold white on dark_blue")
        controls_content.append(f"  {action}\n", style="white")

    logo_panel = Panel(
        Align.center(logo_text),
        border_style="cyan",
        box=box.DOUBLE if frame % 2 == 0 else box.ROUNDED,
        height=len(base_logo) + 2,
    )

    panel_height = 16
    left_panel = Panel(
        left_content,
        border_style="yellow",
        box=box.ROUNDED,
        title="[yellow]✨ 特色[/yellow]",
        height=panel_height,
    )
    menu_panel = Panel(
        menu_content,
        border_style="green",
        box=box.ROUNDED if menu_index != 0 else box.DOUBLE,
        title="[green]🎮 菜单[/green]",
        width=28,
        height=panel_height,
    )
    controls_panel = Panel(
        controls_content,
        border_style="cyan",
        box=box.ROUNDED,
        title="[cyan]⌨ 操作[/cyan]",
        width=24,
        height=panel_height,
    )

    info_layout = Layout()
    info_layout.split_row(
        Layout(left_panel, ratio=3),
        Layout(menu_panel, ratio=2),
        Layout(controls_panel, ratio=2),
    )

    content_layout = Layout()
    content_layout.split_column(
        Layout(logo_panel, size=len(base_logo) + 2),
        Layout(info_layout, size=panel_height),
    )

    total_content_h = len(base_logo) + 2 + panel_height

    main_layout = Layout()
    main_layout.split_column(
        Layout(ratio=1),
        Layout(content_layout, size=total_content_h),
        Layout(ratio=1),
    )

    return main_layout


def create_help_screen() -> Layout:
    text = Text()
    text.append("游戏帮助\n\n", style="bold yellow")
    text.append("WASD / 方向键  移动和攻击\n", style="white")
    text.append("空格           等待一回合，恢复生命\n", style="white")
    text.append("B              打开商店\n", style="white")
    text.append("P              暂停/继续游戏\n", style="white")
    text.append("S              保存游戏\n", style="white")
    text.append("R              重新开始\n", style="white")
    text.append("M              返回主菜单\n", style="white")
    text.append("/ 或 Ctrl+X    命令模式\n", style="white")
    text.append("?              显示帮助\n", style="white")
    text.append("Q              退出游戏\n", style="white")
    text.append("\n按任意键返回主菜单...", style="dim")

    panel = Panel(
        Align.center(text, vertical="middle"),
        title="[bold yellow]帮助[/bold yellow]",
        border_style="yellow",
        box=box.ROUNDED,
        width=50,
        height=16,
    )

    layout = Layout()
    layout.split_column(
        Layout(size=1),
        Layout(Align.center(panel, vertical="middle"), size=16),
        Layout(size=1),
    )
    return layout


def show_help(live_or_input) -> None:
    if hasattr(live_or_input, "update"):
        live_or_input.update(create_help_screen())
        time.sleep(0.1)
    else:
        with Live(screen=True, refresh_per_second=10) as live:
            live.update(create_help_screen())
            while True:
                key = live_or_input.get_key()
                if key:
                    break
                time.sleep(0.05)


def create_settings_screen(frame: int = 0, selected_index: int = 0) -> Layout:
    fps_options = [15, 30, 60]
    fps_index = fps_options.index(CONFIG.fps) if CONFIG.fps in fps_options else 1

    items = [
        (
            "帧率",
            " ".join(
                [
                    f"[{v}]" if i == fps_index else f" {v} "
                    for i, v in enumerate(fps_options)
                ]
            ),
        ),
        ("光照效果", "[开]" if CONFIG.lighting else "[关]"),
        ("粒子效果", "[开]" if CONFIG.particles else "[关]"),
        ("返回主菜单", ""),
    ]

    text = Text()
    text.append(_glitch_text("游戏设置", frame, "bold yellow", 0.15))
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
        title="[bold yellow]设置[/bold yellow]",
        border_style=border,
        box=pulse_box,
        width=42,
        height=14,
    )

    layout = Layout()
    layout.split_column(
        Layout(ratio=1),
        Layout(Align.center(panel, vertical="middle"), size=14),
        Layout(ratio=1),
    )
    return layout


def show_title_screen() -> tuple:
    input_handler = CrossPlatformInputHandler()
    input_handler.start()

    save_manager = SaveManager()
    has_save = save_manager.exists(0)

    menu_items = [
        ("开始游戏", "start", True),
        ("继续游戏", "continue", has_save),
        ("游戏设置", "settings", True),
        ("游戏帮助", "help", True),
        ("退出游戏", "quit", True),
    ]
    menu_index = 0

    char_map = {"1": "default", "2": "mage", "3": "rogue", "4": "paladin"}
    selected_char = "default"

    fps_options = [15, 30, 60]

    try:
        with Live(screen=True, refresh_per_second=10) as live:
            frame = 0
            showing_help = False
            showing_settings = False
            settings_index = 0

            while True:
                frame += 1

                if showing_help:
                    live.update(create_help_screen())
                    key = input_handler.get_key()
                    if key:
                        showing_help = False
                    time.sleep(0.05)
                    continue

                if showing_settings:
                    live.update(create_settings_screen(frame, settings_index))
                    key = input_handler.get_key()
                    if key:
                        if key == "UP" or key == "w" or key == "W":
                            settings_index = max(0, settings_index - 1)
                        elif key == "DOWN" or key == "s" or key == "S":
                            settings_index = min(3, settings_index + 1)
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
                                showing_settings = False
                        elif key == "\x1b" or key.lower() == "q":
                            showing_settings = False
                    time.sleep(0.05)
                    continue

                layout = create_modern_title(frame, menu_index, has_save)
                live.update(layout)

                key = input_handler.get_key()
                if key:
                    if key in char_map:
                        selected_char = char_map[key]
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
                        elif action == "settings":
                            showing_settings = True
                            settings_index = 0
                        elif action in ("start", "continue"):
                            for f in range(15):
                                live.update(
                                    create_menu_transition_layout(
                                        frame=f,
                                        console=live.console,
                                        direction="in",
                                    )
                                )
                                time.sleep(0.04)
                            return (action, selected_char)
                        else:
                            return (action, selected_char)
                    elif key == "\x03" or key.lower() == "q":
                        return ("quit", selected_char)

                time.sleep(0.05)
    except KeyboardInterrupt:
        return ("quit", selected_char)
    finally:
        input_handler.stop()
