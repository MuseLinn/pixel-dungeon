#!/usr/bin/env python3
import os
import sys
import time
import shutil

MIN_WIDTH = 80
MIN_HEIGHT = 24


def get_terminal_size():
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except Exception:
        return 0, 0


def check_python():
    return sys.version_info >= (3, 7)


def check_rich():
    try:
        import rich

        return True
    except ImportError:
        return False


def install_rich():
    try:
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "rich", "-q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return check_rich()
    except Exception:
        return False


def print_logo():
    logo = """
 ___ _         _   ___
| _ (_)_ _____| | |   \ _  _ _ _  __ _ ___ ___ _ _
|  _/ \ \ / -_) | | |) | || | ' \/ _` / -_) _ \ ' \
|_| |_/_/_\___|_| |___/ \_,_|_||_\__, \___\___/_||_|
                                 |___/

              P I X E L   D U N G E O N
                   像素地牢 v1.0
    """
    print(logo)


def spinner_animation(text, duration=1.5):
    import itertools
    import time

    spinner = itertools.cycle(["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"])
    start = time.time()
    while time.time() - start < duration:
        print(f"\r{next(spinner)} {text}", end="", flush=True)
        time.sleep(0.08)
    print(f"\r✓ {text}")


def main():
    width, height = get_terminal_size()

    if width < MIN_WIDTH or height < MIN_HEIGHT:
        print(f"❌ 终端尺寸不足: {width}x{height}")
        print(f"   像素地牢需要至少 {MIN_WIDTH}x{MIN_HEIGHT} 的终端分辨率")
        print("   请调整终端窗口大小后重试")
        sys.exit(1)

    if not check_python():
        print("❌ Python 版本过低，需要 3.7 或更高版本")
        sys.exit(1)

    print_logo()

    if not check_rich():
        print("⚠️  未检测到 Rich 库")
        spinner_animation("正在安装 Rich 库...", duration=3.0)
        if install_rich():
            print("✅ Rich 库安装完成")
        else:
            print("❌ Rich 库安装失败，请手动运行: pip install rich")
            sys.exit(1)
    else:
        from rich.console import Console

        console = Console()
        with console.status("[cyan]正在启动像素地牢...", spinner="dots"):
            time.sleep(0.8)

    print()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    game_script = os.path.join(script_dir, "pixel_dungeon.py")

    if os.path.exists(game_script):
        os.execv(sys.executable, [sys.executable, game_script] + sys.argv[1:])
    else:
        print("❌ 错误：未找到 pixel_dungeon.py")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 已退出")
        sys.exit(0)
