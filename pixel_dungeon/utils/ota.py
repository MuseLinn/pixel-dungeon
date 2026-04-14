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


def check_update_available() -> tuple[bool, str]:
    latest = get_latest_version()
    if latest:
        tag, _ = latest
        if tag != VERSION:
            return True, tag
        return False, VERSION

    root = Path(__file__).parent.parent.parent.resolve()
    if not is_git_repo(root):
        return False, VERSION

    try:
        subprocess.run(
            ["git", "fetch", "origin", "master"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
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
            if local.stdout.strip() != remote.stdout.strip():
                return True, "master"
    except Exception:
        pass

    return False, VERSION


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
    from .i18n import _

    root = Path(__file__).parent.parent.parent.resolve()
    if not is_git_repo(root):
        return False, _("not_git_repo")

    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin", "master"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if fetch.returncode != 0:
            return False, _("cannot_connect_server")

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
                return True, _("latest_version", VERSION)

        ok, msg = update_via_git(root)
        if ok:
            if (
                "already up to date" in msg.lower()
                or "already up-to-date" in msg.lower()
            ):
                return True, _("latest_version", VERSION)
            return True, _("updated_restart")
        return False, _("update_failed", msg)
    except Exception as e:
        return False, _("update_failed", e)


def uninstall() -> tuple[bool, str]:
    from .i18n import _
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
        messages.append(_("deleted", install_dir))
    else:
        messages.append(_("install_dir_not_exist"))

    if wrapper.exists():
        wrapper.unlink()
        messages.append(_("deleted_launcher", wrapper))

    for rc in [Path.home() / ".bashrc", Path.home() / ".zshrc"]:
        if rc.exists():
            content = rc.read_text(encoding="utf-8")
            new_content = "\n".join(
                line for line in content.splitlines() if "pixel-dungeon" not in line
            )
            if new_content != content:
                rc.write_text(new_content, encoding="utf-8")
                messages.append(_("cleaned_rc", rc))

    return True, "\n".join(messages)


def get_version() -> str:
    return VERSION
