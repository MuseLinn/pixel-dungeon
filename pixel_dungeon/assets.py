#!/usr/bin/env python3

from enum import Enum, auto


class TileType(Enum):
    EMPTY = auto()
    WALL = auto()
    EXIT = auto()
    POTION = auto()
    GOLD = auto()


GAME_ASSETS = {
    "player_default": {
        "sprite": [
            " ▄██▄ ",
            " █▄▄█ ",
            "▀█  █▀",
        ],
        "alt_sprite": [
            " ▄██▄ ",
            " █  █ ",
            "▀█  █▀",
        ],
        "name": "勇者",
        "style": "bright_green",
        "style_alt": "green",
        "hp": 100,
        "atk": 10,
        "defense": 0,
        "crit": 0,
        "lifesteal": 0,
        "regen": 0,
    },
    "player_mage": {
        "sprite": [
            " ▲▲▲▲ ",
            " █▄▄█ ",
            " █  █ ",
        ],
        "alt_sprite": [
            " ▲  ▲ ",
            " █▄▄█ ",
            " █  █ ",
        ],
        "name": "法师",
        "style": "bright_cyan",
        "style_alt": "cyan",
        "hp": 80,
        "atk": 15,
        "defense": 0,
        "crit": 10,
        "lifesteal": 0,
        "regen": 1,
    },
    "player_rogue": {
        "sprite": [
            " ▼▼▼▼ ",
            " █▄▄█ ",
            "▀█  █▀",
        ],
        "alt_sprite": [
            " ▼  ▼ ",
            " █▄▄█ ",
            "▀█  █▀",
        ],
        "name": "刺客",
        "style": "bright_red",
        "style_alt": "red",
        "hp": 85,
        "atk": 12,
        "defense": 0,
        "crit": 20,
        "lifesteal": 5,
        "regen": 0,
    },
    "player_paladin": {
        "sprite": [
            " ▄██▄ ",
            " █╋╋█ ",
            "▀███▀ ",
        ],
        "alt_sprite": [
            " ▄██▄ ",
            " █╋╋█ ",
            "▀███▀ ",
        ],
        "name": "圣骑",
        "style": "bright_yellow",
        "style_alt": "yellow",
        "hp": 130,
        "atk": 8,
        "defense": 2,
        "crit": 0,
        "lifesteal": 0,
        "regen": 1,
    },
    "enemy_slime": {
        "sprite": [
            " ▄▄▄▄ ",
            "░◉◉◉░",
            "▀▒▒▒▀",
        ],
        "alt_sprite": [
            " ░░░░ ",
            "░◉◉◉░",
            "▀▒▒▒▀",
        ],
        "name": "史莱姆",
        "style": "green",
        "style_alt": "bright_green",
    },
    "enemy_goblin": {
        "sprite": [
            "▀▄▄▄▄▀",
            "░◉░░◉░",
            " ▀▀▀▀ ",
        ],
        "alt_sprite": [
            "▀░▄▄░▀",
            "░◉░░◉░",
            " ▀▀▀▀ ",
        ],
        "name": "哥布林",
        "style": "yellow",
        "style_alt": "bright_yellow",
    },
    "enemy_skeleton": {
        "sprite": [
            " ▄▄▄▄ ",
            "░▓░░▓░",
            " ▀▓▓▀ ",
        ],
        "alt_sprite": [
            " ▒▒▒▒ ",
            "░▓░░▓░",
            " ▀▓▓▀ ",
        ],
        "name": "骷髅",
        "style": "white",
        "style_alt": "bright_white",
    },
    "enemy_orc": {
        "sprite": [
            " ▀▀▀▀ ",
            "░▓▓▓▓░",
            "▀░█░▀ ",
        ],
        "alt_sprite": [
            " ▀▀▀▀ ",
            "░▓░▓░▓",
            "▀░█░▀ ",
        ],
        "name": "兽人",
        "style": "red",
        "style_alt": "bright_red",
    },
    "enemy_shadow": {
        "sprite": [
            " ▓░▓░ ",
            "░▓▓▓▓░",
            " ▒▒▒▒ ",
        ],
        "alt_sprite": [
            " ░░▓░ ",
            "░▓░▓░▓",
            " ▒░░░ ",
        ],
        "name": "暗影",
        "style": "magenta",
        "style_alt": "bright_magenta",
    },
    "wall": {
        "sprite": [
            "▓▓░░▓▓",
            "░░▓▓░░",
            "▓▓░░▓▓",
        ],
        "alt_sprite": [
            "░░▓▓░░",
            "▓▓░░▓▓",
            "░░▓▓░░",
        ],
        "name": "墙壁",
        "style": "bright_black",
        "style_alt": "bright_black",
    },
    "floor": {
        "sprite": [
            "  ·  ·",
            " ·  · ",
            "  ·  ·",
        ],
        "alt_sprite": [
            " ·  · ",
            "  ·  ·",
            " ·  · ",
        ],
        "name": "地面",
        "style": "dim white",
        "style_alt": "dim white",
    },
    "potion": {
        "sprite": [
            " ♥♥♥♥ ",
            " ▓▓▓▓ ",
            " ░░░░ ",
        ],
        "alt_sprite": [
            " ♥♥♥♥ ",
            " ░░░░ ",
            "      ",
        ],
        "name": "生命药水",
        "style": "bright_red",
        "style_alt": "red",
    },
    "gold": {
        "sprite": [
            " ◆◆◆◆ ",
            "◆◆◆◆◆◆",
            " ▓▓▓▓ ",
        ],
        "alt_sprite": [
            " ◆◆◆◆ ",
            "▓▓▓▓▓▓",
            " ░░░░ ",
        ],
        "name": "金币",
        "style": "bright_yellow",
        "style_alt": "yellow",
    },
    "exit": {
        "sprite": [
            " ⌂⌂⌂⌂ ",
            "▓▓▓▓▓▓",
            " ░░░░ ",
        ],
        "alt_sprite": [
            " ⌂⌂⌂⌂ ",
            "██████",
            " ▒▒▒▒ ",
        ],
        "name": "出口",
        "style": "bright_cyan",
        "style_alt": "cyan",
    },
}

PIXEL_ASSETS = GAME_ASSETS

CHARACTERS = {
    "default": "player_default",
    "mage": "player_mage",
    "rogue": "player_rogue",
    "paladin": "player_paladin",
}

ENEMY_TYPES = [
    ("enemy_slime", "史莱姆", 15, 5, 10, 5),
    ("enemy_goblin", "哥布林", 25, 8, 15, 8),
    ("enemy_skeleton", "骷髅", 30, 12, 20, 10),
    ("enemy_orc", "兽人", 50, 10, 25, 15),
    ("enemy_shadow", "暗影", 40, 15, 30, 20),
]


def get_player_asset(char_set: str = "default") -> dict:
    asset_key = CHARACTERS.get(char_set, "player_default")
    return GAME_ASSETS.get(asset_key, GAME_ASSETS["player_default"])


def get_enemy_asset(enemy_type: str) -> dict:
    return GAME_ASSETS.get(enemy_type, GAME_ASSETS["enemy_slime"])


def get_tile_asset(tile_type: TileType) -> dict:
    mapping = {
        TileType.WALL: "wall",
        TileType.POTION: "potion",
        TileType.GOLD: "gold",
        TileType.EXIT: "exit",
        TileType.EMPTY: "floor",
    }
    key = mapping.get(tile_type, "floor")
    return GAME_ASSETS[key]
