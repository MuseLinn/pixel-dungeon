chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host "    ___ _         _   ___"
    Write-Host "   | _ (_)_ _____| | |   \ _  _ _ _  __ _ ___ ___ _ _"
    Write-Host "   |  _/ \ \ / -_) | | |) | || | ' \/ _` / -_) _ \ ' \"
    Write-Host "   |_| |_/_/_\___|_| |___/ \_,_|_||_\__, \___\___/_||_|"
    Write-Host "                                      |___/"
    Write-Host "              P I X E L   D U N G E O N"
    Write-Host "                   像素地牢"
    Write-Host ""
}

Show-Banner

Write-Host "==> 检查环境..."

function Test-Python {
    param([string]$Cmd)
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        return $null
    }
    try {
        $ver = & $Cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($ver -match '^\d+\.\d+$') {
            return $ver
        }
    } catch {}
    return $null
}

$PythonCmd = $null
$VersionStr = $null
foreach ($cmd in @("python3", "python", "py")) {
    $VersionStr = Test-Python $cmd
    if ($VersionStr) {
        $PythonCmd = $cmd
        break
    }
}

if (-not $PythonCmd) {
    Write-Error "错误: 未找到可用的 Python，请先安装 Python 3.7+"
    exit 1
}

$VersionParts = $VersionStr -split '\.'
$Major = [int]$VersionParts[0]
$Minor = [int]$VersionParts[1]

if ($Major -lt 3 -or ($Major -eq 3 -and $Minor -lt 7)) {
    Write-Error "错误: Python 版本过低 ($Major.$Minor)，需要 >= 3.7"
    exit 1
}

Write-Host "   Python: $Major.$Minor ($PythonCmd)"

try {
    & $PythonCmd -c "import rich" | Out-Null
    Write-Host "   rich: 已安装"
} catch {
    Write-Host "==> 安装依赖 rich..."
    & $PythonCmd -m pip install rich | Out-Null
    try {
        & $PythonCmd -c "import rich" | Out-Null
    } catch {
        Write-Error "错误: 无法自动安装 rich，请手动运行: pip install rich"
        exit 1
    }
}

$RepoUrlHttps = "https://github.com/muselinn/pixel-dungeon.git"
$RepoUrlSsh = "git@github.com:muselinn/pixel-dungeon.git"
$InstallDir = if ($env:PIXEL_DUNGEON_HOME) { $env:PIXEL_DUNGEON_HOME } else { Join-Path $env:LOCALAPPDATA "pixel-dungeon" }
$BinDir = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
$Wrapper = Join-Path $BinDir "pixel-dungeon.bat"

function Clone-Repo {
    param([string]$Url)
    $Parent = Split-Path $InstallDir -Parent
    if (!(Test-Path $Parent)) { New-Item -ItemType Directory -Path $Parent -Force | Out-Null }
    git clone $Url $InstallDir
    return $LASTEXITCODE
}

Write-Host "==> 安装 Pixel Dungeon 到 $InstallDir"

if (Test-Path $InstallDir) {
    Write-Host "==> 目录已存在，执行更新 (git pull)..."
    Push-Location
    Set-Location $InstallDir
    git pull origin master
    Pop-Location
    if ($LASTEXITCODE -ne 0) {
        Write-Error "错误: git pull 失败，请检查网络连接或 Git SSL 配置"
        exit 1
    }
} else {
    Write-Host "==> 尝试 HTTPS 克隆..."
    $cloneCode = Clone-Repo $RepoUrlHttps
    if ($cloneCode -ne 0) {
        Write-Host "==> HTTPS 失败，尝试 SSH 克隆..."
        $cloneCode = Clone-Repo $RepoUrlSsh
        if ($cloneCode -ne 0) {
            Write-Error "错误: git clone 失败。HTTPS 和 SSH 均不可用。`n建议: 1) 运行 'git config --global http.sslBackend openssl' 后重试; 2) 或手动下载 ZIP 解压到 $InstallDir"
            exit 1
        }
    }
}

if (-not (Test-Path $InstallDir)) {
    Write-Error "错误: 安装目录不存在，克隆似乎失败了"
    exit 1
}

Write-Host "==> 创建启动器..."
if (!(Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir -Force | Out-Null }

$BatchContent = @"
@echo off
set PIXEL_DUNGEON_HOME=$InstallDir
cd /d "%PIXEL_DUNGEON_HOME%"
if /I "%1"=="update" (
    $PythonCmd pixel_dungeon.py --update
) else if /I "%1"=="uninstall" (
    $PythonCmd pixel_dungeon.py --uninstall
) else (
    $PythonCmd pixel_dungeon.py %*
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
