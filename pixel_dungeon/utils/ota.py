#!/usr/bin/env python3
"""OTA 更新模块"""

import json
import os
import subprocess
import urllib.request
from pathlib import Path

VERSION = "1.1.0"
REPO = "muselinn/pixel-dungeon"
GITHUB_API = f"https://api.github.com/repos/{REPO}/releases/latest"


def get_latest_version() -> tuple[str, str] | None:
    try:
        req = urllib.request.Request(
            GITHUB_API,
            headers={"User-Agent": "pixel-dungeon-ota"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        tag = data.get("tag_name", VERSION)
        zip_url = data.get("zipball_url", "")
        return tag, zip_url
    except Exception:
        return None


def is_git_repo(path: Path) -> bool:
    return (path / ".git").is_dir()


def update_via_git(path: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "master"],
            cwd=str(path),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_and_update() -> tuple[bool, str]:
    root = Path(__file__).parent.parent.parent.resolve()
    if not is_git_repo(root):
        return False, "暂不支持非 Git 仓库的自动更新，请手动下载新版本"

    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "master"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if fetch.returncode != 0:
            return False, "无法连接到更新服务器"

        local = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        remote = subprocess.run(
            ["git", "rev-parse", "origin/master"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if local.returncode == 0 and remote.returncode == 0:
            if local.stdout.strip() == remote.stdout.strip():
                return True, f"当前已是最新版本 {VERSION}"

        ok, msg = update_via_git(root)
        if ok:
            if (
                "already up to date" in msg.lower()
                or "already up-to-date" in msg.lower()
            ):
                return True, f"当前已是最新版本 {VERSION}"
            return True, "已更新到最新版本，请重启游戏"
        return False, f"更新失败: {msg}"
    except Exception as e:
        return False, f"更新失败: {e}"


def uninstall() -> tuple[bool, str]:
    import shutil
    import platform

    install_dir = Path.home() / ".local" / "share" / "pixel-dungeon"
    if platform.system() == "Windows":
        install_dir = (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "pixel-dungeon"
        )
        bin_dir = (
            Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            / "Microsoft"
            / "WindowsApps"
        )
        wrapper = bin_dir / "pixel-dungeon.bat"
    else:
        bin_dir = Path.home() / ".local" / "bin"
        wrapper = bin_dir / "pixel-dungeon"

    messages = []
    if install_dir.exists():
        shutil.rmtree(install_dir)
        messages.append(f"已删除 {install_dir}")
    else:
        messages.append("安装目录不存在")

    if wrapper.exists():
        wrapper.unlink()
        messages.append(f"已删除启动器 {wrapper}")

    for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
        if rc.exists():
            content = rc.read_text(encoding="utf-8")
            new_content = "\n".join(
                line for line in content.splitlines() if "pixel-dungeon" not in line
            )
            if new_content != content:
                rc.write_text(new_content, encoding="utf-8")
                messages.append(f"已清理 {rc}")

    return True, "\n".join(messages)


def get_version() -> str:
    return VERSION
