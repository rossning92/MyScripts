from typing import TypeVar

_T = TypeVar("_T", int, float)


def clamp(value: _T, min_value: _T, max_value: _T) -> _T:
    return max(min_value, min(value, max_value))
