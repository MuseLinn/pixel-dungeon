"""跨平台输入处理模块
支持 Windows (msvcrt) 和 Unix (termios/tty/select)
"""

import sys
import os

# 检测操作系统
_IS_WINDOWS = os.name == "nt"
_IS_POSIX = os.name == "posix"

if _IS_WINDOWS:
    # Windows 平台使用 msvcrt
    import msvcrt
    import time
else:
    # Unix 平台使用 termios/tty/select
    try:
        import termios
        import tty
        import select

        _HAS_TERMIOS = True
    except ImportError:
        _HAS_TERMIOS = False


class CrossPlatformInputHandler:
    """跨平台输入处理器"""

    def __init__(self):
        self._old_settings = None
        self._is_windows = _IS_WINDOWS
        self._has_termios = _HAS_TERMIOS if not _IS_WINDOWS else False

    def start(self):
        """启动输入处理模式"""
        if self._is_windows:
            pass
        elif self._has_termios:
            try:
                self._old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
                sys.stdout.write("\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1006l")
                sys.stdout.flush()
            except:
                pass

    def stop(self):
        """停止输入处理模式"""
        if self._is_windows:
            # Windows 不需要特殊清理
            pass
        elif self._has_termios and self._old_settings:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)
            except:
                pass

    def get_key(self):
        """获取按键输入（非阻塞）"""
        if self._is_windows:
            return self._get_key_windows()
        else:
            return self._get_key_unix()

    def _get_key_windows(self):
        """Windows 平台获取按键"""
        if msvcrt.kbhit():
            key = msvcrt.getch()

            # 处理特殊键（方向键等）
            if key == b"\x00" or key == b"\xe0":
                # 功能键前缀
                seq = msvcrt.getch()
                key_map = {
                    b"H": "UP",
                    b"P": "DOWN",
                    b"K": "LEFT",
                    b"M": "RIGHT",
                }
                return key_map.get(seq, None)

            # 处理普通按键
            key_str = key.decode("utf-8", errors="ignore")

            # 映射特殊字符
            special_map = {
                "\r": "\r",  # Enter
                "\x08": "\x7f",  # Backspace
                "\x09": "TAB",  # Tab
                "\x1b": "\x1b",  # Escape
                "\x10": "\x10",  # Ctrl+P (命令面板)
                "\x18": "\x18",  # Ctrl+X (命令模式)
            }

            return special_map.get(key_str, key_str)
        return None

    def _get_key_unix(self):
        if not self._has_termios:
            return None

        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == "\x1b":
                if select.select([sys.stdin], [], [], 0)[0]:
                    next_char = sys.stdin.read(1)
                    if next_char == "M":
                        sys.stdin.read(3) if select.select([sys.stdin], [], [], 0)[
                            0
                        ] else None
                        return None
                    if next_char == "<":
                        while select.select([sys.stdin], [], [], 0)[0]:
                            c = sys.stdin.read(1)
                            if c in ("m", "M"):
                                break
                        return None
                    seq = next_char
                    if select.select([sys.stdin], [], [], 0)[0]:
                        seq += sys.stdin.read(1)
                    if seq == "[A":
                        return "UP"
                    if seq == "[B":
                        return "DOWN"
                    if seq == "[C":
                        return "RIGHT"
                    if seq == "[D":
                        return "LEFT"
            if key == "\t":
                return "TAB"
            return key
        return None


# 保持向后兼容的别名
InputHandler = CrossPlatformInputHandler
