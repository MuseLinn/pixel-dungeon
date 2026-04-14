#!/usr/bin/env python3
"""Pixel Dungeon 主入口"""

import sys
import argparse

from .config import CONFIG
from .core.game import Game
from .ui.screens import show_title_screen
from .utils.i18n import set_language, _


def parse_args():
    parser = argparse.ArgumentParser(description=_("cli_desc"))
    parser.add_argument("--fps", type=int, default=30, help=_("arg_fps"))
    parser.add_argument("--no-light", action="store_true", help=_("arg_no_light"))
    parser.add_argument("--no-particle", action="store_true", help=_("arg_no_particle"))
    parser.add_argument(
        "--char",
        type=str,
        default="default",
        choices=["default", "mage", "rogue", "paladin"],
        help=_("arg_char"),
    )
    parser.add_argument("--skip-title", action="store_true", help=_("arg_skip_title"))
    parser.add_argument("--update", action="store_true", help=_("arg_update"))
    parser.add_argument("--uninstall", action="store_true", help=_("arg_uninstall"))
    parser.add_argument("--version", action="store_true", help=_("arg_version"))

    return parser.parse_args()


def main():
    CONFIG.load_settings()
    set_language(CONFIG.language)

    args = parse_args()

    if args.version:
        from .utils.ota import get_version

        print(f"Pixel Dungeon {get_version()}")
        return

    if args.uninstall:
        from .utils.ota import uninstall

        ok, msg = uninstall()
        print(msg)
        if ok:
            print(f"==> {_('uninstall_complete')}")
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
            print(_("quit_msg"))
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
