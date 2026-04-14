#!/usr/bin/env python3
"""游戏主逻辑模块"""

import random
import time
from typing import List, Tuple, Optional, Dict, Any

from rich.console import Console
from rich.live import Live

from ..config import CONFIG
from ..assets import TileType, ENEMY_TYPES
from ..core.player import Player
from ..core.enemy import Enemy
from ..systems.particles import ParticleSystem
from ..systems.upgrades import UpgradePool
from ..systems.shop import Shop
from ..systems.achievements import AchievementManager
from ..utils.validators import validate_command_arg
from ..utils.save_load import SaveManager
from ..ui.renderer import Renderer
from ..core.commands import CommandHandler


console = Console()


class Game:
    """游戏主类"""

    def __init__(self):
        # 游戏状态
        self.state = "playing"  # playing, upgrading, shopping, paused, game_over
        self.running = True
        self.floor = 1
        self.paused = False

        # 游戏对象
        self.player: Optional[Player] = None
        self.enemies: List[Enemy] = []
        self.map: List[List[TileType]] = []
        self.explored_map: List[List[bool]] = []

        # 系统
        self.particles = ParticleSystem(CONFIG.particle_limit)
        self.shop = Shop()
        self.achievements = AchievementManager()
        self.save_manager = SaveManager()
        self.renderer = Renderer(console)

        # 升级系统
        self.upgrades = []
        self.sel_upgrade = 0

        self.cmd_mode = False
        self.cmd_buffer = ""
        self.cmd_suggestions = []
        self.commands = None
        self.return_to_menu = False

        # 消息日志
        self.messages: List[Tuple[str, str, str]] = []

        # 统计
        self.stats: Dict[str, Any] = {
            "enemies_killed": 0,
            "total_gold_earned": 0,
            "total_healed": 0,
            "close_call_wins": 0,
            "max_crit_damage": 0,
            "play_time": 0,
        }

        # 时间记录
        self.start_time = time.time()

    def init_game(self, char_set: str = "default") -> None:
        """初始化游戏"""
        self.player = Player.create(char_set)
        self.init_map()
        self.commands = CommandHandler(self)
        self.add_msg("欢迎来到像素地牢！", "green", "system")

    def init_map(self) -> None:
        self.map = [
            [TileType.EMPTY for _ in range(CONFIG.map_width)]
            for _ in range(CONFIG.map_height)
        ]
        self.explored_map = [
            [False for _ in range(CONFIG.map_width)] for _ in range(CONFIG.map_height)
        ]

        for x in range(CONFIG.map_width):
            self.map[0][x] = TileType.WALL
            self.map[CONFIG.map_height - 1][x] = TileType.WALL
        for y in range(CONFIG.map_height):
            self.map[y][0] = TileType.WALL
            self.map[y][CONFIG.map_width - 1] = TileType.WALL

        for _ in range(CONFIG.map_width * CONFIG.map_height // 10):
            x = random.randint(2, CONFIG.map_width - 3)
            y = random.randint(2, CONFIG.map_height - 3)
            if (x, y) != (1, 1) and (x, y) != (
                CONFIG.map_width - 2,
                CONFIG.map_height - 2,
            ):
                self.map[y][x] = TileType.WALL

        if self.player:
            self.player.x = 1
            self.player.y = 1

        self.spawn_enemies()
        self.spawn_items()
        self.map[CONFIG.map_height - 2][CONFIG.map_width - 2] = TileType.EXIT
        self.update_explored()

    def update_explored(self) -> None:
        import math

        px, py = self.player.x, self.player.y
        vd = CONFIG.view_distance

        for y in range(CONFIG.map_height):
            for x in range(CONFIG.map_width):
                dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
                if dist <= vd:
                    self.explored_map[y][x] = True

    def spawn_enemies(self) -> None:
        """生成敌人"""
        self.enemies.clear()

        # 根据层数确定可用敌人类型
        available = ENEMY_TYPES[: min(len(ENEMY_TYPES), 1 + self.floor // 3)]

        num_enemies = random.randint(3, 5) + self.floor // 2

        for _ in range(num_enemies):
            enemy_type, name, hp, atk, exp, gold = random.choice(available)

            # 找到空位置
            for _ in range(100):  # 尝试100次
                x = random.randint(1, CONFIG.map_width - 2)
                y = random.randint(1, CONFIG.map_height - 2)

                if (
                    self.map[y][x] == TileType.EMPTY
                    and not self.get_enemy_at(x, y)
                    and abs(x - self.player.x) + abs(y - self.player.y) > 5
                ):  # 不要太靠近玩家
                    enemy = Enemy.create(
                        enemy_type, name, x, y, hp, atk, exp, gold, self.floor
                    )
                    self.enemies.append(enemy)
                    break

    def spawn_items(self) -> None:
        """生成物品"""
        # 生成血瓶
        for _ in range(random.randint(1, 3)):
            x = random.randint(1, CONFIG.map_width - 2)
            y = random.randint(1, CONFIG.map_height - 2)
            if self.map[y][x] == TileType.EMPTY and not self.get_enemy_at(x, y):
                self.map[y][x] = TileType.POTION

        # 生成金币
        for _ in range(random.randint(2, 5)):
            x = random.randint(1, CONFIG.map_width - 2)
            y = random.randint(1, CONFIG.map_height - 2)
            if self.map[y][x] == TileType.EMPTY and not self.get_enemy_at(x, y):
                self.map[y][x] = TileType.GOLD

    def get_enemy_at(self, x: int, y: int) -> Optional[Enemy]:
        """获取指定位置的敌人"""
        for enemy in self.enemies:
            if enemy.x == x and enemy.y == y and enemy.is_alive():
                return enemy
        return None

    def move_player(self, dx: int, dy: int) -> bool:
        """移动玩家，返回是否成功移动"""
        if self.state != "playing" or self.paused:
            return False

        new_x = self.player.x + dx
        new_y = self.player.y + dy

        # 检查边界
        if not (0 <= new_x < CONFIG.map_width and 0 <= new_y < CONFIG.map_height):
            return False

        # 检查墙壁
        if self.map[new_y][new_x] == TileType.WALL:
            return False

        # 检查敌人
        enemy = self.get_enemy_at(new_x, new_y)
        if enemy:
            self.attack(enemy)
            return True

        # 移动
        self.player.x = new_x
        self.player.y = new_y

        # 拾取物品
        self.check_tile(new_x, new_y)

        # 敌人回合
        self.enemy_turn()

        # 更新动画
        self.animate()

        # 检查成就
        self.check_achievements()

        self.update_explored()

        return True

    def attack(self, enemy: Enemy) -> None:
        """玩家攻击敌人"""
        # 计算伤害
        damage = self.player.atk
        is_crit = random.randint(1, 100) <= self.player.crit

        if is_crit:
            damage = int(damage * 2)
            self.stats["max_crit_damage"] = max(self.stats["max_crit_damage"], damage)

        # 造成伤害
        enemy.take_damage(damage)

        # 显示伤害
        self.particles.spawn(enemy.x, enemy.y, 5, ["*"], ["red"])
        self.particles.add_text(
            enemy.x, enemy.y, str(damage), "bold yellow" if is_crit else "white", 25
        )

        msg = f"对 {enemy.name} 造成 {damage} 伤害"
        if is_crit:
            msg += " (暴击!)"
        self.add_msg(msg, "red" if is_crit else "white", "combat")

        # 生命偷取
        if self.player.lifesteal > 0 and damage > 0:
            heal = int(damage * self.player.lifesteal / 100)
            if heal > 0:
                actual = self.player.heal(heal)
                self.stats["total_healed"] += actual
                self.particles.add_text(
                    self.player.x, self.player.y, f"+{actual}", "green", 20
                )

        # 检查击杀
        if not enemy.is_alive():
            self.kill_enemy(enemy)

        # 敌人回合
        self.enemy_turn()
        self.animate()

    def kill_enemy(self, enemy: Enemy) -> None:
        """击杀敌人"""
        self.particles.spawn(enemy.x, enemy.y, 8, ["*", "+"], ["red", "yellow"])
        self.add_msg(
            f"击败了 {enemy.name}！获得 {enemy.exp} 经验, {enemy.gold}G",
            "yellow",
            "combat",
        )

        self.player.exp += enemy.exp
        self.player.gold += enemy.gold
        self.stats["enemies_killed"] += 1
        self.stats["total_gold_earned"] += enemy.gold

        # 检查升级
        if self.player.exp >= self.player.exp_next:
            self.level_up()

    def level_up(self) -> None:
        """升级"""
        self.player.level_up()
        self.add_msg(f"升级了！现在是 {self.player.level} 级", "cyan", "level")
        self.particles.spawn(
            self.player.x, self.player.y, 10, ["★", "✦"], ["yellow", "cyan"]
        )

        # 进入升级选择
        self.upgrades = UpgradePool.get_random_upgrades(3)
        self.sel_upgrade = 0
        self.state = "upgrading"

    def select_upgrade(self, index: int) -> None:
        """选择升级"""
        if 0 <= index < len(self.upgrades):
            upgrade = self.upgrades[index]
            upgrade.apply(self.player)
            self.add_msg(f"获得: {upgrade.name}！", "cyan", "success")
            self.particles.spawn(
                self.player.x, self.player.y, 8, ["✦", "★"], ["yellow", "cyan"]
            )
            self.state = "playing"

    def enemy_turn(self) -> None:
        """敌人回合"""
        for enemy in self.enemies:
            if not enemy.is_alive():
                continue

            enemy.animate()

            # 简单AI：如果相邻则攻击，否则移动
            dx = abs(enemy.x - self.player.x)
            dy = abs(enemy.y - self.player.y)

            if dx + dy == 1:  # 相邻
                self.enemy_attack(enemy)
            elif dx + dy < 8:  # 在视野内，尝试接近
                self.move_enemy(enemy)

        # 玩家恢复
        regen = self.player.regen_hp()
        if regen > 0:
            self.stats["total_healed"] += regen

    def enemy_attack(self, enemy: Enemy) -> None:
        """敌人攻击玩家"""
        damage = enemy.atk
        actual = self.player.take_damage(damage)

        self.particles.add_text(self.player.x, self.player.y, f"-{actual}", "red", 25)
        self.add_msg(f"{enemy.name} 对你造成 {actual} 伤害", "red", "combat")

        # 检查死亡
        if not self.player.is_alive():
            self.game_over()
        elif self.player.hp < 10:
            # 死里逃生
            pass

    def move_enemy(self, enemy: Enemy) -> None:
        dx = 1 if enemy.x < self.player.x else (-1 if enemy.x > self.player.x else 0)
        dy = 1 if enemy.y < self.player.y else (-1 if enemy.y > self.player.y else 0)

        if dx == 0 and dy == 0:
            return

        if dx != 0 and dy != 0:
            if random.choice([True, False]):
                candidates = [(dx, 0), (0, dy)]
            else:
                candidates = [(0, dy), (dx, 0)]
        else:
            candidates = [(dx, dy)]

        for cdx, cdy in candidates:
            new_x = enemy.x + cdx
            new_y = enemy.y + cdy
            if (
                0 <= new_x < CONFIG.map_width
                and 0 <= new_y < CONFIG.map_height
                and self.map[new_y][new_x] != TileType.WALL
                and not self.get_enemy_at(new_x, new_y)
                and (new_x, new_y) != (self.player.x, self.player.y)
            ):
                enemy.x = new_x
                enemy.y = new_y
                return

        random.shuffle(candidates)
        for cdx, cdy in candidates:
            alt_moves = []
            if cdx != 0 and cdy == 0:
                alt_moves = [(0, 1), (0, -1)]
            elif cdy != 0 and cdx == 0:
                alt_moves = [(1, 0), (-1, 0)]
            random.shuffle(alt_moves)
            for adx, ady in alt_moves:
                nx, ny = enemy.x + adx, enemy.y + ady
                if (
                    0 <= nx < CONFIG.map_width
                    and 0 <= ny < CONFIG.map_height
                    and self.map[ny][nx] != TileType.WALL
                    and not self.get_enemy_at(nx, ny)
                    and (nx, ny) != (self.player.x, self.player.y)
                ):
                    enemy.x = nx
                    enemy.y = ny
                    return

    def check_tile(self, x: int, y: int) -> None:
        """检查并处理格子"""
        tile = self.map[y][x]

        if tile == TileType.POTION:
            heal = self.player.heal(30)
            self.stats["total_healed"] += heal
            self.map[y][x] = TileType.EMPTY
            self.particles.spawn(x, y, 5, ["+"], ["red"])
            self.add_msg(f"喝下药水，恢复 {heal} HP", "red", "item")

        elif tile == TileType.GOLD:
            amount = random.randint(5, 15)
            self.player.gold += amount
            self.stats["total_gold_earned"] += amount
            self.map[y][x] = TileType.EMPTY
            self.particles.spawn(x, y, 4, ["◆"], ["yellow"])
            self.add_msg(f"拾取 {amount}G", "yellow", "item")

        elif tile == TileType.EXIT:
            self.next_floor()

    def next_floor(self) -> None:
        """进入下一层"""
        self.floor += 1
        self.add_msg(f"进入第 {self.floor} 层...", "cyan", "system")
        self.init_map()
        self.particles.clear()

    def open_shop(self) -> None:
        """打开商店"""
        self.shop.refresh()
        self.state = "shopping"

    def close_shop(self) -> None:
        """关闭商店"""
        self.state = "playing"

    def shop_navigate(self, direction: int) -> None:
        """商店导航"""
        if direction > 0:
            self.shop.select_next()
        else:
            self.shop.select_prev()

    def shop_buy(self) -> None:
        """购买商品"""
        success, msg = self.shop.buy_selected(self.player)
        self.add_msg(msg, "green" if success else "red", "shop")
        if success:
            self.particles.spawn(self.player.x, self.player.y, 5, ["$"], ["yellow"])

    def game_over(self) -> None:
        """游戏结束"""
        self.state = "game_over"
        self.add_msg("你被击败了！游戏结束。", "red", "system")

    def add_msg(
        self, text: str, style: str = "white", msg_type: str = "system"
    ) -> None:
        """添加消息"""
        self.messages.append((text, style, msg_type))
        if len(self.messages) > 100:
            self.messages.pop(0)

    def animate(self) -> None:
        """更新动画"""
        self.player.animate()
        for enemy in self.enemies:
            enemy.animate()
        self.particles.update()

    def check_achievements(self) -> None:
        """检查成就"""
        new_achievements = self.achievements.check(self)
        for ach in new_achievements:
            self.add_msg(
                f"🏆 解锁成就: {ach.name}！", ach.get_tier_style(), "achievement"
            )

    def toggle_pause(self) -> None:
        """切换暂停状态"""
        self.paused = not self.paused
        if self.paused:
            self.add_msg("游戏已暂停", "yellow", "system")
        else:
            self.add_msg("游戏继续", "green", "system")

    def save_game(self, slot: int = 0) -> bool:
        """保存游戏"""
        success = self.save_manager.save(self, slot)
        if success:
            self.add_msg(f"游戏已保存到槽位 {slot}", "green", "system")
        else:
            self.add_msg("保存失败", "red", "system")
        return success

    def load_game(self, slot: int = 0) -> bool:
        """加载游戏"""
        success = self.save_manager.load(self, slot)
        if success:
            self.add_msg(f"已从槽位 {slot} 加载游戏", "green", "system")
        else:
            self.add_msg("加载失败", "red", "system")
        return success

    def reset(self) -> None:
        """重置游戏"""
        self.__init__()

    def run(self) -> None:
        """运行游戏主循环"""
        from ..input_handler import CrossPlatformInputHandler

        handler = CrossPlatformInputHandler()
        frame_time = 1.0 / CONFIG.fps

        try:
            handler.start()

            with Live(
                console=console, refresh_per_second=CONFIG.fps, screen=True
            ) as live:
                last_time = time.time()

                while self.running:
                    try:
                        # 帧率控制
                        current_time = time.time()
                        elapsed = current_time - last_time

                        if elapsed < frame_time:
                            time.sleep(frame_time - elapsed)

                        last_time = time.time()

                        # 更新游戏时间
                        self.stats["play_time"] = int(time.time() - self.start_time)

                        # 处理输入
                        self.handle_input(handler)

                        # 更新动画
                        if not self.paused and self.state == "playing":
                            self.animate()

                        # 渲染
                        self.render(live)

                        if self.return_to_menu:
                            self.running = False
                            break
                    except KeyboardInterrupt:
                        self.running = False
                        break

        finally:
            handler.stop()

    def handle_input(self, handler) -> None:
        key = handler.get_key()
        if not key:
            return

        if self.cmd_mode:
            self.handle_command_input(key)
            return

        if self.paused:
            self.handle_pause_input(key)
            return

        if self.state == "playing":
            self.handle_playing_input(key)
        elif self.state == "upgrading":
            self.handle_upgrade_input(key)
        elif self.state == "shopping":
            self.handle_shop_input(key)
        elif self.state == "game_over":
            self.handle_gameover_input(key)

    def handle_playing_input(self, key: str) -> None:
        key_map = {
            "w": (0, -1),
            "W": (0, -1),
            "UP": (0, -1),
            "s": (0, 1),
            "S": (0, 1),
            "DOWN": (0, 1),
            "a": (-1, 0),
            "A": (-1, 0),
            "LEFT": (-1, 0),
            "d": (1, 0),
            "D": (1, 0),
            "RIGHT": (1, 0),
        }

        if key in key_map:
            dx, dy = key_map[key]
            self.move_player(dx, dy)
        elif key == " ":
            self.enemy_turn()
            self.animate()
        elif key.lower() == "b":
            self.open_shop()
        elif key.lower() == "p":
            self.toggle_pause()
        elif key.lower() == "s":
            self.save_game()
        elif key.lower() == "r":
            self.restart_game()
        elif key.lower() == "m":
            self.return_to_menu = True
            self.running = False
        elif key.lower() == "q":
            self.running = False
        elif key == "/" or key == "\x18":
            self.cmd_mode = True
            self.cmd_buffer = ""
            self.cmd_suggestions = (
                self.commands.get_suggestions("") if self.commands else []
            )
            self.add_msg("进入命令模式，按 Esc 退出", "cyan", "system")
        elif key == "?":
            self.add_msg(
                "WASD/方向键:移动  空格:等待  B:商店  P:暂停  /:命令", "dim", "info"
            )

    def handle_command_input(self, key: str) -> None:
        if key == "\x1b":
            self.cmd_mode = False
            self.cmd_buffer = ""
            self.cmd_suggestions = []
            self.add_msg("退出命令模式", "dim", "info")
        elif key == "\r" or key == "\n":
            if self.commands and self.cmd_buffer.strip():
                result = self.commands.execute("/" + self.cmd_buffer.strip())
                if result:
                    self.add_msg(result, "yellow")
            self.cmd_mode = False
            self.cmd_buffer = ""
            self.cmd_suggestions = []
        elif key == "\x7f":
            self.cmd_buffer = self.cmd_buffer[:-1]
            self.cmd_suggestions = (
                self.commands.get_suggestions(self.cmd_buffer) if self.commands else []
            )
        elif key == "\t":
            if self.cmd_suggestions:
                self.cmd_buffer = self.cmd_suggestions[0]
                self.cmd_suggestions = []
        elif len(key) == 1 and key.isprintable():
            self.cmd_buffer += key
            self.cmd_suggestions = (
                self.commands.get_suggestions(self.cmd_buffer) if self.commands else []
            )

    def handle_upgrade_input(self, key: str) -> None:
        """处理升级选择输入"""
        if key == "1":
            self.select_upgrade(0)
        elif key == "2":
            self.select_upgrade(1)
        elif key == "3":
            self.select_upgrade(2)

    def handle_shop_input(self, key: str) -> None:
        """处理商店输入"""
        if key == "w" or key == "W" or key == "UP":
            self.shop_navigate(-1)
        elif key == "s" or key == "S" or key == "DOWN":
            self.shop_navigate(1)
        elif key == "\r" or key == "\n":
            self.shop_buy()
        elif key == "\x1b":  # Escape
            self.close_shop()
        elif key.lower() == "q":
            self.close_shop()

    def handle_gameover_input(self, key: str) -> None:
        if key.lower() == "r":
            self.restart_game()
        elif key.lower() == "m":
            self.return_to_menu = True
            self.running = False
        elif key.lower() == "q":
            self.running = False

    def handle_pause_input(self, key: str) -> None:
        if key.lower() == "p":
            self.toggle_pause()
        elif key.lower() == "s":
            self.save_game()
        elif key.lower() == "r":
            self.toggle_pause()
            self.restart_game()
        elif key.lower() == "m":
            self.return_to_menu = True
            self.running = False
        elif key.lower() == "q":
            self.running = False
        elif key == "\x1b":
            self.toggle_pause()

    def restart_game(self) -> None:
        char = self.player.char_set if self.player else "default"
        self.reset()
        self.init_game(char)

    def render(self, live) -> None:
        if self.paused:
            layout = self.renderer.render_with_pause()
        elif self.cmd_mode:
            layout = self.renderer.render_with_command_overlay(
                self, self.cmd_buffer, self.cmd_suggestions
            )
        elif self.state == "upgrading":
            layout = self.renderer.render_with_upgrade(self)
        elif self.state == "shopping":
            layout = self.renderer.render_with_shop(self)
        elif self.state == "game_over":
            layout = self.renderer.render_with_gameover(self)
        else:
            layout = self.renderer.render_game(self)

        live.update(layout)
