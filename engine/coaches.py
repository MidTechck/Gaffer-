"""Head coaches and assistants. User is the manager who hires them."""

from __future__ import annotations

import random

LEVELS = {
    "E": {"boost": 0.4, "wage": 8_000, "stars": 1},
    "D": {"boost": 0.8, "wage": 16_000, "stars": 2},
    "C": {"boost": 1.3, "wage": 28_000, "stars": 3},
    "B": {"boost": 1.9, "wage": 48_000, "stars": 3},
    "A": {"boost": 2.6, "wage": 75_000, "stars": 4},
    "A+": {"boost": 3.2, "wage": 95_000, "stars": 4},
    "S": {"boost": 3.8, "wage": 130_000, "stars": 5},
}

PLAY_KEYS = (
    ("possession", "Possession"),
    ("lbc", "Long ball counter"),
    ("qc", "Quick counter"),
    ("lb", "Long ball"),
    ("wide", "Out wide"),
)

STYLE_TO_PLAY = {
    "possession": "possession",
    "tiki_taka": "possession",
    "quick_counter": "qc",
    "gegenpress": "qc",
    "harambee": "qc",
    "long_ball": "lb",
    "long_ball_counter": "lbc",
    "out_wide": "wide",
    "park_bus": "lbc",
    "low_block": "lbc",
    "balanced": None,
}

FIRST = ["Hugo", "Marco", "Luis", "Owen", "Ravi", "Niko", "Ibrahim", "Sean", "Pavel", "Jonas", "Amadou", "Diego", "Erik", "Tomas", "Kwame"]
LAST = ["Hart", "Vidal", "Nkrumah", "Berg", "Santos", "Kovacs", "Diallo", "Reeves", "Nowak", "Costa", "Lindgren", "Okoye", "Farrell", "Mbeki"]
NATS = ["England", "Spain", "Italy", "Germany", "France", "Portugal", "Netherlands", "Belgium", "Brazil", "Argentina", "Zambia", "Egypt", "Nigeria", "Senegal", "Croatia"]
STYLES = list(STYLE_TO_PLAY)
CLUB_HINTS = ["United", "City", "Sporting", "Athletic", "Rovers", "Wanderers", "FC", "Town"]

NAMED = [
    {"first_name": "Fabio", "last_name": "Capello", "nation": "Italy", "age": 80, "level": "S", "style": "long_ball",
     "play": {"possession": 46, "lbc": 89, "qc": 57, "lb": 89, "wide": 64}, "titles": 9},
    {"first_name": "Roberto", "last_name": "Martinez", "nation": "Spain", "age": 53, "level": "A+", "style": "quick_counter",
     "play": {"possession": 58, "lbc": 70, "qc": 90, "lb": 89, "wide": 64}, "titles": 4},
    {"first_name": "Thomas", "last_name": "Tuchel", "nation": "Germany", "age": 53, "level": "S", "style": "possession",
     "play": {"possession": 90, "lbc": 59, "qc": 89, "lb": 58, "wide": 70}, "titles": 6},
    {"first_name": "Xabi", "last_name": "Alonso", "nation": "Spain", "age": 44, "level": "S", "style": "out_wide",
     "play": {"possession": 71, "lbc": 54, "qc": 89, "lb": 56, "wide": 89}, "titles": 3},
    {"first_name": "Franz", "last_name": "Beckenbauer", "nation": "Germany", "age": 78, "level": "S", "style": "lbc",
     "play": {"possession": 65, "lbc": 89, "qc": 57, "lb": 89, "wide": 60}, "titles": 8},
    {"first_name": "Cesc", "last_name": "Fabregas", "nation": "Spain", "age": 38, "level": "A", "style": "possession",
     "play": {"possession": 89, "lbc": 56, "qc": 65, "lb": 57, "wide": 68}, "titles": 1},
    {"first_name": "Pep", "last_name": "Guardiola", "nation": "Spain", "age": 55, "level": "S", "style": "tiki_taka",
     "play": {"possession": 94, "lbc": 48, "qc": 72, "lb": 42, "wide": 80}, "titles": 15},
    {"first_name": "Carlo", "last_name": "Ancelotti", "nation": "Italy", "age": 67, "level": "S", "style": "balanced",
     "play": {"possession": 78, "lbc": 70, "qc": 74, "lb": 66, "wide": 72}, "titles": 12},
    {"first_name": "Jurgen", "last_name": "Klopp", "nation": "Germany", "age": 59, "level": "S", "style": "gegenpress",
     "play": {"possession": 68, "lbc": 62, "qc": 93, "lb": 55, "wide": 76}, "titles": 8},
    {"first_name": "Jose", "last_name": "Mourinho", "nation": "Portugal", "age": 63, "level": "A+", "style": "park_bus",
     "play": {"possession": 55, "lbc": 88, "qc": 70, "lb": 72, "wide": 58}, "titles": 10},
    {"first_name": "Mikel", "last_name": "Arteta", "nation": "Spain", "age": 44, "level": "A+", "style": "possession",
     "play": {"possession": 88, "lbc": 52, "qc": 78, "lb": 50, "wide": 81}, "titles": 2},
    {"first_name": "Antonio", "last_name": "Conte", "nation": "Italy", "age": 56, "level": "A+", "style": "quick_counter",
     "play": {"possession": 64, "lbc": 75, "qc": 88, "lb": 60, "wide": 70}, "titles": 7},
]


def _file(rng: random.Random, level: str) -> list:
    n = rng.randint(2, 5)
    rows = []
    year = 2014
    for _ in range(n):
        years = rng.randint(1, 4)
        titles = rng.randint(0, 2 if level in ("A", "A+", "S") else 1)
        rows.append({
            "club": f"{rng.choice(LAST)} {rng.choice(CLUB_HINTS)}",
            "from": year,
            "to": year + years,
            "titles": titles,
        })
        year += years
    return rows


def _play_from_style(style: str, rng: random.Random) -> dict:
    base = {k: rng.randint(48, 68) for k, _ in PLAY_KEYS}
    key = STYLE_TO_PLAY.get(style)
    if key:
        base[key] = rng.randint(82, 94)
    else:
        for k in base:
            base[k] = rng.randint(60, 78)
    return base


def make_coach(cid: int, rng: random.Random | None = None, named: dict | None = None) -> dict:
    rng = rng or random.Random(cid * 17)
    if named:
        level = named.get("level", "A")
        spec = LEVELS[level]
        play = dict(named["play"])
        style = named.get("style", "balanced")
        if style == "lbc":
            style = "park_bus"
        return {
            "id": cid,
            "first_name": named["first_name"],
            "last_name": named["last_name"],
            "nation": named["nation"],
            "age": named["age"],
            "level": level,
            "stars": spec["stars"],
            "style": style,
            "play": play,
            "attack": play.get("qc", 70),
            "defence": play.get("lbc", 70),
            "youth": rng.randint(50, 88),
            "fitness": rng.randint(50, 88),
            "wage": spec["wage"] + rng.randint(0, 20_000),
            "years": rng.randint(2, 4),
            "club_id": 0,
            "role": "free",
            "history": named.get("history") or _file(rng, level),
            "titles": named.get("titles", 3),
            "started": named.get("started", 2000),
            "named": True,
        }
    level = rng.choices(list(LEVELS), weights=[18, 18, 20, 16, 12, 10, 6], k=1)[0]
    spec = LEVELS[level]
    style = rng.choice(STYLES)
    play = _play_from_style(style, rng)
    return {
        "id": cid,
        "first_name": rng.choice(FIRST),
        "last_name": rng.choice(LAST),
        "nation": rng.choice(NATS),
        "age": rng.randint(38, 62),
        "level": level,
        "stars": spec["stars"],
        "style": style,
        "play": play,
        "attack": play.get("qc", 60),
        "defence": play.get("lbc", 60),
        "youth": rng.randint(40, 90),
        "fitness": rng.randint(40, 90),
        "wage": spec["wage"] + rng.randint(-2000, 8000),
        "years": rng.randint(1, 4),
        "club_id": 0,
        "role": "free",
        "history": _file(rng, level),
        "titles": sum(r["titles"] for r in _file(rng, level)),
        "named": False,
    }


def display(c: dict) -> str:
    return f"{c.get('first_name','')} {c.get('last_name','')}".strip() or "Coach"


def play_of(c: dict) -> dict:
    p = dict(c.get("play") or {})
    if p:
        return p
    return _play_from_style(c.get("style", "balanced"), random.Random(c.get("id", 1)))


def style_fit(c: dict | None, style: str) -> float:
    if not c:
        return 0.0
    play = play_of(c)
    key = STYLE_TO_PLAY.get(style)
    if not key:
        avg = sum(play.values()) / max(1, len(play))
        return 0.6 if avg >= 70 else 0.15
    score = float(play.get(key, 55))
    if score >= 85:
        return 6.8
    if score >= 75:
        return 3.6
    if score >= 65:
        return 0.6
    if score >= 55:
        return -2.8
    return -5.5


def boost(c: dict | None, style: str | None = None) -> float:
    if not c:
        return 0.0
    base = LEVELS.get(c.get("level", "C"), LEVELS["C"])["boost"]
    raw = base + (float(c.get("attack", 60)) + float(c.get("defence", 60))) / 140.0
    if style:
        raw += style_fit(c, style)
    return raw


def pack_coaches(n: int = 260) -> list:
    from engine.coach_book import REAL
    seen = set()
    rows = []
    for row in list(REAL) + list(NAMED):
        key = (row["first_name"], row["last_name"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    out = []
    i = 1
    for row in rows:
        out.append(make_coach(i, random.Random(2026 + i), row))
        i += 1
    while len(out) < n:
        out.append(make_coach(i, random.Random(2026 + i * 13)))
        i += 1
    return out
