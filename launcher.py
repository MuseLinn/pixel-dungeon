#!/usr/bin/env python3
"""
🎮 Pixel Dungeon 现代化启动器
统一的TUI界面，整合环境检查和游戏启动
"""

import sys
import subprocess
import os
import shutil
from typing import Tuple, Optional

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()


class Launcher:
    def __init__(self):
        self.checks = {
            "python": {"status": "pending", "message": "检查中...", "detail": ""},
            "rich": {"status": "pending", "message": "检查中...", "detail": ""},
            "terminal": {"status": "pending", "message": "检查中...", "detail": ""},
        }
        self.all_passed = False
        
    def get_status_icon(self, status: str) -> Tuple[str, str]:
        """获取状态图标和颜色"""
        icons = {
            "pending": ("◌", "dim"),
            "checking": ("◐", "yellow"),
            "success": ("✓", "green"),
            "warning": ("⚠", "yellow"),
            "error": ("✗", "red"),
        }
        return icons.get(status, ("?", "white"))
    
    def create_check_panel(self) -> Panel:
        """创建检查状态面板"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(width=3)
        table.add_column(width=12)
        table.add_column()
        
        for name, check in self.checks.items():
            icon, color = self.get_status_icon(check["status"])
            name_display = {
                "python": "Python",
                "rich": "Rich 库",
                "terminal": "终端",
            }.get(name, name)
            
            table.add_row(
                f"[{color}]{icon}[/{color}]",
                f"[bold]{name_display}[/bold]",
                check["message"]
            )
            if check["detail"]:
                table.add_row("", "", f"[dim]{check['detail']}[/dim]")
        
        return Panel(
            table,
            title="[bold cyan]环境检查[/bold cyan]",
            border_style="cyan",
            box=box.ROUNDED,
            height=12,
        )
    
    def create_info_panel(self) -> Panel:
        """创建信息面板"""
        text = Text()
        text.append("控制方式\n", style="bold yellow")
        text.append("  ")
        text.append("WASD", style="bold white on dark_blue")
        text.append(" 移动攻击  ")
        text.append("空格", style="bold white on dark_blue")
        text.append(" 等待恢复\n")
        text.append("  ")
        text.append("B", style="bold white on dark_blue")
        text.append(" 打开商店  ")
        text.append("P", style="bold white on dark_blue")
        text.append(" 暂停游戏  ")
        text.append("Q", style="bold white on dark_blue")
        text.append(" 退出\n\n")
        
        text.append("命令模式\n", style="bold yellow")
        text.append("  ")
        text.append("/", style="bold white on dark_blue")
        text.append(" 进入命令  ")
        text.append("/shop", style="dim")
        text.append(" 商店  ")
        text.append("/help", style="dim")
        text.append(" 帮助\n\n")
        
        text.append("CLI 参数\n", style="bold yellow")
        text.append("  ")
        text.append("--fps 30", style="dim cyan")
        text.append(" 设置帧率  ")
        text.append("--char mage", style="dim cyan")
        text.append(" 选择角色")
        
        return Panel(
            text,
            title="[bold yellow]游戏指南[/bold yellow]",
            border_style="yellow",
            box=box.ROUNDED,
            height=12,
        )
    
    def create_action_panel(self) -> Panel:
        """创建操作提示面板"""
        if self.all_passed:
            text = Text()
            text.append("✅ 环境检查通过！\n\n", style="bold green")
            text.append("按 ", style="dim")
            text.append("Enter", style="bold yellow")
            text.append(" 启动游戏", style="dim")
            border_style = "green"
        else:
            text = Text()
            text.append("⏳ 正在检查环境...\n\n", style="dim")
            text.append("请稍候", style="dim")
            border_style = "cyan"
        
        return Panel(
            Align.center(text, vertical="middle"),
            border_style=border_style,
            box=box.ROUNDED,
            height=6,
        )
    
    def render(self) -> Layout:
        """渲染启动器界面"""
        main_layout = Layout()
        
        # Logo区域
        logo_text = Text()
        logo_text.append("\n")
        logo_text.append("  ██████╗ ██╗  ██╗██╗███████╗███████╗██╗     \n", style="cyan")
        logo_text.append("  ██╔══██╗╚██╗██╔╝██║██╔════╝██╔════╝██║     \n", style="cyan")
        logo_text.append("  ██████╔╝ ╚███╔╝ ██║█████╗  █████╗  ██║     \n", style="cyan")
        logo_text.append("  ██╔═══╝  ██╔██╗ ██║██╔══╝  ██╔══╝  ██║     \n", style="cyan")
        logo_text.append("  ██║     ██╔╝ ██╗██║██║     ██║     ███████╗\n", style="cyan")
        logo_text.append("  ╚═╝     ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝     ╚══════╝\n", style="cyan")
        logo_text.append("\n")
        logo_text.append("              P I X E L   D U N G E O N              \n", style="bold cyan")
        logo_text.append("                   像素地牢 v1.0                     \n", style="dim cyan")
        
        logo_panel = Panel(
            Align.center(logo_text),
            border_style="cyan",
            box=box.DOUBLE,
            height=11,
        )
        
        # 中间区域
        middle = Layout()
        middle.split_row(
            Layout(self.create_check_panel(), ratio=1),
            Layout(self.create_info_panel(), ratio=1),
        )
        
        # 底部操作区
        bottom = Layout(self.create_action_panel())
        
        main_layout.split_column(
            Layout(logo_panel, size=11),
            Layout(middle, size=12),
            Layout(bottom, size=6),
        )
        
        return main_layout
    
    def check_python(self) -> bool:
        """检查Python版本"""
        self.checks["python"]["status"] = "checking"
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version >= (3, 7):
            self.checks["python"]["status"] = "success"
            self.checks["python"]["message"] = f"版本 {version_str}"
            self.checks["python"]["detail"] = "✓ 满足要求 (>= 3.7)"
            return True
        else:
            self.checks["python"]["status"] = "error"
            self.checks["python"]["message"] = f"版本 {version_str}"
            self.checks["python"]["detail"] = "✗ 需要 >= 3.7"
            return False
    
    def check_rich(self) -> bool:
        """检查Rich库"""
        self.checks["rich"]["status"] = "checking"
        
        try:
            import rich
            try:
                version = rich.__version__
            except AttributeError:
                version = "未知"
            self.checks["rich"]["status"] = "success"
            self.checks["rich"]["message"] = f"已安装 v{version}"
            self.checks["rich"]["detail"] = "✓ TUI渲染库就绪"
            return True
        except ImportError:
            self.checks["rich"]["status"] = "error"
            self.checks["rich"]["message"] = "未安装"
            self.checks["rich"]["detail"] = "必需依赖，需要安装"
            return False
    
    def install_rich(self) -> bool:
        """安装Rich库"""
        self.checks["rich"]["status"] = "checking"
        self.checks["rich"]["message"] = "正在安装..."
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # 重新加载以检测
            import importlib
            importlib.invalidate_caches()
            import rich
            try:
                version = rich.__version__
            except AttributeError:
                version = "未知"
            self.checks["rich"]["status"] = "success"
            self.checks["rich"]["message"] = f"已安装 v{version}"
            self.checks["rich"]["detail"] = "✓ 安装成功"
            return True
        except Exception as e:
            self.checks["rich"]["status"] = "error"
            self.checks["rich"]["message"] = "安装失败"
            self.checks["rich"]["detail"] = str(e)
            return False
    
    def check_terminal(self) -> bool:
        """检查终端"""
        self.checks["terminal"]["status"] = "checking"
        
        try:
            size = shutil.get_terminal_size()
            width, height = size.columns, size.lines
            
            if width >= 100 and height >= 35:
                self.checks["terminal"]["status"] = "success"
                self.checks["terminal"]["message"] = f"{width}x{height}"
                self.checks["terminal"]["detail"] = "✓ 推荐尺寸"
            elif width >= 80 and height >= 30:
                self.checks["terminal"]["status"] = "warning"
                self.checks["terminal"]["message"] = f"{width}x{height}"
                self.checks["terminal"]["detail"] = "⚠ 可用但建议更大"
            else:
                self.checks["terminal"]["status"] = "warning"
                self.checks["terminal"]["message"] = f"{width}x{height}"
                self.checks["terminal"]["detail"] = "⚠ 建议 100x35 以上"
            
            return True
        except:
            self.checks["terminal"]["status"] = "warning"
            self.checks["terminal"]["message"] = "无法检测"
            self.checks["terminal"]["detail"] = "⚠ 可能影响体验"
            return True
    
    def run_checks(self):
        """运行所有检查"""
        with Live(self.render(), refresh_per_second=10, screen=True) as live:
            # Python检查
            python_ok = self.check_python()
            live.update(self.render())
            time.sleep(0.3)
            
            # Rich检查
            rich_ok = self.check_rich()
            live.update(self.render())
            time.sleep(0.3)
            
            # 如果需要安装Rich
            if not rich_ok:
                self.checks["rich"]["message"] = "按 I 安装"
                self.checks["rich"]["detail"] = "或按 Q 退出"
                live.update(self.render())
                
                # 等待用户输入
                import termios
                import tty
                import select
                
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    while True:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1)
                            if key.lower() == 'i':
                                if self.install_rich():
                                    live.update(self.render())
                                    time.sleep(0.5)
                                    break
                                else:
                                    live.update(self.render())
                                    time.sleep(2)
                                    sys.exit(1)
                            elif key.lower() == 'q':
                                sys.exit(0)
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            # 终端检查
            self.check_terminal()
            live.update(self.render())
            time.sleep(0.3)
            
            # 检查是否全部通过
            self.all_passed = all(
                c["status"] in ("success", "warning") 
                for c in self.checks.values()
            )
            live.update(self.render())
            
            # 等待用户按键启动游戏
            if self.all_passed:
                import termios
                import tty
                import select
                
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    while True:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            key = sys.stdin.read(1)
                            if key == '\r' or key == '\n':  # Enter
                                return True
                            elif key.lower() == 'q':
                                sys.exit(0)
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            
            return False


def main():
    """主函数"""
    launcher = Launcher()
    
    try:
        if launcher.run_checks():
            console.clear()
            # 启动游戏
            script_dir = os.path.dirname(os.path.abspath(__file__))
            game_script = os.path.join(script_dir, "pixel_dungeon.py")
            
            if os.path.exists(game_script):
                # 传递所有参数给游戏
                os.execv(sys.executable, [sys.executable, game_script] + sys.argv[1:])
            else:
                console.print("[red]错误：未找到 pixel_dungeon.py[/red]")
                sys.exit(1)
    except KeyboardInterrupt:
        console.clear()
        console.print("[yellow]已取消[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    main()
