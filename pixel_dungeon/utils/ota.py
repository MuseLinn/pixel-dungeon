#!/usr/bin/env python3
"""OTA 更新模块"""

import json
import os
import subprocess
import urllib.request
from pathlib import Path

VERSION = "1.0.0"
REPO = "MuseLinn/pixel-dungeon"
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
    latest = get_latest_version()
    if latest is None:
        return False, "无法连接到更新服务器"

    latest_ver, _ = latest
    if latest_ver == VERSION:
        return True, f"当前已是最新版本 {VERSION}"

    root = Path(__file__).parent.parent.parent.resolve()
    if is_git_repo(root):
        ok, msg = update_via_git(root)
        if ok:
            return True, f"已更新到 {latest_ver}，请重启游戏"
        return False, f"更新失败: {msg}"

    return False, "暂不支持非 Git 仓库的自动更新，请手动下载新版本"


def get_version() -> str:
    return VERSION
