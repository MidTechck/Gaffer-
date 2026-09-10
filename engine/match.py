"""
Match simulation.

Drawn from ideas used across managers — not copied from any one game:

- Football Manager: player quality beats tactics; missing a leader/star hurts
  the line they play in. Position and fitness change every action.
- eFootball / Master League: lineup 'team strength' moves with overall,
  condition and putting people in natural roles. Wrong slots punish you.
- FootLord-style: one overall scale, role multiplier, compressed scores.
- DLS-style simplicity: the better XI should usually win, not always.

Presence: the best two outfield players carry extra weight. If they sit,
strength falls more than swapping an average player.
"""

from __future__ import annotations

import random
from typing import Any


ROLE_LINE = {
    "GK": "gk",
    "LB": "def",
    "CB": "def",
    "RB": "def",
    "CDM": "mid",
    "CM": "mid",
    "CAM": "mid",
    "LM": "mid",
    "RM": "mid",
    "LW": "att",
    "RW": "att",
    "ST": "att",
}

STYLE_NEED = {
    "possess": {"mid": 1.06, "att": 1.02, "def": 0.98},
    "possession": {"mid": 1.07, "att": 1.02, "def": 1.0},
    "balanced": {"mid": 1.0, "att": 1.0, "def": 1.0},
    "direct": {"att": 1.06, "def": 1.02, "mid": 0.98},
    "quick_counter": {"att": 1.08, "mid": 1.02, "def": 0.96},
    "long_ball": {"att": 1.07, "def": 1.03, "mid": 0.95},
    "long_ball_counter": {"att": 1.09, "def": 1.06, "mid": 0.94},
    "park_bus": {"def": 1.10, "gk": 1.04, "att": 0.90, "mid": 0.96},
    "out_wide": {"att": 1.05, "mid": 1.02, "def": 0.98},
    "gegenpress": {"att": 1.06, "mid": 1.05, "def": 0.96},
    "harambee": {"att": 1.07, "mid": 1.04, "def": 0.95},
    "tiki_taka": {"mid": 1.08, "att": 1.01, "def": 0.98},
    "low_block": {"def": 1.12, "gk": 1.05, "att": 0.88, "mid": 0.96},
}

# phrase, weight, rarity (common / uncommon / rare), who can score it
GOAL_TYPES = [
    ("a tap-in", 0.10, "common", "any"),
    ("a close-range finish", 0.09, "common", "any"),
    ("a low drive", 0.07, "common", "any"),
    ("a placed finish", 0.06, "common", "att"),
    ("a one-on-one", 0.05, "common", "att"),
    ("a cut-back finish", 0.05, "common", "att"),
    ("a rebound", 0.05, "common", "any"),
    ("a near-post dart", 0.04, "common", "att"),
    ("a far-post finish", 0.04, "common", "att"),
    ("a header from a cross", 0.05, "common", "any"),
    ("a header from a corner", 0.04, "common", "any"),
    ("a penalty", 0.05, "common", "att"),
    ("a counter-attack finish", 0.04, "uncommon", "att"),
    ("a drilled shot under the keeper", 0.03, "uncommon", "att"),
    ("a tight-angle finish", 0.03, "uncommon", "att"),
    ("a curling effort", 0.03, "uncommon", "att"),
    ("a deflected strike", 0.03, "uncommon", "any"),
    ("a direct free kick", 0.025, "uncommon", "mid"),
    ("a long-range strike", 0.03, "uncommon", "mid"),
    ("a volley", 0.02, "rare", "att"),
    ("a half-volley", 0.015, "rare", "att"),
    ("a diving header", 0.012, "rare", "att"),
    ("a bicycle kick", 0.008, "rare", "att"),
    ("an outside-of-the-boot curler", 0.01, "rare", "att"),
    ("a chip over the keeper", 0.01, "rare", "att"),
]

INJURY_TYPES = [
    ("bruise", 4, 5, False),
    ("knock", 5, 7, False),
    ("dead leg", 6, 8, False),
    ("ankle sprain", 10, 18, False),
    ("hamstring", 14, 28, False),
    ("groin strain", 18, 30, False),
    ("shoulder strain", 21, 35, False),
    ("broken arm", 70, 100, True),
    ("broken leg", 150, 220, True),
    ("knee ligament", 240, 365, True),
]

STANCE_XG = {
    "attacking": (0.38, 0.22),
    "balanced": (0.0, 0.0),
    "defensive": (-0.22, -0.28),
}

# attacker style vs defender style → extra xG for the attacker
STYLE_MATCHUP = {
    ("quick_counter", "possession"): 0.28,
    ("quick_counter", "possess"): 0.28,
    ("possession", "park_bus"): -0.22,
    ("possess", "park_bus"): -0.22,
    ("long_ball", "park_bus"): 0.12,
    ("out_wide", "park_bus"): 0.08,
    ("park_bus", "quick_counter"): -0.10,
    ("gegenpress", "possession"): 0.18,
    ("harambee", "park_bus"): 0.10,
    ("tiki_taka", "gegenpress"): -0.12,
    ("low_block", "quick_counter"): -0.08,
}


def shape_mod(style: str, opp_form: str) -> float:
    form = opp_form or "4-3-3"
    if style in ("quick_counter", "gegenpress") and form.startswith(("4-3", "4-2")):
        return 0.16
    if style in ("quick_counter", "gegenpress") and form.startswith("5"):
        return -0.16
    if style == "long_ball" and form.startswith("3"):
        return 0.12
    if style == "long_ball" and form.startswith("4"):
        return -0.08
    if style in ("possession", "tiki_taka", "possess") and form in ("4-1-2-3", "4-1-4-1"):
        return -0.12
    if style in ("park_bus", "low_block") and form.startswith("4-3"):
        return -0.10
    if style == "out_wide" and form.startswith("3"):
        return 0.10
    return 0.0


def _role_mult(player: dict, slot: str) -> float:
    natural = {r["code"]: float(r.get("mult", 1)) for r in player.get("roles", [])}
    if slot in natural:
        return max(0.72, natural[slot])
    line = ROLE_LINE.get(slot, "mid")
    for code, m in natural.items():
        if ROLE_LINE.get(code) == line:
            return max(0.78, m * 0.9)
    return 0.72


def _slot_role(slot: str) -> str:
    return "".join(ch for ch in slot if not ch.isdigit())


def player_presence(player: dict, slot: str) -> float:
    slot = _slot_role(slot)
    ovr = float(player.get("overall", 70))
    fit = float(player.get("condition", 100)) / 100.0
    form = float(player.get("form", 6.6))
    form_m = 0.92 + (form - 6.5) * 0.04
    adapt = 0.94 + float(player.get("adaptation", 70)) / 500.0
    return ovr * _role_mult(player, slot) * max(0.55, fit) * form_m * adapt


def xi_strength(players_by_slot: dict[str, dict], style: str = "balanced") -> dict:
    if not players_by_slot:
        return {"total": 50.0, "gk": 50, "def": 50, "mid": 50, "att": 50, "star_cut": 0}
    lines = {"gk": [], "def": [], "mid": [], "att": []}
    raw = []
    for slot, p in players_by_slot.items():
        val = player_presence(p, slot)
        raw.append((val, p, slot))
        lines[ROLE_LINE.get(_slot_role(slot), "mid")].append(val)
    raw.sort(key=lambda t: t[0], reverse=True)
    # Star presence: top 2 outfield count 18% extra. Bench them and you feel it.
    star_bonus = 0.0
    for val, p, slot in raw[:3]:
        if _slot_role(slot) != "GK":
            star_bonus += val * 0.09
    need = STYLE_NEED.get(style, STYLE_NEED["balanced"])

    def avg(xs):
        return sum(xs) / len(xs) if xs else 62.0

    gk = avg(lines["gk"]) * need.get("gk", 1)
    de = avg(lines["def"]) * need.get("def", 1)
    mi = avg(lines["mid"]) * need.get("mid", 1)
    at = avg(lines["att"]) * need.get("att", 1)
    mood = avg([float(p.get("morale", 72)) for p in players_by_slot.values()])
    total = (gk * 0.15 + de * 0.27 + mi * 0.27 + at * 0.31) + star_bonus * 0.07
    total *= 0.90 + mood / 700.0
    return {
        "total": round(total, 2),
        "gk": round(gk, 1),
        "def": round(de, 1),
        "mid": round(mi, 1),
        "att": round(at, 1),
        "star_cut": round(star_bonus, 2),
    }


def _sample_goals(xg: float, rng: random.Random) -> int:
    xg = max(0.18, min(3.6, xg))
    # Independent chances — a 2.1 xG side should often score 2, not stall at 0.
    g = 0
    p = 1.0 - pow(2.71828, -xg)
    for _ in range(6):
        if rng.random() < min(0.78, p):
            g += 1
            p *= 0.55
        else:
            if rng.random() > 0.35:
                break
    if g >= 6 and rng.random() < 0.65:
        g = 5
    return g


def simulate_match(
    home_xi: dict[str, dict],
    away_xi: dict[str, dict],
    home_style: str = "balanced",
    away_style: str = "balanced",
    home_adv: bool = True,
    seed: int | None = None,
    home_stance: str = "balanced",
    away_stance: str = "balanced",
    home_form: str = "4-3-3",
    away_form: str = "4-3-3",
    home_boost: float = 0.0,
    away_boost: float = 0.0,
    knockout: bool = False,
    lite: bool = False,
) -> dict[str, Any]:
    rng = random.Random(seed)
    hs = xi_strength(home_xi, home_style)
    aws = xi_strength(away_xi, away_style)
    h = hs["total"] + (2.2 if home_adv else 0.0) + float(home_boost or 0)
    a = aws["total"] + float(away_boost or 0)
    diff = h - a
    # ~8 strength points ≈ a clear favourite who should usually win.
    hxg = 1.15 + max(-1.1, min(1.8, diff * 0.14))
    axg = 0.95 + max(-1.1, min(1.8, -diff * 0.12))
    h_off, h_vuln = STANCE_XG.get(home_stance, (0.0, 0.0))
    a_off, a_vuln = STANCE_XG.get(away_stance, (0.0, 0.0))
    hxg += h_off + a_vuln
    axg += a_off + h_vuln
    hxg += STYLE_MATCHUP.get((home_style, away_style), 0.0)
    axg += STYLE_MATCHUP.get((away_style, home_style), 0.0)
    hxg += shape_mod(home_style, away_form)
    axg += shape_mod(away_style, home_form)
    if home_style in ("possession", "possess"):
        hxg *= 0.92
        axg *= 0.90
    if away_style in ("possession", "possess"):
        axg *= 0.92
        hxg *= 0.90
    if home_style == "park_bus":
        hxg *= 0.78
        axg *= 0.82
    if away_style == "park_bus":
        axg *= 0.78
        hxg *= 0.82
    hg = _sample_goals(hxg, rng)
    ag = _sample_goals(axg, rng)

    if lite:
        def _credit(xi, n):
            pool = list(xi.values()) or []
            for _ in range(n):
                if not pool:
                    break
                p = rng.choice(pool)
                st = p.setdefault("season_stats", {"apps": 0, "goals": 0, "assists": 0})
                st["goals"] = st.get("goals", 0) + 1
        _credit(home_xi, hg)
        _credit(away_xi, ag)
        ratings = {}
        for xi, gf, ga in ((home_xi, hg, ag), (away_xi, ag, hg)):
            base = 6.4 + (gf - ga) * 0.15
            for p in xi.values():
                ratings[p["id"]] = round(max(5.2, min(8.6, base + rng.uniform(-0.2, 0.25))), 1)
        return {
            "home_goals": hg, "away_goals": ag,
            "ft_home": hg, "ft_away": ag,
            "extra_time": False, "pens_home": None, "pens_away": None,
            "winner_side": "home" if hg > ag else "away" if ag > hg else None,
            "home_xg": round(max(0.2, hxg), 2), "away_xg": round(max(0.2, axg), 2),
            "home_strength": hs, "away_strength": aws,
            "events": [], "injuries": [], "cards": [], "ratings": ratings,
        }

    events = []
    scorers_h, scorers_a = [], []
    def pick_how(player, slot):
        role = _slot_role(slot)
        line = ROLE_LINE.get(role, "mid")
        pool = []
        for name, w, rare, who in GOAL_TYPES:
            if who == "att" and line not in ("att", "mid"):
                continue
            if who == "mid" and line == "def":
                continue
            if rare == "rare" and role not in ("ST", "LW", "RW", "CAM", "CM"):
                continue
            pool.append((name, w))
        tot = sum(w for _, w in pool) or 1
        r = rng.random() * tot
        acc = 0.0
        for name, w in pool:
            acc += w
            if r <= acc:
                return name
        return "a close-range finish"

    def pick_scorer(xi, line_pref):
        cands = []
        for slot, p in xi.items():
            w = 1.0
            role = _slot_role(slot)
            if ROLE_LINE.get(role) == "att":
                w = 3.2
            elif ROLE_LINE.get(role) == "mid":
                w = 1.4
            elif role == "GK":
                w = 0.02
            cands.append((w * (float(p.get("overall", 70)) / 80), p))
        tot = sum(w for w, _ in cands) or 1
        r = rng.random() * tot
        acc = 0
        for w, p in cands:
            acc += w
            if r <= acc:
                return p
        return list(xi.values())[0]

    minute_pool = list(range(4, 92))
    rng.shuffle(minute_pool)
    mi = 0
    def add_goal(xi, side):
        nonlocal mi
        p = pick_scorer(xi, "att")
        slot = next((s for s, pl in xi.items() if pl["id"] == p["id"]), "ST")
        m = minute_pool[mi]
        mi += 1
        how = pick_how(p, slot)
        if how == "a penalty" and rng.random() < 0.18:
            events.append({
                "minute": m, "type": "miss", "side": side, "player_id": p["id"], "name": p["last_name"],
                "text": f"{m}' {p['last_name']} missed a penalty",
            })
            return False
        assist = None
        pool = [x for x in xi.values() if x["id"] != p["id"]]
        if how not in ("a penalty", "a direct free kick") and pool and rng.random() < 0.7:
            assist = rng.choice(pool)
            assist.setdefault("season_stats", {})
            assist["season_stats"]["assists"] = assist["season_stats"].get("assists", 0) + 1
        p.setdefault("season_stats", {})
        p["season_stats"]["goals"] = p["season_stats"].get("goals", 0) + 1
        bit = f" from {how}" if how != "open play" else ""
        who = f", assist {assist['last_name']}" if assist else ""
        events.append({
            "minute": m, "type": "goal", "side": side, "player_id": p["id"], "name": p["last_name"],
            "how": how, "text": f"{m}' {p['last_name']} scored{bit}{who}",
        })
        return True

    real_h = real_a = 0
    for _ in range(hg):
        if add_goal(home_xi, "home"):
            real_h += 1
    for _ in range(ag):
        if add_goal(away_xi, "away"):
            real_a += 1
    hg, ag = real_h, real_a

    events.sort(key=lambda e: e["minute"])

    def rate(xi, gf, ga):
        ratings = {}
        base = 6.4 + (gf - ga) * 0.18
        for slot, p in xi.items():
            r = base + (float(p.get("overall", 70)) - 75) * 0.02 + rng.uniform(-0.35, 0.45)
            if p["id"] in (scorers_h if p in home_xi.values() else scorers_a) or p["id"] in scorers_h + scorers_a:
                r += 0.55
            ratings[p["id"]] = round(max(5.1, min(9.4, r)), 1)
        return ratings

    injuries = []
    cards = []
    pool = list(home_xi.values()) + list(away_xi.values())
    if pool:
        tired = [p for p in pool if float(p.get("condition", 88)) < 70]
        risk_pool = tired * 2 + pool
        vic = rng.choice(risk_pool)
        fit = float(vic.get("condition", 88))
        chance = 0.08 + max(0, (70 - fit) / 100.0)
        if rng.random() < chance:
            roll = rng.random()
            if roll < 0.02:
                kind, lo, hi, big = INJURY_TYPES[-1]
            elif roll < 0.05:
                kind, lo, hi, big = INJURY_TYPES[-2]
            elif roll < 0.09:
                kind, lo, hi, big = INJURY_TYPES[-3]
            elif fit < 50:
                kind, lo, hi, big = rng.choice(INJURY_TYPES[3:7])
            else:
                kind, lo, hi, big = rng.choice(INJURY_TYPES[:4])
            days = rng.randint(lo, hi)
            injuries.append({
                "player_id": vic["id"], "days": days, "name": vic["last_name"],
                "kind": kind, "big": big,
            })
        if rng.random() < 0.07:
            vic = rng.choice(pool)
            red = rng.random() < 0.12
            cards.append({"player_id": vic["id"], "color": "red" if red else "yellow", "name": vic["last_name"]})
            if red:
                injuries.append({"player_id": vic["id"], "days": rng.choice([7, 10, 14]), "name": vic["last_name"], "kind": "ban"})

    used_mins = {e["minute"] for e in events}
    extra = [m for m in range(8, 90) if m not in used_mins]
    rng.shuffle(extra)
    ei = 0
    cause = {"muscle": "a sprint", "joint": "a challenge", "knock": "a heavy tackle", "ban": "a red card"}
    for inj in injuries:
        m = extra[ei] if ei < len(extra) else rng.randint(10, 85)
        ei += 1
        why = cause.get(inj.get("kind"), "a challenge")
        events.append({
            "minute": m, "type": "injury", "name": inj["name"],
            "text": f"{m}' {inj['name']} went off with a {inj['kind']} from {why} ({inj['days']} days)",
        })
    for card in cards:
        m = extra[ei] if ei < len(extra) else rng.randint(10, 85)
        ei += 1
        if card["color"] == "red":
            txt = f"{m}' {card['name']} was sent off"
        else:
            txt = f"{m}' {card['name']} was booked"
        events.append({"minute": m, "type": "card", "name": card["name"], "text": txt})
    events.sort(key=lambda e: e["minute"])

    ft_h, ft_a = hg, ag
    pens_h = pens_a = None
    extra_used = False
    winner_side = None
    if knockout and hg == ag:
        events.append({"minute": 90, "type": "info", "text": "90' Full time. Extra time."})
        extra_used = True
        eh = 1 if rng.random() < min(0.42, hxg * 0.18) else 0
        ea = 1 if rng.random() < min(0.42, axg * 0.18) else 0
        if eh and ea and rng.random() < 0.45:
            ea = 0
        minute_pool.extend([93, 97, 102, 108, 112, 118])
        for _ in range(eh):
            if add_goal(home_xi, "home"):
                hg += 1
        for _ in range(ea):
            if add_goal(away_xi, "away"):
                ag += 1
        events.append({"minute": 120, "type": "info", "text": f"120' Extra time ends {hg}–{ag}."})
        if hg == ag:
            events.append({"minute": 121, "type": "info", "text": "Penalties."})
            pens_h = pens_a = 0
            order_h = list(home_xi.values())
            order_a = list(away_xi.values())
            rng.shuffle(order_h)
            rng.shuffle(order_a)
            taken = 0
            while taken < 5 or pens_h == pens_a:
                ph = order_h[taken % max(1, len(order_h))]
                pa = order_a[taken % max(1, len(order_a))]
                hs_ok = rng.random() < 0.74
                as_ok = rng.random() < 0.74
                if hs_ok:
                    pens_h += 1
                events.append({
                    "minute": 121 + taken, "type": "pen",
                    "text": f"PEN {ph['last_name']} {'scores' if hs_ok else 'misses'} ({pens_h}–{pens_a})",
                })
                if taken >= 4 and pens_h > pens_a + (4 - taken) and not as_ok:
                    pass
                if as_ok:
                    pens_a += 1
                events.append({
                    "minute": 121 + taken, "type": "pen",
                    "text": f"PEN {pa['last_name']} {'scores' if as_ok else 'misses'} ({pens_h}–{pens_a})",
                })
                taken += 1
                if taken >= 20:
                    if pens_h == pens_a:
                        pens_h += 1
                    break
            winner_side = "home" if pens_h > pens_a else "away"
            events.append({
                "minute": 130, "type": "info",
                "text": f"Penalties {pens_h}–{pens_a}.",
            })
        else:
            winner_side = "home" if hg > ag else "away"
    elif hg > ag:
        winner_side = "home"
    elif ag > hg:
        winner_side = "away"

    events.sort(key=lambda e: e["minute"])

    return {
        "home_goals": hg,
        "away_goals": ag,
        "ft_home": ft_h,
        "ft_away": ft_a,
        "extra_time": extra_used,
        "pens_home": pens_h,
        "pens_away": pens_a,
        "winner_side": winner_side,
        "home_xg": round(max(0.2, hxg), 2),
        "away_xg": round(max(0.2, axg), 2),
        "home_strength": hs,
        "away_strength": aws,
        "events": events,
        "injuries": injuries,
        "cards": cards,
        "ratings": {**rate(home_xi, hg, ag), **rate(away_xi, ag, hg)},
    }


def apply_decider(res: dict, home_xi: dict, away_xi: dict, seed: int | None = None) -> dict:
    if res.get("home_goals") != res.get("away_goals"):
        res["winner_side"] = "home" if res["home_goals"] > res["away_goals"] else "away"
        return res
    rng = random.Random((seed or 1) + 17)
    events = list(res.get("events") or [])
    hg, ag = res["home_goals"], res["away_goals"]
    events.append({"minute": 90, "type": "info", "text": "90' Level. Extra time."})
    names_h = [p.get("last_name", "Home") for p in home_xi.values()] or ["Home"]
    names_a = [p.get("last_name", "Away") for p in away_xi.values()] or ["Away"]
    if rng.random() < 0.38:
        hg += 1
        events.append({"minute": rng.choice([97, 103, 109]), "type": "goal", "text": f"{events[-1]['minute'] if False else 102}' {rng.choice(names_h)} scored in extra time"})
        events[-1]["minute"] = 102
        events[-1]["text"] = f"102' {rng.choice(names_h)} scored in extra time"
    if rng.random() < 0.34:
        ag += 1
        events.append({"minute": 111, "type": "goal", "text": f"111' {rng.choice(names_a)} scored in extra time"})
    res["extra_time"] = True
    res["home_goals"], res["away_goals"] = hg, ag
    if hg != ag:
        res["winner_side"] = "home" if hg > ag else "away"
        events.append({"minute": 120, "type": "info", "text": f"120' Extra time {hg}–{ag}."})
        res["events"] = sorted(events, key=lambda e: e.get("minute", 0))
        return res
    events.append({"minute": 120, "type": "info", "text": "120' Still level. Penalties."})
    ph = pa = 0
    for i in range(5):
        hs_ok = rng.random() < 0.75
        as_ok = rng.random() < 0.75
        if hs_ok:
            ph += 1
        events.append({"minute": 121 + i, "type": "pen", "text": f"PEN {names_h[i % len(names_h)]} {'scores' if hs_ok else 'misses'} ({ph}–{pa})"})
        if as_ok:
            pa += 1
        events.append({"minute": 121 + i, "type": "pen", "text": f"PEN {names_a[i % len(names_a)]} {'scores' if as_ok else 'misses'} ({ph}–{pa})"})
        if i >= 3 and abs(ph - pa) > (4 - i):
            break
    while ph == pa:
        hs_ok = rng.random() < 0.72
        as_ok = rng.random() < 0.72
        if hs_ok:
            ph += 1
        if as_ok:
            pa += 1
        events.append({"minute": 128, "type": "pen", "text": f"PEN sudden death {ph}–{pa}"})
        if ph != pa:
            break
    res["pens_home"], res["pens_away"] = ph, pa
    res["winner_side"] = "home" if ph > pa else "away"
    events.append({"minute": 130, "type": "info", "text": f"Penalties {ph}–{pa}."})
    res["events"] = sorted(events, key=lambda e: e.get("minute", 0))
    return res


FORMATIONS = {
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "LW", "CAM", "RW", "ST"],
    "4-1-4-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "LM", "CM", "CM", "RM", "ST"],
    "4-4-1-1": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "CAM", "ST"],
    "4-5-1": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CDM", "CM", "RM", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "LM", "CM", "CDM", "CM", "RM", "ST", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"],
    "5-3-2": ["GK", "LB", "CB", "CB", "CB", "RB", "CM", "CM", "CM", "ST", "ST"],
}


def auto_xi(squad: list[dict], formation: str = "4-3-3") -> dict[str, dict]:
    slots = FORMATIONS.get(formation, FORMATIONS["4-3-3"])
    used = set()
    xi = {}
    # unique slot keys: CB1 CB2
    counts: dict[str, int] = {}
    keyed = []
    for s in slots:
        counts[s] = counts.get(s, 0) + 1
        keyed.append(s if counts[s] == 1 and slots.count(s) == 1 else f"{s}{counts[s]}")

    def score(p, role):
        if p.get("injury") or p["id"] in used:
            return -1
        return player_presence(p, role)

    for key, role in zip(keyed, slots):
        best = max(squad, key=lambda p: score(p, role.split("1")[0].split("2")[0] if False else role[:2] if role[:2] == "CB" else role))
        # simpler pick
        role_code = "".join(ch for ch in key if not ch.isdigit())
        avail = [p for p in squad if not p.get("injury") and p["id"] not in used]
        if not avail:
            break
        pick = max(avail, key=lambda p: player_presence(p, role_code))
        used.add(pick["id"])
        xi[key] = pick
    return xi
