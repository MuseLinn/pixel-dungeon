chcp 65001 > $null
$ErrorActionPreference = "Stop"

$InstallDir = if ($env:PIXEL_DUNGEON_HOME) { $env:PIXEL_DUNGEON_HOME } else { Join-Path $env:LOCALAPPDATA "pixel-dungeon" }
$BinDir = Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps"
$Wrapper = Join-Path $BinDir "pixel-dungeon.bat"

Write-Host "==> 卸载 Pixel Dungeon"

if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
    Write-Host "   已删除 $InstallDir"
} else {
    Write-Host "   安装目录不存在"
}

if (Test-Path $Wrapper) {
    Remove-Item -Force $Wrapper
    Write-Host "   已删除启动器 $Wrapper"
}

$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -like "*$BinDir*") {
    $NewPath = ($UserPath -split ';' | Where-Object { $_ -ne $BinDir }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "User")
    Write-Host "   已从 PATH 移除 $BinDir"
}

Write-Host "==> 卸载完成"
