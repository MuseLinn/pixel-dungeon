# 🎮 PowerShell 启动指南

Pixel Dungeon 现在提供了功能完善的 PowerShell 启动脚本，为 Windows 用户提供更好的游戏体验。

## 📋 前置要求

- Windows PowerShell 5.1+ 或 PowerShell Core 7.0+
- Python 3.7+
- Rich 库 (`pip install rich`)

## 🚀 使用方法

### 方式1: 完整功能启动器 (推荐)

```powershell
.\Start-Dungeon.ps1
```

这个脚本提供：
- ✅ 环境自动检测
- ✅ 依赖自动安装
- ✅ 终端大小检查
- ✅ 美观的启动界面
- ✅ 游戏控制说明

**参数选项**:
```powershell
# 基本用法
.\Start-Dungeon.ps1

# 选择角色
.\Start-Dungeon.ps1 -Character mage

# 设置帧率
.\Start-Dungeon.ps1 -Fps 60

# 关闭特效
.\Start-Dungeon.ps1 -NoLight -NoParticle

# 使用 TUI 启动器
.\Start-Dungeon.ps1 -UseLauncher

# 组合参数
.\Start-Dungeon.ps1 -Character rogue -Fps 60 -NoParticle
```

### 方式2: 快速启动

```powershell
.\dungeon.ps1
```

快速启动版本，直接运行游戏，适合已知环境配置正确的用户。

```powershell
# 带参数
.\dungeon.ps1 --char paladin --fps 45
```

### 方式3: 传统批处理

```powershell
# 如果更喜欢 CMD 风格
.\start_dungeon.bat
```

## 🎯 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `-Fps` | int | 30 | 游戏帧率 (10-60) |
| `-NoLight` | switch | $false | 关闭光照效果 |
| `-NoParticle` | switch | $false | 关闭粒子效果 |
| `-Character` | string | "default" | 角色: default/mage/rogue/paladin |
| `-SkipTitle` | switch | $false | 跳过标题画面 |
| `-UseLauncher` | switch | $false | 使用 TUI 启动器 |

## 🛠️ PowerShell 执行策略

如果无法运行脚本，可能需要调整执行策略：

```powershell
# 查看当前策略
Get-ExecutionPolicy

# 临时允许当前会话运行脚本（推荐）
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# 然后运行游戏
.\Start-Dungeon.ps1

# 或者为当前用户永久设置（需要管理员权限）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 🔧 故障排除

### 问题1: "无法加载文件，因为在此系统上禁止运行脚本"

**解决方案**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\Start-Dungeon.ps1
```

### 问题2: Python 未找到

**解决方案**:
确保 Python 已添加到系统 PATH：
```powershell
# 检查 Python 位置
Get-Command python
Get-Command python3

# 如果都未找到，需要安装 Python 并添加到 PATH
# 或使用完整路径
C:\Python39\python .\run_game.py
```

### 问题3: Rich 库安装失败

**解决方案**:
```powershell
# 手动安装
pip install rich

# 或使用 Python3
pip3 install rich

# 或使用 Python -m
python -m pip install rich
```

### 问题4: 终端显示乱码

**解决方案**:
脚本已自动设置 UTF-8 编码，如果仍有问题：
```powershell
# 临时设置代码页为 UTF-8
chcp 65001

# 设置控制台字体为支持 Unicode 的字体（如 Cascadia Code、Consolas）
```

## 🎨 特色功能

### 智能环境检测
脚本会自动检测：
- ✅ Python 版本（需要 3.7+）
- ✅ Rich 库安装状态
- ✅ 终端大小是否合适

### 自动依赖安装
如果 Rich 库未安装，脚本会询问是否自动安装。

### 美观的启动界面
```
  ██████╗ ██╗  ██╗██╗███████╗███████╗██╗
  ██╔══██╗╚██╗██╔╝██║██╔════╝██╔════╝██║
  ██████╔╝ ╚███╔╝ ██║█████╗  █████╗  ██║
  ...

              P I X E L   D U N G E O N
                   像素地牢 v1.0
```

### 游戏控制说明
启动时自动显示控制说明，方便新手快速上手。

## 📊 对比

| 功能 | Start-Dungeon.ps1 | dungeon.ps1 | start_dungeon.bat |
|------|-------------------|-------------|-------------------|
| 环境检测 | ✅ 完整 | ❌ 无 | ⚠️ 基础 |
| 自动安装 | ✅ 支持 | ❌ 不支持 | ❌ 不支持 |
| 启动界面 | ✅ 美观 | ❌ 无 | ⚠️ 简单 |
| 参数支持 | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| 速度 | ⚠️ 稍慢 | ✅ 快速 | ✅ 快速 |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 💡 使用建议

- **首次运行**: 使用 `Start-Dungeon.ps1` 进行环境检查
- **日常使用**: 使用 `dungeon.ps1` 快速启动
- **自动化**: 使用 `start_dungeon.bat` 兼容性最好

## 🔗 相关文件

- `Start-Dungeon.ps1` - 完整功能 PowerShell 脚本
- `dungeon.ps1` - 快速启动版本
- `start_dungeon.bat` - Windows 批处理脚本
- `launcher.py` - Python TUI 启动器
- `run_game.py` - Python 游戏启动器

---

**祝你游戏愉快！** 🎮✨
