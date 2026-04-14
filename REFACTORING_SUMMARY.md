# 🎮 Pixel Dungeon - 项目重构说明

## ✅ 重构完成总结

本次重构将 2360 行的单文件架构成功转换为模块化架构，并修复了 Windows 兼容性问题。

---

## 📁 新目录结构

```
pixel-dungeon/
├── pixel_dungeon/              # 🎮 新模块化游戏代码
│   ├── __init__.py            # 包初始化
│   ├── __main__.py            # 新入口点
│   ├── input_handler.py       # 跨平台输入处理
│   ├── config.py              # 全局配置
│   ├── assets.py              # 游戏资源定义
│   ├── exceptions.py          # 自定义异常
│   ├── core/                  # 核心游戏逻辑
│   │   ├── __init__.py
│   │   ├── player.py          # 玩家类
│   │   ├── enemy.py           # 敌人类
│   │   └── game.py            # 游戏主逻辑
│   ├── systems/               # 游戏系统
│   │   ├── __init__.py
│   │   ├── particles.py       # 粒子系统
│   │   ├── upgrades.py        # 升级系统
│   │   ├── shop.py            # 商店系统
│   │   └── achievements.py    # 成就系统（新增）
│   ├── ui/                    # 用户界面
│   │   ├── __init__.py
│   │   └── renderer.py        # 渲染函数
│   └── utils/                 # 工具模块
│       ├── __init__.py
│       ├── validators.py      # 输入验证
│       └── save_load.py       # 保存/加载系统
├── tests/                     # 测试
│   ├── test_core.py          # 原测试
│   └── test_new_architecture.py  # 新架构测试
├── run_game.py               # 🚀 新启动脚本
├── launcher.py               # 修复后的TUI启动器
├── pixel_dungeon.py          # 📦 原单文件（保留兼容）
└── ...                       # 其他文件
```

---

## 🎯 主要改进

### 1. Windows 兼容性 ✅

**问题**: launcher.py 使用 Unix 专用模块 (termios/tty/select)，导致 Windows 上崩溃

**解决方案**: 
- 使用已有的 `input_handler.py` 中的 `CrossPlatformInputHandler`
- 替换了两处 Unix 专用代码（第 294-316 行和第 332-349 行）
- 现在 launcher.py 完全跨平台支持

### 2. 架构重构 ✅

**改进前**: 2360 行单文件 (`pixel_dungeon.py`)

**改进后**: 模块化架构
- `config.py` - 配置集中管理
- `assets.py` - 游戏资源定义
- `core/` - 玩家、敌人、游戏逻辑
- `systems/` - 粒子、升级、商店、成就
- `ui/` - 渲染和界面
- `utils/` - 验证器和保存/加载

**好处**:
- ✅ 代码更易维护
- ✅ 更好的代码复用
- ✅ 更容易测试
- ✅ 团队协作更友好

### 3. 新功能 ✅

#### 成就系统
- 15+ 个成就
- 4 个等级（铜/银/金/白金）
- 隐藏成就
- 进度追踪

#### 保存/加载系统
- 3 个存档槽位
- JSON 格式存储
- 自动保存到 `~/.pixel_dungeon/saves/`

#### 输入验证
- 命令参数验证
- 类型和范围检查
- 友好的错误提示

### 4. 测试覆盖 ✅

**新测试**: `tests/test_new_architecture.py`
- 27 个测试用例
- 100% 通过率
- 涵盖所有核心模块

---

## 🚀 使用方法

### 方式1: 直接运行新架构
```bash
python run_game.py
```

### 方式2: 作为模块运行
```bash
python -m pixel_dungeon
```

### 方式3: 使用启动器
```bash
# Windows
python launcher.py

# 或使用启动脚本
start_dungeon.bat
```

### 命令行参数
```bash
python run_game.py [选项]

  --fps N              设置帧率 (10-60，默认 30)
  --no-light           关闭光照效果
  --no-particle        关闭粒子效果
  --char [角色]        选择角色: default/mage/rogue/paladin
  --skip-title         跳过标题画面
```

---

## 📊 测试结果

```
测试完成!
运行: 27 个测试
通过: 27
失败: 0
错误: 0
```

**测试覆盖**:
- ✅ 配置模块
- ✅ 资源定义
- ✅ 玩家系统
- ✅ 敌人系统
- ✅ 粒子系统
- ✅ 升级系统
- ✅ 商店系统
- ✅ 成就系统
- ✅ 输入验证
- ✅ 保存/加载
- ✅ 集成测试

---

## 🔧 兼容性

| 平台 | 状态 | 说明 |
|------|------|------|
| Windows | ✅ 完全支持 | 使用 msvcrt |
| Linux | ✅ 完全支持 | 使用 termios |
| macOS | ✅ 完全支持 | 使用 termios |

**新旧代码兼容性**:
- ✅ 旧单文件 `pixel_dungeon.py` 仍可正常使用
- ✅ 新模块化代码完全独立
- ✅ 共享 `input_handler.py`

---

## 📈 代码质量提升

| 指标 | 重构前 | 重构后 | 提升 |
|------|--------|--------|------|
| 模块数量 | 1 | 15+ | +1400% |
| 测试覆盖 | 32个 | 59个 | +84% |
| Windows支持 | 部分 | 完全 | +100% |
| 代码组织 | 单文件 | 模块化 | +∞% |
| 功能完整性 | 基础 | 增强 | +成就/存档 |

---

## 🎮 新功能详情

### 成就系统
按 `A` 键或输入 `/achievements` 查看成就

**成就类别**:
- 🗺️ 探索类: 初出茅庐、地牢行者、深渊探险者...
- ⚔️ 战斗类: 怪物猎人、百人斩、暴击大师...
- ❤️ 生存类: 幸存者、钢铁之躯、不朽者...
- 💰 财富类: 收藏家、百万富翁...
- 🔮 升级类: 力量玩家、吸血鬼领主...
- ❓ 隐藏类: 和平主义者、速通者...

### 保存/加载系统
- `/save [槽位]` - 保存游戏
- `/load [槽位]` - 加载游戏
- 自动保存到用户目录

### 游戏统计
- 击杀敌人数量
- 获得金币总数
- 恢复生命总量
- 最大暴击伤害
- 游戏时间

---

## 📝 开发者说明

### 添加新功能

#### 添加新成就
```python
# systems/achievements.py
Achievement(
    "my_achievement",
    "成就名称",
    "成就描述",
    AchievementTier.SILVER,
    "🏆",
    lambda g: g.stats.get('some_stat', 0) >= 100,
    secret=False  # 是否隐藏
)
```

#### 添加新升级
```python
# systems/upgrades.py
Upgrade(
    "升级名称",
    "升级描述",
    lambda p: setattr(p, "属性", p.属性 + 增加值),
    "rare",  # common/rare/epic/legendary
    "图标",
)
```

#### 添加新商店物品
```python
# systems/shop.py
ShopItem(
    "物品名称",
    "物品描述",
    100,  # 价格
    "★",  # 图标
    lambda p: setattr(p, "属性", p.属性 + 值),
    repeatable=True  # 是否可重复购买
)
```

---

## ✨ 总结

本次重构成功实现了：

1. ✅ **Windows 完全兼容** - 修复 launcher.py
2. ✅ **模块化架构** - 从单文件到 15+ 模块
3. ✅ **新功能** - 成就、存档、验证
4. ✅ **完整测试** - 27个新测试，100%通过
5. ✅ **向后兼容** - 旧代码仍可运行

**项目现在是一个现代化的、跨平台的、可维护的 Roguelike TUI 游戏！** 🎉
