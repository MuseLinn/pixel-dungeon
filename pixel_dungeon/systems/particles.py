#!/usr/bin/env python3
"""粒子系统模块"""

from dataclasses import dataclass, field


@dataclass
class Particle:
    """粒子效果"""

    x: float
    y: float
    char: str
    style: str
    life: int
    dx: float = 0
    dy: float = 0
    grav: float = 0.02

    def update(self) -> bool:
        """更新粒子状态，返回是否存活"""
        self.x += self.dx
        self.y += self.dy
        self.dy += self.grav
        self.life -= 1
        return self.life > 0


@dataclass
class FloatingText:
    """浮动文字效果（伤害数字等）"""

    x: int
    y: int
    text: str
    style: str
    life: int
    max_life: int = field(default=0, repr=False)
    dy: float = field(default=-0.15, repr=False)

    def __post_init__(self):
        if self.max_life == 0:
            self.max_life = self.life

    def update(self) -> bool:
        """更新浮动文字，返回是否存活"""
        self.y += self.dy
        self.life -= 1
        return self.life > 0

    def get_alpha_style(self) -> str:
        """根据生命值返回带透明度的样式"""
        alpha = self.life / self.max_life if self.max_life > 0 else 1.0
        if alpha > 0.7:
            return f"bold {self.style}"
        elif alpha > 0.3:
            return self.style
        else:
            return f"dim {self.style}"


class ParticleSystem:
    """粒子系统管理器"""

    def __init__(self, limit: int = 30):
        self.limit = limit
        self.particles: list[Particle] = []
        self.texts: list[FloatingText] = []

    def spawn(
        self,
        x: int,
        y: int,
        count: int = 5,
        chars: list[str] = None,
        styles: list[str] = None,
    ) -> None:
        """生成粒子效果"""
        import random

        if len(self.particles) >= self.limit:
            return

        chars = chars or ["*"]
        styles = styles or ["yellow"]

        for _ in range(min(count, self.limit - len(self.particles))):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(0.1, 0.3)
            self.particles.append(
                Particle(
                    x=x + 0.5,
                    y=y + 0.5,
                    char=random.choice(chars),
                    style=random.choice(styles),
                    life=random.randint(15, 25),
                    dx=math.cos(angle) * speed,
                    dy=math.sin(angle) * speed - 0.1,
                )
            )

    def add_text(
        self, x: int, y: int, text: str, style: str = "white", life: int = 30
    ) -> None:
        """添加浮动文字"""
        self.texts.append(FloatingText(x, y, text, style, life))

    def update(self) -> None:
        """更新所有粒子和文字"""
        self.particles = [p for p in self.particles if p.update()]
        self.texts = [t for t in self.texts if t.update()]

    def clear(self) -> None:
        """清除所有粒子和文字"""
        self.particles.clear()
        self.texts.clear()


import math
