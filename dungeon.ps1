#!/usr/bin/env powershell
<#
.SYNOPSIS
    Pixel Dungeon 快速启动脚本

.DESCRIPTION
    简化的 PowerShell 启动脚本，直接启动游戏

.EXAMPLE
    .\dungeon.ps1

.EXAMPLE
    .\dungeon.ps1 --char mage --fps 60
#>

# 设置编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 获取脚本目录（兼容多种执行方式）
if ($PSScriptRoot) {
    $ScriptDir = $PSScriptRoot
} elseif ($MyInvocation.MyCommand.Path) {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
} else {
    $ScriptDir = $PWD.Path
}

# 检查 Python
$python = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

# 确定游戏脚本
$gameScript = Join-Path $ScriptDir "run_game.py"
if (-not (Test-Path $gameScript)) {
    $gameScript = Join-Path $ScriptDir "pixel_dungeon.py"
}

if (Test-Path $gameScript) {
    & $python $gameScript @args
} else {
    Write-Host "❌ 未找到游戏文件" -ForegroundColor Red
    Write-Host "请确保在正确的目录中运行此脚本" -ForegroundColor Gray
    Read-Host "按 Enter 键退出"
}
