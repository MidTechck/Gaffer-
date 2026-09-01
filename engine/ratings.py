"""Growth, value, condition, form."""

from __future__ import annotations


def clamp(n: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, n))


def age_from_birth(birth: str, today: str) -> int:
    y, m, d = (int(x) for x in birth.split("-"))
    Y, M, D = (int(x) for x in today.split("-"))
    age = Y - y
    if (M, D) < (m, d):
        age -= 1
    return age


def compute_value(overall: float, age: int) -> int:
    base = max(0.2, (overall - 58) ** 2.05) * 18000
    if age < 23:
        base *= 1.35
    elif age < 27:
        base *= 1.15
    elif age > 32:
        base *= max(0.35, 1.15 - (age - 32) * 0.12)
    return int(base)


def growth_delta(age: int, overall: float, potential: float, minutes: int) -> float:
    room = max(0.0, potential - overall)
    if age <= 21:
        g = 0.35 + room * 0.04
    elif age <= 26:
        g = 0.12 + room * 0.02
    elif age <= 30:
        g = 0.02
    elif age <= 33:
        g = -0.18
    else:
        g = -0.45
    if minutes > 2000:
        g += 1.6
    elif minutes > 1200:
        g += 0.85
    elif minutes > 600:
        g += 0.25
    elif minutes < 200 and age < 30:
        g -= 0.15
    return clamp(g, -1.4, 3.1)


def condition_tick(cond: float, played: bool, injured: bool) -> float:
    if injured:
        return clamp(cond + 2, 35, 100)
    if played:
        return clamp(cond - 12, 38, 100)
    return clamp(cond + 3, 38, 100)


def compute_wage(overall: float, age: int) -> int:
    base = max(4_000, int((overall - 55) ** 2.05 * 90))
    if age >= 33:
        base = int(base * 0.85)
    if age <= 21:
        base = int(base * 0.65)
    return base


def staff_wage(reputation: int) -> int:
    return int(6_000 + reputation * 80)
