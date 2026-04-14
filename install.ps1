$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/MuseLinn/pixel-dungeon.git"
$InstallDir = if ($env:PIXEL_DUNGEON_HOME) { $env:PIXEL_DUNGEON_HOME } else { Join-Path $env:LOCALAPPDATA "pixel-dungeon" }
$BinDir = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
$Wrapper = Join-Path $BinDir "pixel-dungeon.bat"

Write-Host "==> 安装 Pixel Dungeon 到 $InstallDir"

if (Test-Path $InstallDir) {
    Write-Host "==> 目录已存在，执行更新 (git pull)..."
    Set-Location $InstallDir
    git pull origin master
} else {
    $Parent = Split-Path $InstallDir -Parent
    if (!(Test-Path $Parent)) { New-Item -ItemType Directory -Path $Parent -Force | Out-Null }
    git clone $RepoUrl $InstallDir
}

Write-Host "==> 创建启动器..."
if (!(Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }

$BatchContent = @"
@echo off
set PIXEL_DUNGEON_HOME=$InstallDir
cd /d "%PIXEL_DUNGEON_HOME%"
if /I "%1"=="update" (
    python3 pixel_dungeon.py --update %*
) else if /I "%1"=="uninstall" (
    python3 pixel_dungeon.py --uninstall %*
) else (
    python3 pixel_dungeon.py %*
)
"@
Set-Content -Path $Wrapper -Value $BatchContent -Encoding ASCII

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$BinDir*") {
    Write-Host "==> 添加 $BinDir 到用户 PATH..."
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", "User")
    $env:Path += ";$BinDir"
}

Write-Host "==> 安装完成！"
Write-Host "   启动命令: pixel-dungeon"
Write-Host "   安装目录: $InstallDir"
