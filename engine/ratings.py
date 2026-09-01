"""Growth, value, condition, form."""

from __future__ import annotations

import random


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


def growth_delta(age: int, overall: float, potential: float, apps: int, goals: int = 0, assists: int = 0) -> float:
    room = max(0.0, potential - overall)
    contrib = int(goals) + int(assists)
    if apps >= 22 and contrib >= 6:
        g = random.uniform(2.0, 3.5)
        if age <= 24:
            g = min(3.9, g + 0.25)
    elif apps >= 15:
        g = random.uniform(1.8, 2.7)
    elif apps >= 6:
        g = random.uniform(1.0, 1.8)
    elif apps >= 1:
        g = random.uniform(0.25, 0.9)
    else:
        g = random.uniform(0.12, 0.45)
    if age <= 21:
        g *= 1.18
    elif age <= 26:
        g *= 1.0
    elif age <= 30:
        g *= 0.55
    elif age <= 33:
        g *= 0.2
    else:
        g = random.uniform(-1.3, -0.35)
    if room < 0.5 and age < 30:
        g = min(g, 0.35)
    return clamp(g, -2.2, 3.9)


def grow_skills(skills: dict | None, delta: float, roles: list | None) -> dict:
    skills = dict(skills or {})
    keys = ["pace", "passing", "shooting", "dribbling", "defence", "physical", "gk"]
    for k in keys:
        skills.setdefault(k, 55.0)
    pos = ""
    if roles:
        raw = roles[0]
        pos = str(raw.get("code") if isinstance(raw, dict) else raw)
    weights = {k: 0.55 for k in keys}
    if pos == "GK":
        weights = {"gk": 1.2, "physical": 0.5, "pace": 0.15, "passing": 0.35, "shooting": 0.1, "dribbling": 0.1, "defence": 0.2}
    elif pos in ("ST", "LW", "RW"):
        weights.update({"shooting": 1.1, "pace": 1.0, "dribbling": 0.9, "passing": 0.5, "defence": 0.2})
    elif pos in ("CM", "CAM", "CDM", "LM", "RM"):
        weights.update({"passing": 1.1, "dribbling": 0.8, "defence": 0.6, "shooting": 0.5})
    else:
        weights.update({"defence": 1.1, "physical": 1.0, "pace": 0.5, "passing": 0.45})
    for k in keys:
        jitter = random.uniform(0.65, 1.2)
        skills[k] = round(clamp(float(skills[k]) + delta * weights.get(k, 0.5) * jitter, 30, 99), 1)
    return skills


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
