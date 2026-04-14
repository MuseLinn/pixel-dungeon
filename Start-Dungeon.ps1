#!/usr/bin/env powershell
<#
.SYNOPSIS
    🎮 Pixel Dungeon - 像素地牢 PowerShell 启动脚本

.DESCRIPTION
    自动检测环境、安装依赖并启动游戏的 PowerShell 脚本
    支持 Windows PowerShell 和 PowerShell Core

.PARAMETER Fps
    设置游戏帧率 (10-60)

.PARAMETER NoLight
    关闭光照效果

.PARAMETER NoParticle
    关闭粒子效果

.PARAMETER Character
    选择角色 (default/mage/rogue/paladin)

.PARAMETER SkipTitle
    跳过标题画面

.PARAMETER UseLauncher
    使用 TUI 启动器（默认直接启动游戏）

.EXAMPLE
    .\Start-Dungeon.ps1

.EXAMPLE
    .\Start-Dungeon.ps1 -Character mage -Fps 60

.EXAMPLE
    .\Start-Dungeon.ps1 -UseLauncher
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateRange(10, 60)]
    [int]$Fps = 30,

    [Parameter()]
    [switch]$NoLight,

    [Parameter()]
    [switch]$NoParticle,

    [Parameter()]
    [ValidateSet("default", "mage", "rogue", "paladin")]
    [string]$Character = "default",

    [Parameter()]
    [switch]$SkipTitle,

    [Parameter()]
    [switch]$UseLauncher
)

# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 获取脚本所在目录（兼容多种执行方式）
if ($PSScriptRoot) {
    $Script:ScriptDir = $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    $Script:ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $Script:ScriptDir = $PWD.Path
}

# 颜色定义
$Colors = @{
    Success = "Green"
    Error = "Red"
    Warning = "Yellow"
    Info = "Cyan"
    Dim = "Gray"
}

# 图标
$Icons = @{
    Check = "✓"
    Cross = "✗"
    Warning = "⚠"
    Info = "ℹ"
    Game = "🎮"
    Sword = "⚔"
}

function Write-StatusLine {
    param(
        [string]$Icon,
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Test-PythonInstalled {
    <#
    检查 Python 是否已安装
    #>
    try {
        $pythonVersion = python --version 2>&1
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]

            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 7)) {
                return @{
                    Installed = $true
                    Version = "$major.$minor"
                    Message = "Python $major.$minor"
                }
            } else {
                return @{
                    Installed = $false
                    Version = "$major.$minor"
                    Message = "需要 Python 3.7+，当前为 $major.$minor"
                }
            }
        }
    } catch {
        # 尝试 python3
        try {
            $pythonVersion = python3 --version 2>&1
            if ($pythonVersion -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                return @{
                    Installed = $true
                    Version = "$major.$minor"
                    Message = "Python $major.$minor"
                    Command = "python3"
                }
            }
        } catch {
            # 忽略错误
        }
    }

    return @{
        Installed = $false
        Version = $null
        Message = "未检测到 Python"
    }
}

function Test-RichInstalled {
    <#
    检查 Rich 库是否已安装
    #>
    try {
        $richVersion = python -c "import importlib.metadata; print(importlib.metadata.version('rich'))" 2>&1
        if ($LASTEXITCODE -eq 0) {
            return @{
                Installed = $true
                Version = $richVersion
                Message = "Rich $richVersion"
            }
        }
    } catch {
        # 尝试 python3
        try {
            $richVersion = python3 -c "import importlib.metadata; print(importlib.metadata.version('rich'))" 2>&1
            if ($LASTEXITCODE -eq 0) {
                return @{
                    Installed = $true
                    Version = $richVersion
                    Message = "Rich $richVersion"
                    Command = "python3"
                }
            }
        } catch {
            # 忽略错误
        }
    }

    return @{
        Installed = $false
        Version = $null
        Message = "未安装 Rich 库"
    }
}

function Install-RichLibrary {
    <#
    安装 Rich 库
    #>
    param([string]$PythonCmd = "python")

    Write-StatusLine -Icon $Icons.Info -Message "正在安装 Rich 库..." -Color $Colors.Info

    try {
        & $PythonCmd -m pip install rich -q 2>&1 | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-StatusLine -Icon $Icons.Check -Message "Rich 库安装成功！" -Color $Colors.Success
            return $true
        } else {
            Write-StatusLine -Icon $Icons.Cross -Message "Rich 库安装失败" -Color $Colors.Error
            return $false
        }
    } catch {
        Write-StatusLine -Icon $Icons.Cross -Message "安装过程出错: $_" -Color $Colors.Error
        return $false
    }
}

function Get-TerminalSize {
    <#
    获取终端大小
    #>
    try {
        $width = $Host.UI.RawUI.WindowSize.Width
        $height = $Host.UI.RawUI.WindowSize.Height
        return @{
            Width = $width
            Height = $height
            Recommended = ($width -ge 100 -and $height -ge 35)
        }
    } catch {
        return @{
            Width = 80
            Height = 24
            Recommended = $false
        }
    }
}

function Show-GameLogo {
    <#
    显示游戏 Logo
    #>
    Clear-Host
    Write-Host ""
    Write-Host "    ████  ████  ████  ████  ███   ███  ████   ████  ███  " -ForegroundColor Cyan
    Write-Host "    ██  ██  ██      ██  ██  ██  ██     ██  ██  ██ ██ " -ForegroundColor Cyan
    Write-Host "    ████  ██  ████  ████  ██ ██ ██  ███   ███  ██  ██" -ForegroundColor Cyan
    Write-Host "    ██  ██  ██      ██  ██  ██  ██     ██  ██ ██    " -ForegroundColor Cyan
    Write-Host "    ████  ████  ████  ██   ███   ███  ████   ████  ██  ██" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "              P I X E L   D U N G E O N              " -ForegroundColor Cyan -Bold
    Write-Host "                   像素地牢 v1.0                     " -ForegroundColor Gray
    Write-Host ""
}

function Show-EnvironmentCheck {
    <#
    显示环境检查结果
    #>
    param(
        [hashtable]$PythonCheck,
        [hashtable]$RichCheck,
        [hashtable]$TerminalInfo
    )

    Write-Host "┌─────────────────────────────────────────┐" -ForegroundColor Cyan
    Write-Host "│         🔍 环境检查                     │" -ForegroundColor Cyan
    Write-Host "├─────────────────────────────────────────┤" -ForegroundColor Cyan

    # Python 检查
    if ($PythonCheck.Installed) {
        Write-Host "│  $($Icons.Check) Python    $($PythonCheck.Message.PadRight(30))│" -ForegroundColor Green
    } else {
        Write-Host "│  $($Icons.Cross) Python    $($PythonCheck.Message.PadRight(30))│" -ForegroundColor Red
    }

    # Rich 检查
    if ($RichCheck.Installed) {
        Write-Host "│  $($Icons.Check) Rich 库   $($RichCheck.Message.PadRight(30))│" -ForegroundColor Green
    } else {
        Write-Host "│  $($Icons.Warning) Rich 库 $($RichCheck.Message.PadRight(30))│" -ForegroundColor Yellow
    }

    # 终端检查
    $terminalMsg = "$($TerminalInfo.Width)x$($TerminalInfo.Height)"
    if ($TerminalInfo.Recommended) {
        Write-Host "│  $($Icons.Check) 终端      $($terminalMsg.PadRight(30))│" -ForegroundColor Green
    } else {
        Write-Host "│  $($Icons.Warning) 终端    $($terminalMsg.PadRight(30))│" -ForegroundColor Yellow
    }

    Write-Host "└─────────────────────────────────────────┘" -ForegroundColor Cyan
    Write-Host ""
}

function Show-GameControls {
    <#
    显示游戏控制说明
    #>
    Write-Host "┌─────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "│         🎮 游戏控制                     │" -ForegroundColor Yellow
    Write-Host "├─────────────────────────────────────────┤" -ForegroundColor Yellow
    Write-Host "│  WASD / 方向键     移动和攻击          │" -ForegroundColor White
    Write-Host "│  空格              等待一回合          │" -ForegroundColor White
    Write-Host "│  B                 打开商店            │" -ForegroundColor White
    Write-Host "│  P                 暂停/继续           │" -ForegroundColor White
    Write-Host "│  /                 命令模式            │" -ForegroundColor White
    Write-Host "│  ?                 显示帮助            │" -ForegroundColor White
    Write-Host "│  Q                 退出游戏            │" -ForegroundColor White
    Write-Host "└─────────────────────────────────────────┘" -ForegroundColor Yellow
    Write-Host ""
}

function Start-Game {
    <#
    启动游戏
    #>
    param(
        [string]$PythonCmd = "python",
        [hashtable]$GameParams
    )

    Write-StatusLine -Icon $Icons.Game -Message "正在启动像素地牢..." -Color $Colors.Success
    Write-Host ""

    # 构建参数
    $arguments = @()

    if ($GameParams.Fps -ne 30) {
        $arguments += "--fps"
        $arguments += $GameParams.Fps
    }

    if ($GameParams.NoLight) {
        $arguments += "--no-light"
    }

    if ($GameParams.NoParticle) {
        $arguments += "--no-particle"
    }

    if ($GameParams.Character -ne "default") {
        $arguments += "--char"
        $arguments += $GameParams.Character
    }

    if ($GameParams.SkipTitle) {
        $arguments += "--skip-title"
    }

    # 确定要运行的脚本
    $gameScript = Join-Path $Script:ScriptDir "run_game.py"

    if (-not (Test-Path $gameScript)) {
        # 尝试旧版本
        $gameScript = Join-Path $Script:ScriptDir "pixel_dungeon.py"
    }

    if (Test-Path $gameScript) {
        try {
            & $PythonCmd $gameScript @arguments
        } catch {
            Write-StatusLine -Icon $Icons.Cross -Message "启动失败: $_" -Color $Colors.Error
            Read-Host "按 Enter 键退出"
        }
    } else {
        Write-StatusLine -Icon $Icons.Cross -Message "未找到游戏文件！" -Color $Colors.Error
        Write-Host "请确保 pixel_dungeon.py 或 run_game.py 在当前目录" -ForegroundColor $Colors.Dim
        Read-Host "按 Enter 键退出"
    }
}

function Start-WithLauncher {
    <#
    使用 TUI 启动器
    #>
    param([string]$PythonCmd = "python")

    $launcherScript = Join-Path $Script:ScriptDir "launcher.py"

    if (Test-Path $launcherScript) {
        Write-StatusLine -Icon $Icons.Game -Message "正在启动 TUI 启动器..." -Color $Colors.Success
        & $PythonCmd $launcherScript
    } else {
        Write-StatusLine -Icon $Icons.Cross -Message "未找到启动器 (launcher.py)" -Color $Colors.Error
        Write-Host "将直接启动游戏..." -ForegroundColor $Colors.Dim
        Start-Sleep -Seconds 1
        Start-Game -PythonCmd $PythonCmd -GameParams @{
            Fps = $Fps
            NoLight = $NoLight
            NoParticle = $NoParticle
            Character = $Character
            SkipTitle = $SkipTitle
        }
    }
}

# ============ 主程序 ============

# 显示 Logo
Show-GameLogo

# 环境检查
Write-StatusLine -Icon $Icons.Info -Message "正在检查环境..." -Color $Colors.Info
Write-Host ""

$pythonCheck = Test-PythonInstalled
$richCheck = Test-RichInstalled
$terminalInfo = Get-TerminalSize

# 确定 Python 命令
$pythonCmd = if ($pythonCheck.Command) { $pythonCheck.Command } else { "python" }

# 显示检查结果
Show-EnvironmentCheck -PythonCheck $pythonCheck -RichCheck $richCheck -TerminalInfo $terminalInfo

# 检查是否通过
if (-not $pythonCheck.Installed) {
    Write-StatusLine -Icon $Icons.Cross -Message "Python 未安装或版本过低！" -Color $Colors.Error
    Write-Host "请访问 https://www.python.org/downloads/ 下载 Python 3.7+" -ForegroundColor $Colors.Dim
    Read-Host "按 Enter 键退出"
    exit 1
}

# 如果需要安装 Rich
if (-not $richCheck.Installed) {
    Write-StatusLine -Icon $Icons.Warning -Message "需要安装 Rich 库" -Color $Colors.Warning
    Write-Host ""

    $install = Read-Host "是否现在安装 Rich 库? (Y/n)"

    if ($install -eq '' -or $install -eq 'Y' -or $install -eq 'y') {
        $installSuccess = Install-RichLibrary -PythonCmd $pythonCmd

        if (-not $installSuccess) {
            Write-Host ""
            Write-StatusLine -Icon $Icons.Cross -Message "安装失败，请手动运行: pip install rich" -Color $Colors.Error
            Read-Host "按 Enter 键退出"
            exit 1
        }

        Write-Host ""
    } else {
        Write-Host ""
        Write-StatusLine -Icon $Icons.Cross -Message "Rich 库是必需的，无法启动游戏" -Color $Colors.Error
        Read-Host "按 Enter 键退出"
        exit 1
    }
}

# 显示控制说明
Show-GameControls

# 延迟一下让用户看到信息
Start-Sleep -Seconds 1

# 启动游戏
if ($UseLauncher) {
    Start-WithLauncher -PythonCmd $pythonCmd
} else {
    Start-Game -PythonCmd $pythonCmd -GameParams @{
        Fps = $Fps
        NoLight = $NoLight
        NoParticle = $NoParticle
        Character = $Character
        SkipTitle = $SkipTitle
    }
}
