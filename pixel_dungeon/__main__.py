#!/usr/bin/env python3
"""Pixel Dungeon 主入口"""

import sys
import argparse

from .config import CONFIG
from .core.game import Game
from .ui.screens import show_title_screen


def parse_args():
    parser = argparse.ArgumentParser(description="Pixel Dungeon - 像素地牢")
    parser.add_argument("--fps", type=int, default=30, help="设置帧率 (10-60，默认 30)")
    parser.add_argument("--no-light", action="store_true", help="关闭光照效果")
    parser.add_argument("--no-particle", action="store_true", help="关闭粒子效果")
    parser.add_argument(
        "--char",
        type=str,
        default="default",
        choices=["default", "mage", "rogue", "paladin"],
        help="选择角色 (default/mage/rogue/paladin)",
    )
    parser.add_argument(
        "--skip-title", action="store_true", help="跳过标题画面（直接开始）"
    )
    parser.add_argument("--update", action="store_true", help="检查并更新到最新版本")
    parser.add_argument("--uninstall", action="store_true", help="卸载游戏")
    parser.add_argument("--version", action="store_true", help="显示版本号")

    return parser.parse_args()


def main():
    CONFIG.load_settings()

    args = parse_args()

    if args.version:
        from .utils.ota import get_version

        print(f"Pixel Dungeon {get_version()}")
        return

    if args.uninstall:
        import platform

        if platform.system() == "Windows":
            print("请在 PowerShell 中运行:")
            print(
                "  iwr -useb https://raw.githubusercontent.com/muselinn/pixel-dungeon/master/uninstall.ps1 | iex"
            )
        else:
            print("请在终端中运行:")
            print(
                "  curl -sSL https://raw.githubusercontent.com/muselinn/pixel-dungeon/master/uninstall.sh | bash"
            )
        return

    if args.update:
        from .utils.ota import check_and_update

        ok, msg = check_and_update()
        print(msg)
        return

    if args.fps:
        CONFIG.set_fps(args.fps)
    if args.no_light:
        CONFIG.lighting = False
    if args.no_particle:
        CONFIG.particles = False

    selected_char = args.char

    if args.skip_title:
        game = Game()
        game.init_game(char_set=selected_char)
        game.run()
        return

    while True:
        action, selected_char = show_title_screen()

        if action == "quit":
            print("已退出游戏")
            break

        if action == "start":
            game = Game()
            game.init_game(char_set=selected_char)
            game.run()
            if not game.return_to_menu:
                break

        elif action == "continue":
            game = Game()
            game.init_game(char_set=selected_char)
            if game.load_game(0):
                px, py = game.player.x, game.player.y
                game.init_map()
                game.player.x, game.player.y = px, py
                game.update_explored()
                game.run()
            else:
                game.run()
            if not game.return_to_menu:
                break


if __name__ == "__main__":
    main()
