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


def create_modern_title(frame: int = 0, selected_char: str = "default") -> Layout:
    import random
    from ..assets import GAME_ASSETS, CHARACTERS

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

    controls = [
        ("WASD", "移动攻击"),
        ("空格", "等待恢复"),
        ("1-3", "选择升级"),
        ("B", "打开商店"),
        ("P", "暂停游戏"),
        ("/", "命令模式"),
        ("?", "帮助面板"),
    ]

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

    char_content = Text()
    char_content.append("选择角色 ", style="bold")
    char_content.append("(按数字切换)\n\n", style="dim")
    chars_preview = [
        ("1", "▓████▓", "bright_green", "勇者", "平衡型", "default"),
        ("2", "▓▓▓▓▓▓", "bright_cyan", "法师", "高攻低防", "mage"),
        ("3", "▒▒▒▒▒▒", "bright_red", "刺客", "暴击型", "rogue"),
        ("4", "▓████▓", "bright_yellow", "圣骑", "坦克型", "paladin"),
    ]
    for num, icon, color, name, desc, char_key in chars_preview:
        is_selected = char_key == selected_char
        prefix = ">>> " if is_selected else "    "
        num_style = f"bold yellow on dark_green" if is_selected else "dim"
        name_style = f"bold yellow" if is_selected else "bold"
        desc_style = "white" if is_selected else "dim"
        char_content.append(f"{prefix}[{num}] ", style=num_style)
        char_content.append(f"{icon}", style=f"bold {color}")
        char_content.append(f" {name:6}", style=name_style)
        char_content.append(f" {desc}\n", style=desc_style)

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
        title="[yellow]✨ 特色[/]",
        height=panel_height,
    )
    right_panel = Panel(
        right_content,
        border_style="cyan",
        box=box.ROUNDED,
        title="[cyan]⌨ 操作[/]",
        height=panel_height,
    )
    char_panel = Panel(
        char_content,
        border_style="green",
        box=box.ROUNDED,
        title="[green]🎭 角色[/]",
        width=30,
        height=panel_height,
    )

    footer = Text()
    footer.append("\n  按 ", style="dim")
    footer.append("任意键", style="bold yellow")
    footer.append(" 开始游戏  ·  ", style="dim")
    footer.append("?", style="dim cyan")
    footer.append(" 查看帮助", style="dim")

    info_layout = Layout()
    info_layout.split_row(
        Layout(left_panel, ratio=2),
        Layout(right_panel, ratio=2),
        Layout(char_panel, ratio=1),
    )

    content_layout = Layout()
    content_layout.split_column(
        Layout(logo_panel, size=len(base_logo) + 2),
        Layout(info_layout, size=panel_height),
    )

    main_layout = Layout()
    main_layout.split_column(
        Layout(content_layout),
        Layout(footer, size=2),
    )

    return main_layout


def show_title_screen() -> tuple:
    input_handler = CrossPlatformInputHandler()
    input_handler.start()
    should_exit = False
    selected_char = "default"
    char_map = {"1": "default", "2": "mage", "3": "rogue", "4": "paladin"}

    try:
        with Live(screen=True, refresh_per_second=10) as live:
            frame = 0
            while True:
                frame += 1
                layout = create_modern_title(frame, selected_char)
                live.update(layout)

                key = input_handler.get_key()
                if key:
                    if key in char_map:
                        selected_char = char_map[key]
                    elif key == "\x03" or key.lower() == "q":
                        should_exit = True
                        break
                    else:
                        break

                time.sleep(0.05)
    except KeyboardInterrupt:
        should_exit = True
    finally:
        input_handler.stop()

    return (not should_exit, selected_char)
