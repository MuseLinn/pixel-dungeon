# Pixel Dungeon (像素地牢) - AGENTS.md

> 本文档供 AI 编码助手阅读，用于快速理解项目结构和开发规范。

## 项目概述

**Pixel Dungeon** 是一个基于终端的 Roguelike 游戏，使用 Python + Rich 库构建的 TUI (Terminal User Interface) 应用。

- **项目名称**: 像素地牢 (Pixel Dungeon)
- **项目类型**: Roguelike TUI 游戏
- **技术栈**: Python 3.7+, Rich 库
- **代码语言**: 中文注释和文档
- **架构模式**: 单文件架构（所有游戏逻辑在一个文件中）

## 项目结构

```
/home/linn/pixel-dungeon/
├── pixel_dungeon.py      # 🎮 主游戏文件 (~1238 行，包含全部游戏逻辑)
├── check_env.py          # 🔍 环境检测工具（检查 Python 版本、Rich 库等）
├── start_dungeon.sh      # 🚀 Bash 启动脚本（自动检测环境并启动游戏）
├── README_PIXEL_DUNGEON.md  # 📖 功能说明文档
├── README_dungeon.md     # 📖 基础说明文档
└── AGENTS.md             # 📋 本文件
```

**注意**: 本项目采用**单文件架构**，所有游戏逻辑、数据定义、渲染代码都集中在 `pixel_dungeon.py` 一个文件中。

## 快速开始

### 环境要求
- Python 3.7 或更高版本
- Rich 库 (`pip3 install rich`)
- 终端支持 100x35 以上分辨率（推荐）

### 运行方式

**方式1: 使用启动脚本（推荐）**
```bash
./start_dungeon.sh
```

**方式2: 直接运行**
```bash
python3 pixel_dungeon.py
```

**方式3: 先检查环境**
```bash
python3 check_env.py
```

### 命令行参数
```bash
python3 pixel_dungeon.py [选项]

  --fps N              设置帧率 (10-60，默认 30)
  --no-light           关闭光照效果
  --no-particle        关闭粒子效果
  --char [角色]        选择角色: default/mage/rogue/paladin
  --skip-title         跳过标题画面
```

## 代码架构

### 全局配置

**CONFIG 类** - 游戏全局配置（代码第 27-36 行）
```python
class CONFIG:
    fps = 30                # 帧率
    map_width = 30          # 地图宽度
    map_height = 12         # 地图高度
    view_distance = 8       # 视野距离
    particle_limit = 30     # 粒子数量上限
    lighting = True         # 光照效果开关
    particles = True        # 粒子效果开关
    animations = True       # 动画开关
    char_set = "default"    # 当前角色
```

**GAME_ASSETS** - 游戏资源定义（代码第 39-54 行）
- 玩家角色: player_default, player_mage, player_rogue, player_paladin
- 敌人: enemy_slime, enemy_goblin, enemy_skeleton, enemy_orc, enemy_shadow
- 地图元素: wall, floor, potion, gold, exit

### 数据类定义

| 类名 | 用途 | 关键属性 |
|------|------|----------|
| `TileType` (Enum) | 地图格子类型 | EMPTY, WALL, EXIT, POTION, GOLD |
| `Particle` | 粒子效果 | x, y, char, style, life, dx, dy |
| `FloatingText` | 浮动文字（伤害数字） | x, y, text, style, life |
| `Enemy` | 敌人实体 | enemy_type, name, x, y, hp, atk, exp, gold |
| `Player` | 玩家实体 | x, y, hp, max_hp, atk, level, exp, gold |
| `Upgrade` | 升级选项 | name, desc, effect, rarity, icon |

### 核心类

#### 1. CommandHandler (命令处理器)
位置: 第 196-354 行

处理游戏内命令输入（按 `/` 进入命令模式）。

**命令列表**:
- `help`, `h` - 显示帮助
- `quit`, `q` - 退出游戏
- `fps [10-60]` - 设置帧率
- `light [on|off]` - 开关光照
- `particle [on|off]` - 开关粒子
- `char [角色名]` - 切换角色
- `config` - 显示当前配置
- **调试命令**: `heal`, `level`, `gold`, `god`, `killall`, `next`

#### 2. Game (游戏主逻辑)
位置: 第 357-784 行

游戏的核心类，包含:
- **地图生成** (`init_map()`) - 随机生成地图、敌人、物品
- **游戏状态** (`state`) - "playing", "upgrading", "game_over"
- **战斗系统** (`attack()`, `enemy_attack()`)
- **升级系统** (`get_upgrades()`, `apply_upgrade()`)
- **粒子系统** (`spawn_particles()`)
- **光照系统** (`update_light()`)

#### 3. InputHandler (输入处理)
位置: 第 787-822 行

使用 `termios` + `select` 实现非阻塞输入，支持:
- 方向键 (UP/DOWN/LEFT/RIGHT)
- WASD 按键
- TAB 自动补全
- 特殊键处理

### 渲染系统

所有渲染函数使用 Rich 库的组件:

| 函数 | 功能 | 位置 |
|------|------|------|
| `render_map()` | 渲染游戏地图（含光照、粒子、浮动文字） | 840-899 |
| `create_stats()` | 玩家状态面板 | 902-925 |
| `create_legend_panel()` | 图例说明面板 | 928-958 |
| `create_log()` | 消息日志面板 | 961-984 |
| `create_help_panel()` | 帮助面板 | 987-998 |
| `create_upgrade()` | 升级选择界面 | 1001-1020 |
| `create_gameover()` | 游戏结束界面 | 1023-1038 |

渲染使用 `rich.live.Live` 实现无闪烁刷新（第 1120 行）。

## 游戏机制

### 角色系统
4 种可选角色（代码第 56-61 行），各有不同的初始属性:

| 角色 | 图标 | HP | ATK | DEF | CRT | LS | REG | 特点 |
|------|------|-----|-----|-----|-----|-----|-----|------|
| `default` | ♛ | 100 | 10 | 0 | 0% | 0% | 0 | 平衡型 |
| `mage` | ⚚ | 80 | 15 | 0 | 10% | 0% | 1 | 高攻低防 |
| `rogue` | ⚔ | 85 | 12 | 0 | 20% | 5% | 0 | 暴击型 |
| `paladin` | ⚕ | 130 | 8 | 2 | 0% | 0% | 1 | 坦克型 |

**属性说明**: HP=生命值, ATK=攻击力, DEF=防御, CRT=暴击率, LS=生命偷取, REG=生命恢复

### 敌人类型
5 种敌人，随层数递增解锁（代码第 411-417 行）:
| 类型 | 名称 | 特点 |
|------|------|------|
| enemy_slime | 史莱姆 | 最弱，前期出现 |
| enemy_goblin | 哥布林 | 平衡型 |
| enemy_skeleton | 骷髅 | 攻击力高 |
| enemy_orc | 兽人 | 生命值高 |
| enemy_shadow | 暗影 | 后期强敌 |

敌人属性随层数缩放 (`scale = 1 + (floor - 1) * 0.15`)

### 升级系统 (Roguelike)
12 种升级选项，分 4 个稀有度（代码第 500-607 行）:

| 稀有度 | 权重 | 升级项 |
|--------|------|--------|
| 普通 (common) | 50 | 生命强化, 攻击强化, 生命恢复, 铁皮 |
| 稀有 (rare) | 30 | 生命偷取, 暴击, 狂战士, 泰坦 |
| 史诗 (epic) | 15 | 吸血鬼, 狂怒 |
| 传说 (legendary) | 5 | 不朽, 毁灭者 |

每次升级时从加权池中随机抽取 3 个选项供玩家选择。

### 属性系统
- **HP** - 生命值
- **ATK** - 攻击力
- **DEF** - 防御（减伤，使用边际递减公式）
- **REG** - 生命恢复（每回合）
- **LS** - 生命偷取百分比
- **CRT** - 暴击几率百分比

**防御公式**: `dmg = max(1, int(atk * (1 - DEF/(DEF+10))))`
- 防御有边际递减效果，永远不会完全无敌
- 10点防御约减伤50%，20点约减伤67%

### 商店系统
按 `B` 键或输入 `/shop` 命令打开商店界面。

**商品列表**:

| 物品 | 图标 | 价格 | 效果 |
|------|------|------|------|
| 生命药水 | ♥ | 20G | 恢复 30 HP |
| 力量卷轴 | ⚔ | 50G | 攻击力 +2 |
| 体质卷轴 | ♥ | 50G | 最大生命 +20 |
| 铁皮药剂 | 🛡 | 40G | 防御 +1 |
| 狂暴卷轴 | ⚡ | 60G | 暴击率 +10% |

商店每次随机显示 3-5 件商品。

### 地图元素
- `█` 墙壁 - 不可通过
- `·` 空地 - 可行走
- `♥` 血瓶 - 恢复 30 HP
- `◆` 金币 - 获得 5-15 金币
- `⌂` 出口 - 进入下一层

## 开发指南

### 添加新敌人
在 `Game.spawn_enemies()` 方法中修改敌人类型列表（第 411-417 行）:
```python
enemy_types = [
    ("enemy_slime", "史莱姆", 15, 5, 10, 5),      # (类型, 名称, HP, ATK, EXP, 金币)
    # 添加新敌人...
]
```

并在 `GAME_ASSETS` 中添加对应资源定义（第 39-54 行）。

### 添加新升级
在 `Game.get_upgrades()` 的 `pool` 列表中添加新的 `Upgrade` 对象（第 501-602 行）:
```python
Upgrade(
    "升级名称",
    "效果描述",
    lambda p: setattr(p, "属性名", p.属性名 + 增加值),
    "稀有度",  # common/rare/epic/legendary
    "图标",    # 单字符或 emoji
)
```

### 添加商店商品
在 `Shop.ITEMS` 列表中添加新的 `ShopItem` 对象（第 179-193 行）:
```python
ShopItem(
    "商品名称",
    "效果描述",
    价格,
    "图标",
    lambda p: 效果函数,
    是否一次性  # True=可重复购买, False=只能买一次
)
```

### 添加新命令
在 `CommandHandler.COMMANDS` 字典中添加命令说明（第 197-214 行），然后在 `execute()` 方法中添加处理逻辑（第 231-251 行）。

### 修改地图大小
修改 `CONFIG.map_width` 和 `CONFIG.map_height`（第 29-30 行），注意终端需要足够大以显示完整地图。

## 关键实现细节

### 1. 游戏循环
使用固定时步（fixed timestep）游戏循环（第 1119-1129 行）:
```python
frame_time = 1.0 / CONFIG.fps
with Live(console=console, refresh_per_second=CONFIG.fps, screen=True) as live:
    while game.running:
        # 控制帧率
        elapsed = time.time() - last
        if elapsed < frame_time:
            time.sleep(frame_time - elapsed)
        # 更新和渲染...
```

### 2. 非阻塞输入
使用 `select.select()` 检查 stdin 是否有输入（第 802-822 行），这样动画可以在等待输入时继续播放。

### 3. 粒子系统
简单的粒子系统（第 72-88 行），每个粒子有:
- 位置和速度
- 重力影响
- 生命周期
- 粒子数量上限控制 (`CONFIG.particle_limit`)

### 4. 光照系统
基于距离的光照计算（第 461-476 行）:
```python
dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
if dist <= view_distance:
    light = max(0.5, 1.0 - (dist / view_distance) * 0.4)
```

### 5. 状态机
游戏使用简单的状态字符串管理状态:
- `"playing"` - 正常游戏
- `"upgrading"` - 升级选择界面
- `"game_over"` - 游戏结束

## 文件编码和风格

- **编码**: UTF-8（必须，因为使用大量 Unicode 字符）
- **缩进**: 4 个空格
- **字符串引号**: 双引号为主
- **中文**: 代码中使用中文变量名和注释
- **类型注解**: 使用 Python 类型注解 (typing 模块)

## 测试和调试

### 调试命令
游戏内置多个调试命令（按 `/` 后输入）:
- `/god` - 无敌模式（9999 HP, 999 ATK）
- `/heal [数值]` - 恢复生命
- `/killall` - 消灭所有敌人
- `/next` - 直接进入下一层
- `/level [数值]` - 设置等级

### 性能调优
如果游戏卡顿，可以:
1. 降低 `CONFIG.fps`（建议 15-20）
2. 降低 `CONFIG.particle_limit`（建议 20-50）
3. 关闭光照: `--no-light` 或 `/light off`
4. 关闭粒子: `--no-particle` 或 `/particle off`

## 注意事项

1. **单文件限制**: 由于所有代码在一个文件中，修改时要注意不要破坏依赖顺序
2. **终端兼容性**: 使用 `termios` 和 `tty`，仅在类 Unix 系统（Linux/macOS）上测试过
3. **Rich 版本**: 确保 Rich 库版本足够新以支持所有功能
4. **Unicode 支持**: 终端必须支持 Unicode 字符以正确显示游戏画面

---

*最后更新: 2026-04-10*
