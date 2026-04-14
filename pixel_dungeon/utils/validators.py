#!/usr/bin/env python3
"""输入验证模块"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    value: Any
    error: Optional[str] = None


class Validator:
    """输入验证器"""

    def __init__(self, name: str):
        self.name = name
        self.rules: List[Callable[[Any], ValidationResult]] = []

    def add_rule(
        self,
        check: Callable[[Any], bool],
        error_msg: str,
        transform: Optional[Callable[[Any], Any]] = None,
    ) -> "Validator":
        """添加验证规则"""

        def rule(value):
            if transform:
                try:
                    value = transform(value)
                except Exception:
                    return ValidationResult(False, value, f"{self.name} 格式错误")

            if check(value):
                return ValidationResult(True, value)
            return ValidationResult(False, value, error_msg)

        self.rules.append(rule)
        return self

    def validate(self, value: Any) -> ValidationResult:
        """执行所有验证规则"""
        for rule in self.rules:
            result = rule(value)
            if not result.is_valid:
                return result
        return ValidationResult(True, value)


# 预定义的验证器
VALIDATORS = {
    "fps": Validator("fps").add_rule(
        lambda x: 10 <= x <= 60, "fps 必须在 10-60 之间", int
    ),
    "level": Validator("level").add_rule(lambda x: x > 0, "等级必须为正整数", int),
    "gold": Validator("gold").add_rule(lambda x: x >= 0, "金币不能为负数", int),
    "heal": Validator("heal").add_rule(lambda x: x > 0, "恢复值必须为正整数", int),
    "floor": Validator("floor").add_rule(lambda x: x > 0, "层数必须为正整数", int),
}


def get_validator(name: str) -> Optional[Validator]:
    """获取预定义的验证器"""
    return VALIDATORS.get(name)


def validate_command_arg(cmd: str, arg: str) -> ValidationResult:
    """验证命令参数"""
    validator = get_validator(cmd)
    if validator:
        return validator.validate(arg)
    return ValidationResult(True, arg)
