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


def _regenerate_launcher(install_dir: Path) -> tuple[bool, str]:
    import platform
    import sys

    try:
        if platform.system() == "Windows":
            bin_dir = (
                Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
                / "Microsoft"
                / "WindowsApps"
            )
            wrapper = bin_dir / "pixel-dungeon.bat"
            python_cmd = sys.executable or "python"
            batch_content = (
                f"@echo off\n"
                f"set PIXEL_DUNGEON_HOME={install_dir}\n"
                f'cd /d "%PIXEL_DUNGEON_HOME%"\n'
                f'if /I "%1"=="update" (\n'
                f"    {python_cmd} pixel_dungeon.py --update\n"
                f') else if /I "%1"=="uninstall" (\n'
                f"    {python_cmd} pixel_dungeon.py --uninstall\n"
                f") else (\n"
                f"    {python_cmd} pixel_dungeon.py %*\n"
                f")\n"
            )
            bin_dir.mkdir(parents=True, exist_ok=True)
            wrapper.write_text(batch_content, encoding="ascii")
        else:
            bin_dir = Path.home() / ".local" / "bin"
            wrapper = bin_dir / "pixel-dungeon"
            shell_content = (
                "#!/usr/bin/env bash\n"
                f'export PIXEL_DUNGEON_HOME="${{PIXEL_DUNGEON_HOME:-{install_dir}}}"\n'
                'cd "$PIXEL_DUNGEON_HOME"\n'
                'case "$1" in\n'
                "  update)\n"
                "    shift\n"
                '    python3 pixel_dungeon.py --update "$@"\n'
                "    ;;\n"
                "  uninstall)\n"
                "    shift\n"
                '    python3 pixel_dungeon.py --uninstall "$@"\n'
                "    ;;\n"
                "  *)\n"
                '    python3 pixel_dungeon.py "$@"\n'
                "    ;;\n"
                "esac\n"
            )
            bin_dir.mkdir(parents=True, exist_ok=True)
            wrapper.write_text(shell_content, encoding="utf-8")
            wrapper.chmod(0o755)
        return True, str(wrapper)
    except Exception as e:
        return False, str(e)


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
            lr_ok, lr_msg = _regenerate_launcher(root)
            lines = [_("updated_restart")]
            if lr_ok:
                lines.append(_("launcher_regenerated", lr_msg))
            else:
                lines.append(_("launcher_regen_failed", lr_msg))
            return True, "\n".join(lines)
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
