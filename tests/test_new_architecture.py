#!/usr/bin/env python3
"""测试新模块化架构"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from pixel_dungeon import CONFIG, GAME_ASSETS
from pixel_dungeon.assets import TileType, get_player_asset, get_enemy_asset
from pixel_dungeon.core.player import Player
from pixel_dungeon.core.enemy import Enemy
from pixel_dungeon.systems.particles import Particle, FloatingText, ParticleSystem
from pixel_dungeon.systems.upgrades import Upgrade, UpgradePool
from pixel_dungeon.systems.shop import Shop, ShopItem
from pixel_dungeon.systems.achievements import AchievementManager, AchievementTier
from pixel_dungeon.utils.validators import Validator, validate_command_arg
from pixel_dungeon.utils.save_load import SaveManager, SaveData


class TestConfig(unittest.TestCase):
    """测试配置模块"""

    def test_config_defaults(self):
        """测试配置默认值"""
        self.assertEqual(CONFIG.fps, 30)
        self.assertEqual(CONFIG.map_width, 80)
        self.assertEqual(CONFIG.map_height, 40)
        self.assertEqual(CONFIG.tile_width, 6)
        self.assertEqual(CONFIG.tile_height, 3)
        self.assertTrue(CONFIG.lighting)
        self.assertTrue(CONFIG.particles)

    def test_config_setters(self):
        """测试配置设置器"""
        original_fps = CONFIG.fps

        # 有效值
        self.assertTrue(CONFIG.set_fps(60))
        self.assertEqual(CONFIG.fps, 60)

        # 无效值
        self.assertFalse(CONFIG.set_fps(100))
        self.assertFalse(CONFIG.set_fps(5))

        # 恢复
        CONFIG.fps = original_fps

    def test_config_toggles(self):
        """测试配置切换"""
        original_lighting = CONFIG.lighting

        result = CONFIG.toggle_lighting()
        self.assertEqual(result, not original_lighting)

        # 恢复
        CONFIG.lighting = original_lighting


class TestAssets(unittest.TestCase):
    """测试资源模块"""

    def test_player_assets_exist(self):
        """测试玩家资源存在"""
        for char in ["default", "mage", "rogue", "paladin"]:
            asset = get_player_asset(char)
            self.assertIsNotNone(asset)
            self.assertIn("sprite", asset)
            self.assertIn("hp", asset)
            self.assertIn("atk", asset)

    def test_enemy_assets_exist(self):
        """测试敌人资源存在"""
        enemy_types = [
            "enemy_slime",
            "enemy_goblin",
            "enemy_skeleton",
            "enemy_orc",
            "enemy_shadow",
        ]
        for etype in enemy_types:
            asset = get_enemy_asset(etype)
            self.assertIsNotNone(asset)
            self.assertIn("sprite", asset)

    def test_tile_types(self):
        """测试地图格子类型"""
        self.assertIsNotNone(TileType.EMPTY)
        self.assertIsNotNone(TileType.WALL)
        self.assertIsNotNone(TileType.EXIT)


class TestPlayer(unittest.TestCase):
    """测试玩家类"""

    def test_player_create_default(self):
        """测试创建默认玩家"""
        player = Player.create("default")
        self.assertEqual(player.hp, 100)
        self.assertEqual(player.max_hp, 100)
        self.assertEqual(player.atk, 10)
        self.assertEqual(player.char_set, "default")

    def test_player_create_mage(self):
        """测试创建法师"""
        player = Player.create("mage")
        self.assertEqual(player.hp, 80)
        self.assertEqual(player.atk, 15)
        self.assertEqual(player.crit, 10)

    def test_player_take_damage(self):
        """测试受到伤害"""
        player = Player.create("default")
        player.hp = 100

        damage = player.take_damage(20)
        self.assertEqual(player.hp, 80)
        self.assertEqual(damage, 20)

    def test_player_heal(self):
        """测试恢复生命"""
        player = Player.create("default")
        player.hp = 50

        healed = player.heal(30)
        self.assertEqual(player.hp, 80)
        self.assertEqual(healed, 30)

        # 测试上限
        healed = player.heal(50)
        self.assertEqual(player.hp, 100)
        self.assertEqual(healed, 20)

    def test_player_level_up(self):
        """测试升级"""
        player = Player.create("default")
        original_level = player.level
        original_max_hp = player.max_hp
        original_atk = player.atk

        player.level_up()

        self.assertEqual(player.level, original_level + 1)
        self.assertEqual(player.max_hp, original_max_hp + 10)
        self.assertEqual(player.atk, original_atk + 2)


class TestEnemy(unittest.TestCase):
    """测试敌人类"""

    def test_enemy_creation(self):
        """测试创建敌人"""
        enemy = Enemy.create("enemy_slime", "史莱姆", 5, 5, 20, 5, 10, 5, 1)
        self.assertEqual(enemy.name, "史莱姆")
        self.assertEqual(enemy.x, 5)
        self.assertEqual(enemy.y, 5)
        self.assertTrue(enemy.is_alive())

    def test_enemy_scaling(self):
        """测试敌人属性缩放"""
        enemy_floor1 = Enemy.create("enemy_slime", "史莱姆", 5, 5, 20, 5, 10, 5, 1)
        enemy_floor10 = Enemy.create("enemy_slime", "史莱姆", 5, 5, 20, 5, 10, 5, 10)

        # 高层敌人应该更强
        self.assertGreater(enemy_floor10.hp, enemy_floor1.hp)
        self.assertGreater(enemy_floor10.atk, enemy_floor1.atk)

    def test_enemy_take_damage(self):
        """测试敌人受伤"""
        enemy = Enemy.create("enemy_slime", "史莱姆", 5, 5, 20, 5, 10, 5, 1)
        enemy.take_damage(10)

        self.assertEqual(enemy.hp, 10)
        self.assertEqual(enemy.flash, 3)


class TestParticleSystem(unittest.TestCase):
    """测试粒子系统"""

    def test_particle_update(self):
        """测试粒子更新"""
        particle = Particle(0.0, 0.0, "*", "red", 10, 0.1, 0.1)

        self.assertTrue(particle.update())
        self.assertEqual(particle.life, 9)

        # 消耗完生命
        for _ in range(9):
            particle.update()

        self.assertFalse(particle.update())

    def test_floating_text(self):
        """测试浮动文字"""
        text = FloatingText(5, 5, "+10", "green", 20)

        self.assertTrue(text.update())
        self.assertEqual(text.life, 19)

        style = text.get_alpha_style()
        self.assertIn("bold", style)


class TestUpgradeSystem(unittest.TestCase):
    """测试升级系统"""

    def test_upgrade_creation(self):
        """测试创建升级"""
        player = Player.create("default")
        original_hp = player.max_hp

        upgrade = Upgrade(
            "生命强化",
            "最大生命 +20",
            lambda p: (
                setattr(p, "max_hp", p.max_hp + 20) or setattr(p, "hp", p.hp + 20)
            ),
            "common",
            "♥",
        )

        upgrade.apply(player)
        self.assertEqual(player.max_hp, original_hp + 20)

    def test_upgrade_pool(self):
        """测试升级池"""
        upgrades = UpgradePool.get_random_upgrades(3)

        self.assertEqual(len(upgrades), 3)
        for upgrade in upgrades:
            self.assertIsNotNone(upgrade.name)
            self.assertIsNotNone(upgrade.effect)
            self.assertIn(upgrade.rarity, ["common", "rare", "epic", "legendary"])


class TestShopSystem(unittest.TestCase):
    """测试商店系统"""

    def test_shop_item(self):
        """测试商店商品"""
        player = Player.create("default")
        player.gold = 100

        item = ShopItem(
            "测试物品",
            "测试描述",
            50,
            "★",
            lambda p: setattr(p, "atk", p.atk + 5),
        )

        self.assertTrue(item.buy(player))
        self.assertEqual(player.gold, 50)
        self.assertEqual(player.atk, 15)

    def test_shop_insufficient_gold(self):
        """测试金币不足"""
        player = Player.create("default")
        player.gold = 10

        item = ShopItem(
            "昂贵物品",
            "测试",
            100,
            "★",
            lambda p: setattr(p, "atk", p.atk + 5),
        )

        self.assertFalse(item.buy(player))


class TestAchievementSystem(unittest.TestCase):
    """测试成就系统"""

    def test_achievement_creation(self):
        """测试成就管理器创建"""
        manager = AchievementManager()
        self.assertEqual(len(manager.unlocked), 0)

    def test_achievement_tiers(self):
        """测试成就等级"""
        self.assertIsNotNone(AchievementTier.BRONZE)
        self.assertIsNotNone(AchievementTier.SILVER)
        self.assertIsNotNone(AchievementTier.GOLD)
        self.assertIsNotNone(AchievementTier.PLATINUM)


class TestValidators(unittest.TestCase):
    """测试验证器模块"""

    def test_validator_valid_input(self):
        """测试有效输入"""
        validator = Validator("test").add_rule(
            lambda x: 10 <= x <= 60, "值必须在 10-60 之间", int
        )

        # 使用整数输入
        result = validator.validate(30)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.value, 30)

    def test_validator_invalid_input(self):
        """测试无效输入"""
        validator = Validator("fps").add_rule(
            lambda x: 10 <= x <= 60, "fps 必须在 10-60 之间", int
        )

        result = validator.validate("100")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error)


class TestSaveLoad(unittest.TestCase):
    """测试保存/加载系统"""

    def test_save_data_creation(self):
        """测试保存数据创建"""
        save_data = SaveData(
            version="1.0",
            timestamp="2026-01-01T00:00:00",
            floor=5,
        )

        self.assertEqual(save_data.version, "1.0")
        self.assertEqual(save_data.floor, 5)

    def test_save_data_conversion(self):
        """测试保存数据转换"""
        save_data = SaveData(floor=10)
        data_dict = save_data.to_dict()

        self.assertEqual(data_dict["floor"], 10)

        restored = SaveData.from_dict(data_dict)
        self.assertEqual(restored.floor, 10)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def test_full_game_flow(self):
        """测试完整游戏流程"""
        from pixel_dungeon.core.game import Game

        game = Game()
        game.init_game("default")

        # 验证初始化
        self.assertIsNotNone(game.player)
        self.assertEqual(game.floor, 1)
        self.assertEqual(game.state, "playing")

        # 验证地图
        self.assertEqual(len(game.map), CONFIG.map_height)
        self.assertEqual(len(game.map[0]), CONFIG.map_width)

        # 验证系统
        self.assertIsNotNone(game.particles)
        self.assertIsNotNone(game.shop)
        self.assertIsNotNone(game.achievements)
        self.assertIsNotNone(game.save_manager)


if __name__ == "__main__":
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出摘要
    print(f"\n{'=' * 70}")
    print(f"测试完成!")
    print(f"运行: {result.testsRun} 个测试")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"{'=' * 70}")

    # 返回退出码
    sys.exit(0 if result.wasSuccessful() else 1)
