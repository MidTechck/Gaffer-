"""Load / save world and apply career actions."""

from __future__ import annotations

import json
import random
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

from engine.badges import svg as badge_svg
from engine.match import FORMATIONS, auto_xi, simulate_match, xi_strength
from engine import press


def badge(club: dict, size: int = 28) -> str:
    return badge_svg(club or {}, size)
from engine import sponsors as SPON
from engine.ratings import age_from_birth, compute_value, compute_wage, condition_tick, grow_skills, growth_delta, staff_wage


ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def new_career(pack: dict, club_id: int, manager_name: str, profile: dict | None = None) -> dict:
    w = deepcopy(pack)
    profile = profile or {}
    first = (profile.get("first") or manager_name.split(" ")[0] or "You").strip()
    last = (profile.get("last") or " ".join(manager_name.split(" ")[1:]) or "Manager").strip()
    w["user"] = {
        "manager_name": f"{first} {last}".strip(),
        "first_name": first,
        "last_name": last,
        "age": int(profile.get("age") or 35),
        "nationality": profile.get("nation") or "England",
        "club_id": club_id,
        "formation": "4-3-3",
        "style": "balanced",
        "stance": "balanced",
        "xi": {},
        "bench": [],
        "sponsors": [],
        "awards": [],
        "trophies": [],
        "fan_mood": 62,
        "win_streak": 0,
    }
    w["seats"] = {str(club_id): w["user"]}
    w["lobby"] = {"needed": 2}
    w["meta"]["europe_on"] = False
    w["meta"]["tickets"] = {}
    w["news"] = []
    w["results"] = []
    for c in w["clubs"]:
        c.setdefault("form_meter", 55)
    club(w, club_id)["form_meter"] = 12
    club(w, club_id)["human"] = True
    repair_home_away(w)
    ensure_staff(w)
    ensure_xi(w)
    add_news(w, f"{manager_name} appointed at {club_name(w, club_id)}.", "board", True)
    starter = [s for s in SPON.CATALOG if s.get("min_rank", "E") in ("E", "D")]
    if starter:
        pick = dict(random.choice(starter))
        w["user"]["sponsor_mail"] = [pick]
        add_news(w, f"{pick['name']} offered a deal. Open Club to sign or refuse.", "desk", True)
    return w


def club_name(w: dict, cid: int) -> str:
    for c in w["clubs"]:
        if c["id"] == cid:
            return c["name"]
    return "?"


def club(w: dict, cid: int) -> dict:
    if not cid:
        return {
            "id": 0, "name": "Free agent", "short": "FA", "nation": "",
            "league_id": 0, "budget": 0, "reputation": 40, "colors": ["#889", "#223"],
        }
    return next(c for c in w["clubs"] if c["id"] == cid)


def player(w: dict, pid: int) -> dict:
    return next(p for p in w["players"] if p["id"] == pid)


def squad(w: dict, cid: int) -> list[dict]:
    return [p for p in w["players"] if p["club_id"] == cid and not p.get("retired")]


def league_clubs(w: dict, lid: int) -> list[dict]:
    return [c for c in w["clubs"] if c["league_id"] == lid]


def parse_d(s: str) -> date:
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def fmt_d(d: date) -> str:
    return d.isoformat()


def window_open(w: dict) -> bool:
    d = parse_d(w["meta"]["current_date"])
    y = int(w["meta"].get("season_start_year", d.year))
    summer = (date(y, 6, 15) <= d <= date(y, 9, 1))
    winter = (date(y + 1, 1, 1) <= d <= date(y + 1, 2, 1))
    return summer or winter


def window_label(w: dict) -> str:
    return "OPEN" if window_open(w) else "SHUT"


def add_news(w: dict, text: str, kind: str = "desk", important: bool = True, club_id: int | None = None) -> None:
    if club_id is None and kind != "wire":
        club_id = w.get("user", {}).get("club_id")
    w.setdefault("news", []).insert(0, {
        "date": w["meta"]["current_date"],
        "text": text,
        "kind": kind,
        "important": important,
        "club_id": club_id,
    })


def wire_news(w: dict, limit: int = 20) -> list[dict]:
    return [n for n in w.get("news", []) if n.get("kind") == "wire"][:limit]


def desk_news(w: dict, limit: int = 6) -> list[dict]:
    cid = w.get("user", {}).get("club_id")
    out = []
    for n in w.get("news", []):
        if n.get("important") is False:
            continue
        if n.get("club_id") not in (None, cid) and n.get("kind") not in ("window", "board"):
            continue
        if n.get("kind") == "wire":
            continue
        out.append(n)
        if len(out) >= limit:
            break
    return out


def repair_home_away(w: dict) -> None:
    """Balance remaining home games so a club is not stuck away for two months."""
    from collections import defaultdict
    if w["meta"].get("ha_fixed"):
        return
    leagues = {f["league_id"] for f in w["fixtures"]}
    for lid in leagues:
        fx = [f for f in w["fixtures"] if f["league_id"] == lid]
        homes: dict[int, int] = defaultdict(int)
        for f in fx:
            if f.get("played"):
                homes[f["home_id"]] += 1
        for f in fx:
            if f.get("played"):
                continue
            h, a = f["home_id"], f["away_id"]
            if homes[h] > homes[a]:
                f["home_id"], f["away_id"] = a, h
                homes[a] += 1
            else:
                homes[h] += 1
    w["meta"]["ha_fixed"] = True


def player_wage(w: dict, p: dict) -> int:
    if p.get("wage"):
        return int(p["wage"])
    age = age_from_birth(p["birthdate"], w["meta"]["current_date"])
    return compute_wage(float(p.get("overall", 70)), age)


def wage_bill(w: dict, cid: int) -> int:
    return sum(player_wage(w, p) for p in squad(w, cid))


def club_staff_wage(w: dict, cid: int) -> int:
    return staff_wage(int(club(w, cid).get("reputation", 70)))


CONTINENTAL = {"UCL", "Europa League", "Conference League", "CAF Champions League"}
EURO_LIDS = {1, 2, 3, 4, 5, 13, 14, 15}
AFR_LIDS = {6, 7, 8, 9, 10, 11, 12}


def ensure_cups(w: dict) -> None:
    y = int(w["meta"].get("season_start_year", 2026))
    if not any(f.get("cup") and f.get("cup") not in CONTINENTAL for f in w.get("fixtures", [])):
        w["fixtures"].extend(_first_cup_rounds(w, w.get("fixtures", []), y))
    seed_continental(w, y)


def europe_tickets_from_tables(w: dict) -> dict:
    tickets = {"UCL": [], "Europa League": [], "Conference League": [], "CAF Champions League": []}
    used: set[int] = set()
    for lid in sorted(EURO_LIDS):
        rows = table_for(w, lid)
        if not rows:
            club_rows = sorted(
                [c for c in w["clubs"] if c["league_id"] == lid],
                key=lambda c: -float(c.get("reputation", 70)),
            )
            rows = [{"club_id": c["id"]} for c in club_rows]
        for i, row in enumerate(rows, 1):
            cid = row["club_id"]
            if cid in used:
                continue
            if i <= 5:
                tickets["UCL"].append(cid)
                used.add(cid)
            elif i == 6:
                tickets["Europa League"].append(cid)
                used.add(cid)
            elif i in (7, 8):
                tickets["Conference League"].append(cid)
                used.add(cid)
    for lid in sorted(AFR_LIDS):
        rows = table_for(w, lid)
        if not rows:
            club_rows = sorted(
                [c for c in w["clubs"] if c["league_id"] == lid],
                key=lambda c: -float(c.get("reputation", 70)),
            )
            rows = [{"club_id": c["id"]} for c in club_rows]
        for i, row in enumerate(rows[:2], 1):
            cid = row["club_id"]
            if cid not in used:
                tickets["CAF Champions League"].append(cid)
                used.add(cid)
    return tickets


def _euro_pool(w: dict) -> list:
    nats = {"England", "Spain", "Italy", "Germany", "France", "Netherlands", "Portugal", "Belgium"}
    return sorted(
        [c for c in w["clubs"] if c.get("nation") in nats],
        key=lambda c: -float(c.get("reputation", 70)),
    )


def _league_phase(w, title, ids, year, dates, fid, rng):
    used = {cid: 0 for cid in ids}
    made = set()
    for md, dt in enumerate(dates, 1):
        pool = ids[:]
        rng.shuffle(pool)
        for i in range(0, len(pool) - 1, 2):
            a, b = pool[i], pool[i + 1]
            key = (min(a, b), max(a, b), md)
            if key in made or used[a] >= 8 or used[b] >= 8:
                continue
            w["fixtures"].append({
                "id": fid, "league_id": 0, "cup": title, "phase": "league",
                "round": md, "week": 0, "date": dt,
                "home_id": a, "away_id": b, "played": False,
            })
            fid += 1
            used[a] += 1
            used[b] += 1
            made.add(key)
    return fid


def seed_continental(w: dict, year: int) -> None:
    if not w["meta"].get("europe_on"):
        w["fixtures"] = [f for f in w["fixtures"] if f.get("cup") not in CONTINENTAL]
        return
    tickets = w["meta"].get("tickets") or {}
    if not tickets:
        return
    fid = 1 + max((f["id"] for f in w["fixtures"] if isinstance(f.get("id"), int)), default=0)
    rng = random.Random(year * 13)
    ucl_dates = [
        f"{year}-09-09", f"{year}-10-14", f"{year}-10-21", f"{year}-11-04",
        f"{year}-11-25", f"{year}-12-09", f"{year+1}-01-20", f"{year+1}-01-27",
    ]
    uel_dates = [
        f"{year}-09-17", f"{year}-10-02", f"{year}-10-23", f"{year}-11-06",
        f"{year}-11-27", f"{year}-12-11", f"{year+1}-01-22", f"{year+1}-01-29",
    ]
    uecl_dates = [
        f"{year}-10-02", f"{year}-10-23", f"{year}-11-06", f"{year}-11-27",
        f"{year}-12-11", f"{year+1}-02-19",
    ]
    if not any(f.get("cup") == "UCL" for f in w["fixtures"]):
        fid = _league_phase(w, "UCL", list(tickets.get("UCL") or []), year, ucl_dates, fid, rng)
    if not any(f.get("cup") == "Europa League" for f in w["fixtures"]):
        fid = _league_phase(w, "Europa League", list(tickets.get("Europa League") or []), year, uel_dates, fid, rng)
    if not any(f.get("cup") == "Conference League" for f in w["fixtures"]):
        fid = _league_phase(w, "Conference League", list(tickets.get("Conference League") or []), year, uecl_dates, fid, rng)
    if not any(f.get("cup") == "CAF Champions League" for f in w["fixtures"]):
        caf = list(tickets.get("CAF Champions League") or [])
        rng2 = random.Random(year * 17)
        rng2.shuffle(caf)
        gdate = f"{year}-11-22"
        for i in range(0, len(caf) - 1, 2):
            w["fixtures"].append({
                "id": fid, "league_id": 0, "cup": "CAF Champions League", "phase": "group",
                "round": 1, "week": 0, "date": gdate,
                "home_id": caf[i], "away_id": caf[i + 1], "played": False,
            })
            fid += 1
    return
    auto = eur[:32]
    play = eur[32:40]
    fid = 1 + max((f["id"] for f in w["fixtures"]), default=0)
    qdate = f"{year}-08-26"
    winners = list(auto)
    rng = random.Random(year * 13)
    for i in range(0, len(play) - 1, 2):
        w["fixtures"].append({
            "id": fid, "league_id": 0, "cup": "UCL", "phase": "qualifying",
            "round": 0, "week": 0, "date": qdate,
            "home_id": play[i]["id"], "away_id": play[i + 1]["id"], "played": False,
        })
        fid += 1
        winners.append(play[i])
    field = [c["id"] for c in winners[:36]]
    rng.shuffle(field)
    days = [14, 35, 42, 56, 77, 91, 126, 133]
    used = {cid: 0 for cid in field}
    made = set()
    for md, off in enumerate(days, 1):
        dt = f"{year}-{8 + (off // 31):02d}-{max(1, off % 28):02d}"
        if md >= 7:
            dt = f"{year+1}-01-{10 if md==7 else 27}"
        pool = field[:]
        rng.shuffle(pool)
        for i in range(0, min(len(pool) - 1, 35), 2):
            a, b = pool[i], pool[i + 1]
            key = tuple(sorted((a, b, md)))
            if key in made or used[a] >= 8 or used[b] >= 8:
                continue
            w["fixtures"].append({
                "id": fid, "league_id": 0, "cup": "UCL", "phase": "league",
                "round": md, "week": 0, "date": dt,
                "home_id": a, "away_id": b, "played": False,
            })
            fid += 1
            used[a] += 1
            used[b] += 1
            made.add(key)
    afr = [c for c in w["clubs"] if c.get("nation") in SCOUT_REGIONS["africa"] or c["league_id"] >= 6]
    afr.sort(key=lambda c: -float(c.get("reputation", 60)))
    sixteen = [c["id"] for c in afr[:16]]
    rng2 = random.Random(year * 17)
    rng2.shuffle(sixteen)
    gdate = f"{year}-11-22"
    for i in range(0, 16, 2):
        w["fixtures"].append({
            "id": fid, "league_id": 0, "cup": "CAF Champions League", "phase": "group",
            "round": 1, "week": 0, "date": gdate,
            "home_id": sixteen[i], "away_id": sixteen[i + 1], "played": False,
        })
        fid += 1


def league_place(w: dict, cid: int) -> int:
    lid = club(w, cid)["league_id"]
    table = table_for(w, lid)
    return next((i for i, r in enumerate(table, 1) if r["club_id"] == cid), 10)


RANK_CAP = {"E": 55, "D": 68, "C": 76, "B": 80, "A": 86, "A+": 92, "S": 99.9}


def squad_ovr(w: dict, cid: int) -> float:
    sq = sorted(squad(w, cid), key=lambda p: -float(p.get("overall", 70)))[:11]
    if not sq:
        return 60.0
    return sum(float(p["overall"]) for p in sq) / len(sq)


def team_rank(w: dict, cid: int) -> str:
    c = club(w, cid)
    meter = float(c.get("form_meter", 55))
    if meter >= 92:
        return "S"
    if meter >= 80:
        return "A+"
    if meter >= 68:
        return "A"
    if meter >= 56:
        return "B"
    if meter >= 42:
        return "C"
    if meter >= 28:
        return "D"
    return "E"


def form_meter(w: dict, cid: int) -> int:
    return int(club(w, cid).get("form_meter", 55))


def bump_form(w: dict, cid: int, delta: float) -> None:
    c = club(w, cid)
    c["form_meter"] = max(0, min(100, float(c.get("form_meter", 55)) + delta))


def max_buy_ovr(w: dict, cid: int) -> float:
    return float(RANK_CAP[team_rank(w, cid)])


def can_buy(w: dict, cid: int, p: dict) -> tuple[bool, str, int]:
    if not window_open(w):
        return False, "Window is shut.", 0
    if p.get("club_id") == cid:
        return False, "Already at the club.", 0
    if p.get("retired"):
        return False, "Retired.", 0
    fee = int(p.get("value", 1_000_000) * (0.28 if not p.get("club_id") else 1.08))
    if club(w, cid)["budget"] < fee:
        return False, "Not enough budget.", fee
    if len(squad(w, cid)) >= 28:
        return False, "Squad is full (28).", fee
    cap = max_buy_ovr(w, cid)
    rank = team_rank(w, cid)
    if float(p["overall"]) > cap + 0.15:
        return False, f"Rank {rank} clubs cannot sign {p['overall']:.0f} OVR (cap {cap:.0f}).", fee
    return True, "ok", fee


def complete_transfer(w: dict, pid: int, to_id: int, fee: int | None = None, years: int = 3) -> str:
    p = player(w, pid)
    frm = p["club_id"]
    if frm == to_id:
        return "same"
    fee = int(fee if fee is not None else p.get("value", 0) * 1.08)
    seller = club(w, frm)
    buyer = club(w, to_id)
    buyer["budget"] -= fee
    seller["budget"] += fee
    p["club_id"] = to_id
    p["adaptation"] = 55
    p["contract_years"] = max(1, min(5, int(years)))
    p["wage"] = compute_wage(float(p["overall"]), age_from_birth(p["birthdate"], w["meta"]["current_date"]))
    uid = w.get("user", {}).get("club_id")
    line = (
        f"{p['first_name']} {p['last_name']} has joined {buyer['name']} "
        f"from {seller['name']} on a {p['contract_years']}-year deal (£{fee:,})."
    )
    if frm == uid or to_id == uid:
        add_news(w, line, "desk", True)
    AFR = {"Zambia", "Egypt", "South Africa", "Morocco", "Nigeria", "Ghana", "Tunisia", "Kenya", "Senegal", "Algeria", "Cameroon"}
    EUR = {"England", "Spain", "Italy", "Germany", "France", "Portugal", "Netherlands", "Belgium", "Croatia"}
    bn, sn = buyer.get("nation", ""), seller.get("nation", "")
    if bn in AFR and (sn in EUR or p.get("nation") in EUR) and float(p["overall"]) >= 72:
        add_news(
            w,
            f"WIRE — {buyer['name']} bring {p['first_name']} {p['last_name']} from Europe (£{fee:,}).",
            "wire", True, club_id=None,
        )
    elif bn in EUR and (sn in AFR or p.get("nation") in AFR) and float(p["overall"]) >= 70:
        add_news(
            w,
            f"WIRE — {buyer['name']} sign {p['first_name']} {p['last_name']} out of Africa (£{fee:,}).",
            "wire", True, club_id=None,
        )
    elif float(p["overall"]) >= 78:
        add_news(
            w,
            press.fill(
                "signed",
                player=f"{p['first_name']} {p['last_name']}",
                buyer=buyer["name"],
                seller=seller["name"],
                years=p.get("contract_years", 3),
                fee=f"{fee:,}",
            ),
            "wire",
            True,
            club_id=None,
        )
    if uid and frm == uid:
        u = w["user"]
        u["xi"] = {k: v for k, v in u.get("xi", {}).items() if v != pid}
        ensure_xi(w)
    return line


def _seller_reply(w: dict, p: dict, buyer_id: int, fee: int, rounds: int = 1) -> tuple[str, str, int]:
    seller_id = p["club_id"]
    if not seller_id:
        return "yes", "Free agent agreed terms.", int(p.get("value", 0) * 0.28 or fee)
    sq = squad(w, seller_id)
    value = int(p.get("value", 0) or 1)
    tops = sorted(sq, key=lambda x: -float(x.get("overall", 70)))[:3]
    star = p["id"] in {x["id"] for x in tops}
    want = int(value * (1.48 if star else 1.32 if rounds == 1 else 1.18))
    if len(sq) <= 18:
        return "short", "Squad too thin. Talks closed.", want
    if club(w, buyer_id).get("budget", 0) < 0:
        return "no", "Sort your books first.", want
    if rounds >= 4 and fee < want:
        return "no", "Talks collapsed.", want
    if fee + 50_000 < want:
        return "talk", f"Not enough. We want £{want:,}.", want
    if rounds < 2 and float(p.get("overall", 70)) >= 82:
        return "talk", f"Directors want another look. Floor is £{want:,}.", want
    return "yes", "Both boards signed. Papers going through.", want


def open_offer(w: dict, pid: int, buyer_id: int, years: int = 3, fee: int | None = None) -> dict:
    p = player(w, pid)
    fee = int(fee if fee is not None else p.get("value", 0) * 1.08)
    oid = 1 + max((o["id"] for o in w.get("offers", [])), default=0)
    wait = 1 if float(p.get("overall", 70)) < 82 else 2
    today = parse_d(w["meta"]["current_date"])
    offer = {
        "id": oid,
        "pid": pid,
        "buyer_id": buyer_id,
        "seller_id": p["club_id"],
        "fee": fee,
        "years": max(1, min(5, years)),
        "status": "processing",
        "reply": "Offer being processed.",
        "created": w["meta"]["current_date"],
        "resolve": fmt_d(today + timedelta(days=wait)),
        "rounds": 1,
    }
    w.setdefault("offers", []).append(offer)
    uid = w.get("user", {}).get("club_id")
    if buyer_id == uid or p["club_id"] == uid:
        add_news(w, f"Bid lodged for {p['last_name']}. {offer['reply']}", "desk", True)
    if float(p["overall"]) >= 78:
        add_news(
            w,
            press.fill(
                "rumour",
                buyer=club_name(w, buyer_id),
                seller=club_name(w, p["club_id"]),
                player=f"{p['first_name']} {p['last_name']}",
            ),
            "wire",
            True,
            club_id=None,
        )
    return offer


def resolve_offers(w: dict) -> None:
    today = w["meta"]["current_date"]
    uid = w.get("user", {}).get("club_id")
    for off in w.get("offers", []):
        if off["status"] != "processing" or off["resolve"] > today:
            continue
        try:
            p = player(w, off["pid"])
        except StopIteration:
            off["status"] = "dead"
            continue
        if p["club_id"] != off["seller_id"]:
            off["status"] = "dead"
            off["reply"] = "Player already moved."
            continue
        if off["seller_id"] == uid:
            off["status"] = "awaiting"
            off["reply"] = f"{club_name(w, off['buyer_id'])} bid £{off['fee']:,}. Accept, reject, or ask more."
            add_news(w, off["reply"] + f" ({p['last_name']})", "desk", True)
            continue
        status, reply, want = _seller_reply(w, p, off["buyer_id"], off["fee"], int(off.get("rounds", 1)))
        off["reply"] = reply
        off["want"] = want
        if status == "talk":
            off["rounds"] = int(off.get("rounds", 1)) + 1
            if off["buyer_id"] == uid:
                off["status"] = "counter"
                add_news(w, f"{p['last_name']}: {reply} Meet it or type a new bid.", "desk", True)
                continue
            buyer = club(w, off["buyer_id"])
            if buyer.get("budget", 0) >= want and want <= int(p.get("value", 0) * 1.7):
                off["fee"] = want
                off["status"] = "processing"
                off["resolve"] = fmt_d(parse_d(today) + timedelta(days=1))
            else:
                off["status"] = "rejected"
                off["reply"] = "They would not meet the asking price."
            continue
        if status != "yes":
            off["status"] = "rejected"
            if off["buyer_id"] == uid:
                add_news(w, f"{p['last_name']}: {reply}", "desk", True)
            if float(p["overall"]) >= 80:
                add_news(
                    w,
                    press.fill(
                        "reject",
                        seller=club_name(w, off["seller_id"]),
                        buyer=club_name(w, off["buyer_id"]),
                        player=f"{p['first_name']} {p['last_name']}",
                    ),
                    "wire",
                    True,
                    club_id=None,
                )
            continue
        off["status"] = "signed"
        complete_transfer(w, off["pid"], off["buyer_id"], off["fee"], off.get("years", 3))


def user_offer_action(w: dict, oid: int, action: str) -> str:
    off = next((o for o in w.get("offers", []) if o["id"] == oid), None)
    if not off or off["status"] not in ("awaiting", "counter"):
        return "no offer"
    p = player(w, off["pid"])
    if action == "accept":
        off["status"] = "signed"
        off["reply"] = "You accepted the bid."
        complete_transfer(w, off["pid"], off["buyer_id"], off["fee"], off.get("years", 3))
        return "accepted"
    if action == "reject":
        off["status"] = "rejected"
        off["reply"] = "You rejected the bid."
        add_news(w, f"You rejected {club_name(w, off['buyer_id'])} for {p['last_name']}.", "desk", True)
        return "rejected"
    if action == "meet":
        want = int(off.get("want") or off.get("ask") or off["fee"])
        off["fee"] = want
        off["status"] = "processing"
        off["resolve"] = fmt_d(parse_d(w["meta"]["current_date"]) + timedelta(days=1))
        off["reply"] = f"You matched £{want:,}. Papers moving."
        add_news(w, f"{p['last_name']}: matched their ask £{want:,}.", "desk", True)
        return "met"
    if action in ("raise", "counter"):
        extra = off.get("ask")
        fee = int(extra) if extra else int(off.get("want") or off["fee"] * 1.18)
        off["fee"] = fee
        if off["status"] == "counter":
            off["status"] = "processing"
            off["resolve"] = fmt_d(parse_d(w["meta"]["current_date"]) + timedelta(days=1))
            off["reply"] = f"New bid £{fee:,} sent."
            add_news(w, f"{p['last_name']}: you bid £{fee:,}.", "desk", True)
            return "countered"
        buyer = club(w, off["buyer_id"])
        if buyer["budget"] >= fee and float(p["overall"]) <= max_buy_ovr(w, buyer["id"]) + 1:
            off["status"] = "signed"
            off["reply"] = f"{buyer['name']} met £{fee:,}."
            complete_transfer(w, off["pid"], off["buyer_id"], fee, off.get("years", 3))
            return "raised-ok"
        off["status"] = "rejected"
        off["reply"] = f"{buyer['name']} walked away from £{fee:,}."
        add_news(w, off["reply"], "desk", True)
        return "raised-no"
    return "no"


def try_buy(w: dict, pid: int, years: int = 3, fee: int | None = None) -> str:
    uid = w["user"]["club_id"]
    p = player(w, pid)
    ok, why, auto = can_buy(w, uid, p)
    if not ok:
        add_news(w, f"Bid for {p['last_name']} failed. {why}", "desk", True)
        return why
    if any(o["status"] in ("processing", "counter") and o["pid"] == pid and o["buyer_id"] == uid for o in w.get("offers", [])):
        return "Already processing."
    open_offer(w, pid, uid, years, int(fee) if fee else auto)
    return "processing"


def try_sell(w: dict, pid: int) -> str:
    uid = w["user"]["club_id"]
    p = player(w, pid)
    if p["club_id"] != uid:
        return "Not yours."
    if not window_open(w):
        return "Window is shut."
    buyers = [c for c in w["clubs"] if c["id"] != uid]
    random.shuffle(buyers)
    for c in buyers:
        ok, _, fee = can_buy(w, c["id"], {**p, "club_id": uid})
        if ok:
            open_offer(w, pid, c["id"], 3, int(p.get("value", fee) * 0.95))
            add_news(w, f"{p['last_name']} offered out. Clubs are talking.", "desk", True)
            return "listed"
    add_news(w, f"No club opened talks for {p['last_name']}.", "desk", True)
    return "no buyer"


COACH_NAMES = [
    "H. Walsh", "M. Ortega", "S. Keane", "L. Varga", "P. Nilsen",
    "A. Moreau", "J. Silva", "R. Bennett", "K. Okonkwo", "T. Ricci",
    "D. Fraser", "E. Holm", "C. Duarte", "N. Petrov", "B. Clarke",
]


def ensure_staff(w: dict) -> None:
    styles = ["possession", "balanced", "quick_counter", "long_ball", "park_bus"]
    forms = list(FORMATIONS)
    used = {c.get("coach") for c in w["clubs"]}
    names = [n for n in COACH_NAMES]
    random.shuffle(names)
    i = 0
    for c in w["clubs"]:
        if not c.get("coach"):
            while i < len(names) and names[i] in used:
                i += 1
            c["coach"] = names[i % len(names)] if names else "Staff"
            used.add(c["coach"])
            i += 1
        c.setdefault("style", random.choice(styles))
        c.setdefault("formation", random.choice(forms))
        c.setdefault("stance", random.choice(["attacking", "balanced", "defensive"]))
        c.setdefault("bank_rate", 0.02)
        if not c.get("sponsors"):
            c["sponsors"] = [dict(random.choice(SPON.CATALOG))]


def _weak_role(w: dict, cid: int) -> str:
    sq = squad(w, cid)
    if not sq:
        return "ST"
    lines = {"GK": [], "DEF": [], "MID": [], "ATT": []}
    for p in sq:
        code = (p.get("roles") or [{"code": "CM"}])[0]["code"]
        if code == "GK":
            lines["GK"].append(p["overall"])
        elif code in ("CB", "LB", "RB"):
            lines["DEF"].append(p["overall"])
        elif code in ("ST", "LW", "RW"):
            lines["ATT"].append(p["overall"])
        else:
            lines["MID"].append(p["overall"])
    avg = {k: (sum(v) / len(v) if v else 99) for k, v in lines.items()}
    return min(avg, key=avg.get)


SCOUT_REGIONS = {
    "africa": {"Zambia", "Egypt", "South Africa", "Morocco", "Nigeria", "Ghana", "Tunisia", "Kenya", "Senegal", "Algeria"},
    "europe": {"England", "Spain", "Italy", "Germany", "France", "Portugal", "Netherlands", "Belgium", "Croatia"},
}

SCOUTS = {
    "peter": {"name": "Peter", "fee": 60_000, "ranks": {"E"}, "growth": True},
    "oblak": {"name": "Oblak", "fee": 140_000, "ranks": {"D", "C"}, "growth": False},
    "brent": {"name": "Brent", "fee": 280_000, "ranks": {"A", "A+"}, "growth": False},
    "s2g": {"name": "S2G", "fee": 450_000, "ranks": {"B", "A", "A+", "S"}, "growth": False},
}


def hire_scout(w: dict, region: str, who: str = "peter") -> str:
    who = who if who in SCOUTS else "peter"
    spec = SCOUTS[who]
    region = region if region in SCOUT_REGIONS else "africa"
    c = club(w, w["user"]["club_id"])
    fee = spec["fee"]
    if c["budget"] < fee:
        return "No money for a scout trip."
    c["budget"] -= fee
    today = parse_d(w["meta"]["current_date"])
    w["user"]["scout"] = {
        "region": region,
        "who": who,
        "ready": fmt_d(today + timedelta(days=3)),
        "names": [],
    }
    add_news(w, f"{spec['name']} sent to {region}. Report in three days.", "desk", True)
    return "ok"


SCOUT_FAIL = (
    "Thin market this week. No names worth the fee.",
    "Doors stayed shut. Try another region next trip.",
    "Watching lists came back empty. Change scout or region.",
    "Targets were priced past your rank ceiling.",
)


def resolve_scout(w: dict) -> None:
    sc = w.get("user", {}).get("scout")
    if not sc or sc.get("done") or sc.get("ready", "9999") > w["meta"]["current_date"]:
        return
    cid = w["user"]["club_id"]
    spec = SCOUTS.get(sc.get("who"), SCOUTS["peter"])
    need = _weak_role(w, cid)
    lines = {
        "GK": ("GK",),
        "DEF": ("CB", "LB", "RB"),
        "MID": ("CM", "CDM", "CAM", "LM", "RM"),
        "ATT": ("ST", "LW", "RW"),
    }
    want = lines[need]
    cap = max_buy_ovr(w, cid)
    nats = SCOUT_REGIONS.get(sc["region"], set())
    found = []

    def consider(p, rank_ok: bool) -> None:
        if p.get("retired") or p.get("club_id") == cid:
            return
        pos = (p.get("roles") or [{"code": "CM"}])[0]["code"]
        ovr = float(p["overall"])
        pot = float(p.get("potential", ovr))
        is_fa = not p.get("club_id")
        club_nat = "" if is_fa else club(w, p["club_id"]).get("nation", "")
        if p.get("nation") not in nats and club_nat not in nats and not is_fa:
            return
        if not rank_ok and not is_fa:
            if team_rank(w, p["club_id"]) not in spec["ranks"]:
                return
        if spec.get("growth") and pot < ovr + 4 and not is_fa:
            return
        if ovr > cap + 1.5:
            return
        score = ovr + pot * (0.4 if spec.get("growth") else 0.15)
        if pos in want:
            score += 6
        if is_fa:
            score += 8
        found.append((score, p))

    for p in w["players"]:
        consider(p, True)
    if len(found) < 4:
        for p in w["players"]:
            consider(p, False)
    found.sort(key=lambda x: -x[0])
    seen = set()
    names = []
    for _, p in found:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        names.append(p["id"])
        if len(names) >= 8:
            break
    sc["names"] = names
    sc["done"] = True
    if names:
        add_news(w, f"{spec['name']}: {len(names)} names in {sc['region']} (need {need}).", "desk", True)
    else:
        add_news(w, f"{spec['name']}: {random.choice(SCOUT_FAIL)}", "desk", True)


def ai_window_tick(w: dict) -> None:
    if not window_open(w):
        return
    ensure_staff(w)
    uid = w.get("user", {}).get("club_id")
    if random.random() < 0.35:
        add_news(w, press.fill("window"), "wire", True, club_id=None)
    # one smart bid: club buys for its weak line
    # sometimes bid for a user player so you can accept / reject / raise
    if uid and random.random() < 0.28:
        mine = [p for p in squad(w, uid) if float(p.get("overall", 70)) < 90]
        if mine:
            p = random.choice(mine)
            buyers_u = [c for c in w["clubs"] if c["id"] != uid]
            random.shuffle(buyers_u)
            for c in buyers_u[:8]:
                ok, _, fee = can_buy(w, c["id"], p)
                if ok:
                    open_offer(w, p["id"], c["id"], 3, fee)
                    break
    buyers = [c for c in w["clubs"] if c["id"] != uid]
    random.shuffle(buyers)
    for c in buyers[:6]:
        need = _weak_role(w, c["id"])
        want = {
            "GK": ("GK",),
            "DEF": ("CB", "LB", "RB"),
            "MID": ("CM", "CDM", "CAM"),
            "ATT": ("ST", "LW", "RW"),
        }[need]
        pool = [
            p for p in w["players"]
            if not p.get("retired") and p.get("club_id") not in (c["id"], uid)
            and (p.get("roles") or [{"code": "CM"}])[0]["code"] in want
        ]
        if not pool:
            continue
        my_nat = c.get("nation", "")
        AFR = SCOUT_REGIONS["africa"]
        EUR = SCOUT_REGIONS["europe"]
        if random.random() < 0.4:
            if my_nat in AFR:
                cross = [p for p in pool if p.get("nation") in EUR or club(w, p["club_id"]).get("nation") in EUR]
            else:
                cross = [p for p in pool if p.get("nation") in AFR or club(w, p["club_id"]).get("nation") in AFR]
            if cross:
                pool = cross
        pool.sort(key=lambda p: -p["overall"])
        for p in pool[:12]:
            ok, _, fee = can_buy(w, c["id"], p)
            if ok:
                open_offer(w, p["id"], c["id"], random.choice([2, 3, 4]), fee)
                return


def world_colour_news(w: dict) -> None:
    if random.random() > 0.45:
        return
    c = random.choice(w["clubs"])
    kind = random.choice(["fans", "train", "league", "board"])
    sq = squad(w, c["id"])
    p = random.choice(sq) if sq else None
    kw = {
        "club": c["name"],
        "coach": c.get("coach", "the coach"),
        "league": next((l["name"] for l in w["leagues"] if l["id"] == c["league_id"]), "the league"),
        "player": f"{p['first_name']} {p['last_name']}" if p else "a youngster",
        "place": "mid-table",
    }
    if kind == "board" and random.random() < 0.25:
        old = c.get("coach", "the coach")
        c["coach"] = random.choice(COACH_NAMES)
        add_news(w, press.fill("board", **{**kw, "coach": old}), "wire", True, club_id=None)
        return
    add_news(w, press.fill(kind, **kw), "wire", True, club_id=None)


def prize_money(place: int) -> int:
    top = {1: 55_000_000, 2: 46_000_000, 3: 38_000_000, 4: 32_000_000, 5: 26_000_000}
    return top.get(place, 9_000_000 - min(12, place - 6) * 400_000)


def pay_month(w: dict) -> None:
    cid = w.get("user", {}).get("club_id")
    if not cid:
        return
    c = club(w, cid)
    bill = (wage_bill(w, cid) + club_staff_wage(w, cid)) * 4
    rate = float(c.get("bank_rate", 0.02))
    if c["budget"] < 0:
        interest = int(abs(c["budget"]) * rate)
        c["budget"] -= interest
        add_news(w, f"Bank interest on the overdraft (£{interest:,}).", "desk", True)
    c["budget"] -= bill
    if c["budget"] < 0:
        add_news(w, "Wages went out on overdraft. The dressing room is restless.", "desk", True)
        for p in squad(w, cid):
            p["form"] = max(5.4, float(p.get("form", 6.6)) - 0.15)
    else:
        add_news(w, f"Monthly wages paid (£{bill:,}). Bank £{c['budget']:,}.", "desk", True)


def _formation_keys(formation: str) -> list[tuple[str, str]]:
    slots = FORMATIONS.get(formation, FORMATIONS["4-3-3"])
    return list(zip(_slot_keys(slots), slots))


def remap_xi(w: dict, new_form: str) -> None:
    """Keep the same 11 where possible; place them into the new shape."""
    from engine.match import player_presence

    u = w["user"]
    sq = {p["id"]: p for p in squad(w, u["club_id"])}
    current = [sq[pid] for pid in u.get("xi", {}).values() if pid in sq and not sq[pid].get("injury")]
    if len(current) < 11:
        extra = [p for p in squad(w, u["club_id"]) if p not in current and not p.get("injury")]
        extra.sort(key=lambda p: -float(p.get("overall", 70)))
        current.extend(extra[: 11 - len(current)])
    placed = {}
    used = set()
    for key, role in _formation_keys(new_form):
        leftover = [p for p in current if p["id"] not in used]
        if not leftover:
            break
        pick = max(leftover, key=lambda p: player_presence(p, role))
        placed[key] = pick["id"]
        used.add(pick["id"])
    u["xi"] = placed
    u["formation"] = new_form
    ensure_xi(w)


def place_player(w: dict, pid: int, to_slot: str) -> None:
    u = w["user"]
    xi = u.setdefault("xi", {})
    if to_slot == "bench":
        for k, v in list(xi.items()):
            if v == pid:
                del xi[k]
        ensure_xi(w)
        return
    occupant = xi.get(to_slot)
    from_slot = next((k for k, v in xi.items() if v == pid), None)
    if from_slot:
        if occupant:
            xi[from_slot] = occupant
        else:
            del xi[from_slot]
        xi[to_slot] = pid
    else:
        xi[to_slot] = pid
    # drop duplicate ids
    seen = set()
    clean = {}
    for k, v in xi.items():
        if v in seen:
            continue
        seen.add(v)
        clean[k] = v
    u["xi"] = clean
    ensure_xi(w)


def ensure_xi(w: dict) -> None:
    u = w["user"]
    cid = u["club_id"]
    sq = squad(w, cid)
    form = u.get("formation", "4-3-3")
    keyed = _formation_keys(form)
    valid_keys = {k for k, _ in keyed}
    u["xi"] = {k: v for k, v in u.get("xi", {}).items() if k in valid_keys}
    if not u.get("xi"):
        picked = auto_xi(sq, form)
        u["xi"] = {slot: p["id"] for slot, p in picked.items()}
    used = set(u["xi"].values())
    for key, role in keyed:
        pid = u["xi"].get(key)
        if pid and any(p["id"] == pid and not p.get("injury") for p in sq):
            continue
        avail = [p for p in sq if p["id"] not in used and not p.get("injury")]
        if avail:
            from engine.match import player_presence
            pick = max(avail, key=lambda p: player_presence(p, role))
            u["xi"][key] = pick["id"]
            used.add(pick["id"])
    used = set(u["xi"].values())
    u["bench"] = [p["id"] for p in sorted(sq, key=lambda p: -p["overall"]) if p["id"] not in used][:7]


def _slot_keys(slots: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    keys = []
    for s in slots:
        counts[s] = counts.get(s, 0) + 1
        keys.append(s if slots.count(s) == 1 else f"{s}{counts[s]}")
    return keys


def seat_for_club(w: dict, cid: int) -> dict | None:
    return w.get("seats", {}).get(str(cid))


def resolve_xi(w: dict, cid: int, formation: str | None = None, style: str | None = None) -> dict:
    seat = seat_for_club(w, cid) or (w["user"] if w.get("user", {}).get("club_id") == cid else None)
    if seat and seat.get("xi"):
        out = {}
        for slot, pid in seat["xi"].items():
            try:
                out[slot] = player(w, pid)
            except StopIteration:
                pass
        if out:
            return out
    return auto_xi(squad(w, cid), formation or "4-3-3")


def next_user_fixture(w: dict) -> dict | None:
    cid = w["user"]["club_id"]
    today = w["meta"]["current_date"]
    upcoming = [
        f
        for f in w["fixtures"]
        if not f.get("played") and (f["home_id"] == cid or f["away_id"] == cid) and f["date"] >= today
    ]
    upcoming.sort(key=lambda f: f["date"])
    return upcoming[0] if upcoming else None


def play_fixture(w: dict, fid: int) -> dict:
    fx = next(f for f in w["fixtures"] if f["id"] == fid)
    if fx.get("played"):
        return fx
    uid = w["user"]["club_id"]
    hc, ac = club(w, fx["home_id"]), club(w, fx["away_id"])
    hf = w["user"].get("formation") if fx["home_id"] == uid else hc.get("formation")
    af = w["user"].get("formation") if fx["away_id"] == uid else ac.get("formation")
    home = resolve_xi(w, fx["home_id"], hf)
    away = resolve_xi(w, fx["away_id"], af)
    def ai_plan(c, opp_id):
        pl = league_place(w, c["id"])
        table = table_for(w, c["league_id"])
        leader = table[0]["name"] if table else ""
        best = max(squad(w, c["id"]) or [{"last_name": "—", "overall": 0}], key=lambda p: float(p.get("overall", 0)))
        opp_ovr = squad_ovr(w, opp_id)
        mine = squad_ovr(w, c["id"])
        style = c.get("style", "balanced")
        stance = c.get("stance", "balanced")
        if pl <= 2:
            style, stance = "possession", "attacking"
        elif pl <= 4:
            style, stance = c.get("style", "gegenpress"), "attacking"
        elif pl >= 17:
            style, stance = "park_bus", "defensive"
        elif opp_ovr > mine + 4:
            style, stance = "low_block", "defensive"
        elif opp_ovr + 3 < mine:
            style, stance = "quick_counter", "attacking"
        c["ai_note"] = (
            f"{c.get('coach','Coach')}: {place_word(pl)} · best {best.get('last_name')} "
            f"({best.get('overall',0):.0f}) · chase {leader} · {style}/{stance}"
        )
        return style, stance
    if fx["home_id"] == uid:
        hs, hst = w["user"]["style"], w["user"].get("stance", "balanced")
    else:
        hs, hst = ai_plan(hc, fx["away_id"])
    if fx["away_id"] == uid:
        aws, ast = w["user"]["style"], w["user"].get("stance", "balanced")
    else:
        aws, ast = ai_plan(ac, fx["home_id"])
    res = simulate_match(
        home, away, hs, aws, True,
        seed=fid * 7919 + int(w["meta"]["current_date"].replace("-", "")),
        home_stance=hst, away_stance=ast,
        home_form=hf or "4-3-3", away_form=af or "4-3-3",
    )
    fx["played"] = True
    fx["home_goals"] = res["home_goals"]
    fx["away_goals"] = res["away_goals"]
    fx["report"] = {
        "events": res["events"],
        "home_strength": res["home_strength"],
        "away_strength": res["away_strength"],
        "cards": res["cards"],
        "injuries": res["injuries"],
        "ratings": res["ratings"],
    }
    apply_match_consequences(w, fx, home, away, res)
    w["results"].append({"fixture_id": fid, "hg": res["home_goals"], "ag": res["away_goals"]})
    if fx.get("cup"):
        try:
            continue_cups(w)
        except Exception:
            pass
    return fx


def apply_match_consequences(w: dict, fx: dict, home: dict, away: dict, res: dict) -> None:
    today = parse_d(w["meta"]["current_date"])
    for slot_map in (home, away):
        for p in slot_map.values():
            st = p.setdefault("season_stats", {"apps": 0, "goals": 0, "assists": 0})
            st["apps"] = st.get("apps", 0) + 1
            rat = res["ratings"].get(p["id"], 6.5)
            hist = p.setdefault("form_hist", [])
            hist.append(rat)
            p["form"] = round(sum(hist[-5:]) / len(hist[-5:]), 2)
            try:
                ag = age_from_birth(p["birthdate"], w["meta"]["current_date"])
                if ag >= 34:
                    p["form"] = round(max(5.0, float(p["form"]) - 0.12), 2)
            except Exception:
                pass
            p["condition"] = condition_tick(float(p.get("condition", 90)), True, False)
            mood = float(p.get("morale", 72))
            if rat >= 7.2:
                mood += 4
            elif rat < 6.0:
                mood -= 5
            p["morale"] = max(38, min(99, mood))
            p["adaptation"] = min(100, float(p.get("adaptation", 70)) + 1.5)
    for inj in res["injuries"]:
        try:
            p = player(w, inj["player_id"])
        except StopIteration:
            continue
        ret = today + timedelta(days=inj["days"])
        kind = inj.get("kind", "knock")
        p["injury"] = {"days": inj["days"], "return": fmt_d(ret), "note": kind}
        p["condition"] = min(float(p.get("condition", 80)), 48)
        other = away if p["id"] in {x["id"] for x in home.values()} else home
        hit = max(other.values(), key=lambda x: float(x.get("overall", 70))) if other else None
        by = f" after a challenge by {hit['last_name']}" if hit else ""
        line = f"{p['first_name']} {p['last_name']} picked up a {kind}{by} ({inj['days']} days)."
        mine = w.get("user", {}).get("club_id")
        if p.get("club_id") == mine:
            add_news(w, line, "injury", True)
        if inj.get("big") or inj["days"] >= 90 or "break" in kind.lower() or "bone" in kind.lower() or "acl" in kind.lower():
            p["career_risk"] = True
        if inj.get("big") or inj["days"] >= 60:
            add_news(
                w,
                f"Breaking: {p['first_name']} {p['last_name']} ({club_name(w, p['club_id'])}) faces a long spell out — {kind}, about {inj['days']} days.",
                "wire",
                True,
                club_id=None,
            )
        if float(p.get("overall", 70)) >= 82:
            add_news(
                w,
                press.fill(
                    "injury",
                    player=f"{p['first_name']} {p['last_name']}",
                    club=club_name(w, p["club_id"]),
                    kind=kind,
                    days=inj["days"],
                    by=by,
                ),
                "wire",
                True,
                club_id=None,
            )
    hid, aid = fx["home_id"], fx["away_id"]
    hg, ag = fx["home_goals"], fx["away_goals"]
    if hg > ag:
        bump_form(w, hid, 7 if fx.get("cup") else 6)
        bump_form(w, aid, -4)
    elif ag > hg:
        bump_form(w, aid, 7 if fx.get("cup") else 6)
        bump_form(w, hid, -4)
    else:
        bump_form(w, hid, 1)
        bump_form(w, aid, 1)
    uid = w.get("user", {}).get("club_id")
    if hid == uid or aid == uid:
        add_news(w, f"{club_name(w, hid)} {hg}–{ag} {club_name(w, aid)}", "result", True)
        if hid == uid and hg > ag:
            pay_sponsor_home_win(w)
            note_win_streak(w, True)
        elif uid in (hid, aid):
            gf = hg if hid == uid else ag
            ga = ag if hid == uid else hg
            note_win_streak(w, gf > ga)
    # Match scores stay on Schedule / Table — not the wire.


def sim_due_ai(w: dict) -> int:
    """Play every unplayed fixture on or before current date except user's next if same day handled by UI."""
    today = w["meta"]["current_date"]
    n = 0
    cid = w["user"]["club_id"]
    for fx in w["fixtures"]:
        if fx.get("played") or fx["date"] > today:
            continue
        if (fx["home_id"] == cid or fx["away_id"] == cid) and fx["date"] == today:
            continue
        play_fixture(w, fx["id"])
        n += 1
    return n


def heal(w: dict) -> None:
    today = w["meta"]["current_date"]
    for p in w["players"]:
        inj = p.get("injury")
        if inj and inj.get("return") <= today:
            p["injury"] = None
            p["condition"] = 78
        elif not inj:
            p["condition"] = condition_tick(float(p.get("condition", 88)), False, False)


def advance_day(w: dict) -> None:
    heal(w)
    sim_due_ai(w)
    before = window_open(w)
    d = parse_d(w["meta"]["current_date"]) + timedelta(days=1)
    w["meta"]["current_date"] = fmt_d(d)
    after = window_open(w)
    if before and not after:
        add_news(w, "Transfer window shut.", "window", True)
    if after and not before:
        add_news(w, "Transfer window open.", "window", True)
    resolve_offers(w)
    resolve_scout(w)
    announce_finished_leagues(w)
    world_colour_news(w)
    if window_open(w) and d.weekday() in (1, 3):
        ai_window_tick(w)
    if d.month == 6 and d.day == 1:
        season_turnover(w)


def human_clubs(w: dict) -> set[int]:
    out = set()
    for key in w.get("seats", {}):
        try:
            out.add(int(key))
        except ValueError:
            pass
    if w.get("user"):
        out.add(int(w["user"]["club_id"]))
    return out


def next_human_fixture(w: dict) -> dict | None:
    today = w["meta"]["current_date"]
    humans = human_clubs(w)
    due = [
        f for f in w["fixtures"]
        if not f.get("played") and f["date"] >= today
        and (f["home_id"] in humans or f["away_id"] in humans)
    ]
    due.sort(key=lambda f: (f["date"], f["id"]))
    return due[0] if due else None


def advance_to_next_match(w: dict) -> dict | None:
    mine = next_user_fixture(w)
    block = next_human_fixture(w)
    target = mine
    if block and mine and block["date"] < mine["date"] and block["id"] != mine["id"]:
        add_news(w, f"Calendar holds. {club_name(w, block['home_id'])} vs {club_name(w, block['away_id'])} must be played first.", "desk", True)
        target = block
    if not target:
        return None
    steps = 0
    while w["meta"]["current_date"] < target["date"] and steps < 2:
        advance_day(w)
        steps += 1
    heal(w)
    sim_due_ai(w)
    return next_user_fixture(w)


def season_review(w: dict) -> dict:
    cid = w["user"]["club_id"]
    lid = next(c["league_id"] for c in w["clubs"] if c["id"] == cid)
    table = table_for(w, lid)
    place = next((i for i, r in enumerate(table, 1) if r["club_id"] == cid), 20)
    row = next((r for r in table if r["club_id"] == cid), {"pts": 0, "w": 0, "d": 0, "l": 0})
    target = int(w["user"].get("target_place", 4))
    met = place <= target
    champ = table[0]["name"] if table else ""
    return {
        "place": place,
        "row": row,
        "target": target,
        "met": met,
        "champ": champ,
        "grade": "Objective met" if met else "Short of the plan",
    }


def _new_league_fixtures(w: dict, start: str) -> list[dict]:
    from datetime import date as D, timedelta
    y, m, d = (int(x) for x in start.split("-"))
    day0 = D(y, m, d)
    out = []
    fid = 1 + max((f["id"] for f in w.get("fixtures", [])), default=0)
    by_league: dict[int, list[int]] = {}
    for c in w["clubs"]:
        by_league.setdefault(c["league_id"], []).append(c["id"])
    for lid, ids in by_league.items():
        rot = list(ids)
        rng = random.Random(y * 100 + lid + int(w["meta"].get("season_start_year", y)))
        rng.shuffle(rot)
        if len(rot) % 2:
            rot.append(-1)
        n = len(rot)
        rounds = []
        circle = rot[:]
        for _ in range(n - 1):
            pairs = []
            for i in range(n // 2):
                a, b = circle[i], circle[-1 - i]
                if a != -1 and b != -1:
                    pairs.append((a, b))
            rounds.append(pairs)
            circle = [circle[0]] + [circle[-1]] + circle[1:-1]
        md = 0
        for extra in (False, True):
            for pairs in rounds:
                md += 1
                dt = day0 + timedelta(days=(md - 1) * 7)
                for i, (a, b) in enumerate(pairs):
                    flip = ((md + i) % 2 == 1)
                    home, away = (b, a) if flip else (a, b)
                    if extra:
                        home, away = away, home
                    out.append({
                        "id": fid,
                        "league_id": lid,
                        "week": md,
                        "date": dt.isoformat(),
                        "home_id": home,
                        "away_id": away,
                        "played": False,
                    })
                    fid += 1
    out.extend(_first_cup_rounds(w, out, y))
    return out


def _cup_titles(lg: dict) -> list[tuple[str, str]]:
    name = lg.get("name", "")
    if "Premier" in name and "Egypt" not in name:
        return [("FA Cup", "fa"), ("League Cup", "lc")]
    if "Primeira" in name:
        return [("Taça de Portugal", "fa"), ("Taça da Liga", "lc")]
    if "Eredivisie" in name:
        return [("KNVB Cup", "fa")]
    if "Belgian" in name:
        return [("Belgian Cup", "fa")]
    if "La Liga" in name:
        return [("Copa del Rey", "fa"), ("Copa", "lc")]
    if "Serie" in name:
        return [("Coppa Italia", "fa")]
    if "Bundesliga" in name:
        return [("DFB-Pokal", "fa")]
    if "Ligue" in name:
        return [("Coupe de France", "fa")]
    if "Egypt" in name:
        return [("Egypt Cup", "fa")]
    if "Zambia" in name:
        return [("ABSA Cup", "fa")]
    if "South Africa" in name or "Premiership" in name:
        return [("Nedbank Cup", "fa")]
    if "Botola" in name or "Morocco" in name:
        return [("Throne Cup", "fa")]
    if "Nigeria" in name:
        return [("FA Cup Nigeria", "fa")]
    if "Ghana" in name:
        return [("FA Cup Ghana", "fa")]
    if "Tunisia" in name:
        return [("Tunisia Cup", "fa")]
    return [(f"{name} Cup", "fa")]


def _first_cup_rounds(w: dict, existing: list, year: int) -> list:
    fid = 1 + max((f["id"] for f in existing), default=0)
    extra = []
    for lg in w["leagues"]:
        ids = [c["id"] for c in w["clubs"] if c["league_id"] == lg["id"]]
        if len(ids) < 4:
            continue
        for title, kind in _cup_titles(lg):
            rng = random.Random(year * 17 + lg["id"] + (0 if kind == "fa" else 9))
            draw = ids[:]
            rng.shuffle(draw)
            if len(draw) % 2:
                draw.pop()
            start = date(year, 9, 23) if kind == "lc" else date(year, 10, 7)
            for i in range(0, len(draw), 2):
                extra.append({
                    "id": fid,
                    "league_id": lg["id"],
                    "cup": title,
                    "cup_kind": kind,
                    "round": 1,
                    "week": 0,
                    "date": start.isoformat(),
                    "home_id": draw[i],
                    "away_id": draw[i + 1],
                    "played": False,
                })
                fid += 1
    return extra


def continue_cups(w: dict) -> None:
    by = {}
    for fx in w["fixtures"]:
        if not fx.get("cup"):
            continue
        if fx.get("phase") in ("league", "group", "qualifying"):
            continue
        key = (fx["cup"], int(fx.get("round", 1) or 1), fx.get("league_id"))
        by.setdefault(key, []).append(fx)
    if any(f.get("id") == "next-built" for f in w.get("fixtures", [])):
        return
    fid = 1 + max((f["id"] for f in w["fixtures"] if isinstance(f.get("id"), int)), default=0)
    seen_next = {(f.get("cup"), int(f.get("round", 1) or 1)) for f in w["fixtures"] if f.get("cup")}
    for (title, rnd, lid), matches in list(by.items()):
        if any(not m.get("played") for m in matches):
            continue
        if (title, rnd + 1) in seen_next:
            continue
        if len(matches) <= 1:
            if matches and matches[0].get("played"):
                hg, ag = matches[0].get("home_goals", 0), matches[0].get("away_goals", 0)
                winner = matches[0]["home_id"] if hg >= ag else matches[0]["away_id"]
                add_news(w, f"{club_name(w, winner)} win the {title}.", "wire", True, club_id=None)
                if winner == w.get("user", {}).get("club_id"):
                    add_trophy(w, title)
            continue
        winners = []
        last_date = matches[0]["date"]
        for m in matches:
            last_date = max(last_date, m["date"])
            hg, ag = m.get("home_goals", 0), m.get("away_goals", 0)
            winners.append(m["home_id"] if hg >= ag else m["away_id"])
        byes = w.setdefault("cup_byes", {}).setdefault(title, [])
        winners.extend(byes)
        w["cup_byes"][title] = []
        nxt = fmt_d(parse_d(last_date) + timedelta(days=21))
        i = 0
        while i + 1 < len(winners):
            w["fixtures"].append({
                "id": fid,
                "league_id": lid,
                "cup": title,
                "phase": "knockout",
                "round": rnd + 1,
                "week": 0,
                "date": nxt,
                "home_id": winners[i],
                "away_id": winners[i + 1],
                "played": False,
            })
            fid += 1
            i += 2
        if i < len(winners):
            w.setdefault("cup_byes", {}).setdefault(title, []).append(winners[i])


def _regen_player(w: dict, old: dict) -> dict:
    pid = 1 + max((x["id"] for x in w["players"] if isinstance(x.get("id"), int)), default=0)
    y = int(w["meta"].get("season_start_year", 2026))
    firsts = [x.get("first_name", "Alex") for x in w["players"] if x.get("nation") == old.get("nation")]
    lasts = [x.get("last_name", "Young") for x in w["players"] if x.get("nation") == old.get("nation")]
    ovr = round(random.uniform(58, 67), 1)
    pot = round(min(88, ovr + random.uniform(8, 18)), 1)
    kid = {
        "id": pid,
        "first_name": random.choice(firsts or ["Alex", "Jamie", "Sam"]),
        "last_name": random.choice(lasts or ["Ndlovu", "Costa", "Berg"]),
        "birthdate": f"{y - 18}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        "nation": old.get("nation", "England"),
        "club_id": 0,
        "overall": ovr,
        "potential": pot,
        "roles": list(old.get("roles") or [{"code": "CM", "fit": 1}]),
        "skills": grow_skills({k: random.uniform(48, 64) for k in ("pace", "passing", "shooting", "dribbling", "defence", "physical", "gk")}, 0, old.get("roles")),
        "value": compute_value(ovr, 18),
        "adaptation": 40,
        "condition": 90,
        "form": 6.4,
        "foot": old.get("foot", "R"),
        "height_cm": old.get("height_cm", 180),
        "injury": None,
        "retired": False,
        "season_stats": {"apps": 0, "goals": 0, "assists": 0},
        "contract_years": 3,
    }
    old_club = old.get("club_id")
    if random.random() < 0.55:
        kid["club_id"] = 0
    else:
        pool = [
            c["id"] for c in w["clubs"]
            if c["id"] != old_club and len(squad(w, c["id"])) < 26
        ]
        kid["club_id"] = random.choice(pool) if pool else 0
    w["players"].append(kid)
    return kid


def _should_retire(p: dict, age: int, apps: int) -> bool:
    if age >= 41:
        return True
    if p.get("career_risk") and age >= 34 and random.random() < 0.42:
        return True
    if age < 36:
        return False
    chance = 0.18 + (age - 36) * 0.14
    if apps < 8:
        chance += 0.22
    if float(p.get("form", 6.6)) < 6.2:
        chance += 0.12
    if float(p.get("overall", 70)) < 72:
        chance += 0.18
    if p.get("injury"):
        chance += 0.1
    return random.random() < min(0.92, chance)


def season_turnover(w: dict) -> None:
    today = w["meta"]["current_date"]
    retired = []
    uid = w.get("user", {}).get("club_id")
    for p in w["players"]:
        if p.get("retired"):
            continue
        age = age_from_birth(p["birthdate"], today)
        st = p.get("season_stats") or {}
        apps = int(st.get("apps", 0))
        delta = growth_delta(
            age,
            float(p["overall"]),
            float(p.get("potential", p["overall"] + 2)),
            apps,
            int(st.get("goals", 0)),
            int(st.get("assists", 0)),
        )
        p["overall"] = round(max(40.0, min(99.9, float(p["overall"]) + delta)), 1)
        p["skills"] = grow_skills(p.get("skills"), delta, p.get("roles"))
        p["value"] = compute_value(p["overall"], age)
        p["season_stats"] = {"apps": 0, "goals": 0, "assists": 0}
        p["condition"] = 88
        if age >= 34:
            p["form"] = round(max(5.2, 6.6 - (age - 33) * 0.25), 2)
        else:
            p["form"] = 6.6
        if _should_retire(p, age, apps):
            p["retired"] = True
            retired.append(p)
    for p in retired:
        kid = _regen_player(w, p)
        club_nm = club_name(w, p.get("club_id") or uid or 0)
        if p.get("club_id") == uid or float(p.get("overall", 0)) >= 75:
            add_news(w, f"{p['first_name']} {p['last_name']} retired at {club_nm}.", "board", True)
            add_news(
                w,
                press.fill("retire", player=f"{p['first_name']} {p['last_name']}", club=club_nm),
                "wire",
                True,
                club_id=None,
            )
            dest = "as a free agent" if not kid.get("club_id") else f"at {club_name(w, kid['club_id'])}"
            add_news(w, f"{kid['first_name']} {kid['last_name']} (18, {kid['overall']:.0f}) is on the market {dest}.", "desk", True)


def leaders(w: dict, lid: int, stat: str, n: int = 8) -> list:
    rows = []
    for p in w["players"]:
        if p.get("retired"):
            continue
        try:
            if club(w, p["club_id"])["league_id"] != lid:
                continue
        except StopIteration:
            continue
        val = int(p.get("season_stats", {}).get(stat, 0))
        if val:
            rows.append((val, p))
    rows.sort(key=lambda x: -x[0])
    return rows[:n]


def announce_finished_leagues(w: dict) -> None:
    w.setdefault("crowned", [])
    season = w["meta"].get("season")
    for lg in w["leagues"]:
        key = f"{season}-{lg['id']}"
        if key in w["crowned"]:
            continue
        fx = [f for f in w["fixtures"] if f.get("league_id") == lg["id"]]
        if not fx or any(not f.get("played") for f in fx):
            continue
        table = table_for(w, lg["id"])
        if not table:
            continue
        champ = table[0]
        add_news(w, f"{champ['name']} are {lg['name']} champions.", "wire", True, club_id=None)
        boot = leaders(w, lg["id"], "goals", 1)
        ast = leaders(w, lg["id"], "assists", 1)
        if boot:
            p = boot[0][1]
            add_news(w, f"{lg['name']} golden boot: {p['first_name']} {p['last_name']} ({boot[0][0]}).", "wire", True, club_id=None)
        if ast:
            p = ast[0][1]
            add_news(w, f"{lg['name']} top creator: {p['first_name']} {p['last_name']} ({ast[0][0]}).", "wire", True, club_id=None)
        w["crowned"].append(key)


def add_trophy(w: dict, title: str) -> None:
    w["user"].setdefault("trophies", []).append({
        "title": title,
        "season": w["meta"].get("season"),
        "date": w["meta"]["current_date"],
    })
    low = title.lower()
    if any(k in low for k in ("cup", "pokal", "taça", "taca", "coupe", "coppa")):
        pay_sponsor_cup(w, title)


def take_seat(w: dict, club_id: int, name: str, account: str | None = None) -> None:
    w.setdefault("seats", {})
    for k, s in list(w["seats"].items()):
        same = (account and s.get("account") == account) or ((not account) and s.get("manager_name") == name)
        if same and str(k) != str(club_id):
            w["seats"].pop(k, None)
    key = str(club_id)
    if key not in w["seats"]:
        w["seats"][key] = {
            "manager_name": name,
            "account": account or name,
            "club_id": club_id,
            "formation": "4-3-3",
            "style": "balanced",
            "stance": "balanced",
            "xi": {},
            "bench": [],
            "sponsors": [],
            "trophies": [],
            "fan_mood": 58,
            "win_streak": 0,
        }
    w["seats"][key]["account"] = account or w["seats"][key].get("account") or name
    w["user"] = w["seats"][key]
    club(w, club_id)["form_meter"] = 12
    club(w, club_id)["human"] = True
    ensure_xi(w)
    add_news(w, f"{name} sat down at {club_name(w, club_id)}.", "desk", True)


def leave_seat(w: dict, club_id: int) -> None:
    key = str(club_id)
    name = w.get("seats", {}).get(key, {}).get("manager_name", "A manager")
    w.get("seats", {}).pop(key, None)
    add_news(w, f"{name} left the table.", "desk", True)
    left = list(w.get("seats", {}).values())
    w["user"] = left[0] if left else w.get("user")


def lobby_count(w: dict) -> tuple[int, int]:
    lob = w.setdefault("lobby", {"needed": 2})
    ready = sum(1 for s in w.get("seats", {}).values() if s.get("ready"))
    return ready, int(lob.get("needed", 2))


def set_ready(w: dict, on: bool = True) -> None:
    w["user"]["ready"] = bool(on)
    n, need = lobby_count(w)
    who = w["user"].get("manager_name", "Manager")
    add_news(w, f"{who} is ready ({n}/{need})." if on else f"{who} is not ready.", "desk", True)


def start_next_season(w: dict) -> None:
    rev = season_review(w)
    y = int(w["meta"].get("season_start_year", 2026))
    w.setdefault("history", []).append({
        "season": w["meta"].get("season", f"{y}-{str(y+1)[2:]}"),
        "place": rev["place"],
        "pts": rev["row"]["pts"],
        "club_id": w["user"]["club_id"],
    })
    cid = w["user"]["club_id"]
    c = club(w, cid)
    settle_sponsors(w, rev["place"])
    wages = (wage_bill(w, cid) + club_staff_wage(w, cid)) * 10
    c["budget"] -= wages
    prize = prize_money(rev["place"])
    c["budget"] += prize
    announce_finished_leagues(w)
    if rev["place"] == 1:
        add_trophy(w, f"{next(l['name'] for l in w['leagues'] if l['id']==c['league_id'])} champions")
    for lg in w["leagues"]:
        awards = league_awards(w, lg["id"])
        bits = []
        for label, key in (("Golden boot", "golden_boot"), ("Assists", "playmaker"), ("Young player", "young")):
            p = awards.get(key)
            if not p:
                continue
            bits.append(f"{label} {p['last_name']} ({int(p.get('season_stats',{}).get('goals' if key!='playmaker' else 'assists',0))})")
            if p.get("club_id") == cid:
                add_trophy(w, f"{lg['name']} {label} — {p['last_name']}")
        if bits:
            add_news(w, f"{lg['name']} awards: " + " · ".join(bits), "wire", True, club_id=None)
    awards = league_awards(w, c["league_id"])
    mood = int(w["user"].get("fan_mood", 60))
    mood = min(99, mood + (12 if rev["place"] <= 4 else -8 if rev["place"] >= 16 else 0))
    w["user"]["fan_mood"] = mood
    add_news(w, f"Fans ({mood}): " + ("the stands are loud." if mood >= 70 else "patience is thin." if mood < 50 else "the crowd will travel."), "desk", True)
    if c["budget"] < 0:
        c["budget"] = prize + 8_000_000
    add_news(w, f"Season payroll £{wages:,}. Prize £{prize:,}. Bank £{c['budget']:,}.", "desk", True)
    add_news(
        w,
        f"Season closed. {place_word(rev['place'])}. {rev['grade']}. "
        f"{rev['champ']} are champions. League prize £{prize:,} in the bank.",
        "board",
        True,
    )
    add_news(
        w,
        f"WIRE — {rev['champ']} take the title. Prize money paid down the table.",
        "wire",
        True,
        club_id=None,
    )
    y += 1
    w["meta"]["season_start_year"] = y
    w["meta"]["season"] = f"{y}-{str(y + 1)[2:]}"
    w["meta"]["current_date"] = f"{y}-06-15"
    w["meta"]["ha_fixed"] = False
    season_turnover(w)
    w["archive_fixtures"] = w.get("archive_fixtures", []) + [f for f in w["fixtures"] if f.get("played")]
    w["meta"]["tickets"] = europe_tickets_from_tables(w)
    w["meta"]["europe_on"] = True
    w["fixtures"] = _new_league_fixtures(w, f"{y}-08-21")
    w["results"] = []
    repair_home_away(w)
    ensure_cups(w)
    ensure_xi(w)
    tix = w["meta"]["tickets"]
    add_news(
        w,
        f"{w['meta']['season']} underway. Europe opens: "
        f"UCL {len(tix.get('UCL',[]))} · EL {len(tix.get('Europa League',[]))} · UECL {len(tix.get('Conference League',[]))}.",
        "window",
        True,
    )


def note_win_streak(w: dict, won: bool) -> None:
    u = w["user"]
    if won:
        u["win_streak"] = int(u.get("win_streak", 0)) + 1
        if u["win_streak"] and u["win_streak"] % 5 == 0:
            c = club(w, u["club_id"])
            pay = 0
            for s in u.get("sponsors", []):
                pay += int(s.get("streak", 5_000))
            c["budget"] += pay
            add_news(w, f"Five-game run. Sponsor streak bonus £{pay:,}.", "desk", True)
    else:
        u["win_streak"] = 0


def league_awards(w: dict, lid: int) -> dict:
    rows = [p for p in w["players"] if club(w, p["club_id"])["league_id"] == lid and not p.get("retired")]
    if not rows:
        return {}
    boot = max(rows, key=lambda p: int(p.get("season_stats", {}).get("goals", 0)))
    young = [p for p in rows if age_from_birth(p["birthdate"], w["meta"]["current_date"]) <= 23]
    yp = max(young, key=lambda p: float(p.get("overall", 70))) if young else boot
    play = max(rows, key=lambda p: int(p.get("season_stats", {}).get("assists", 0)) + int(p.get("season_stats", {}).get("goals", 0)))
    return {"golden_boot": boot, "young": yp, "playmaker": play, "club_poty": boot}


def pay_sponsor_home_win(w: dict) -> None:
    c = club(w, w["user"]["club_id"])
    total = 0
    for s in w["user"].get("sponsors", []):
        total += int(s.get("per_home_win", 0))
    if total:
        c["budget"] += total
        add_news(w, f"Home-win sponsor bonus £{total:,}.", "desk", True)


def sign_sponsor(w: dict, sid: str) -> str:
    slots = w["user"].setdefault("sponsors", [])
    if any(s["id"] == sid for s in slots):
        return "already"
    if len(slots) >= 3:
        return "full"
    spec = dict(SPON.get(sid))
    need = spec.get("min_rank", "E")
    if not SPON.rank_ok(team_rank(w, w["user"]["club_id"]), need):
        add_news(w, f"{spec['name']} want a {need}+ club.", "desk", True)
        return "rank"
    spec["left"] = spec["years"]
    slots.append(spec)
    add_news(w, f"Signed {spec['name']} ({spec['years']} seasons). Task: {spec['task']}.", "desk", True)
    return "ok"


def settle_sponsors(w: dict, place: int) -> None:
    c = club(w, w["user"]["club_id"])
    awards = league_awards(w, c["league_id"])
    kept = []
    for s in w["user"].get("sponsors", []):
        hit = SPON.task_ok(s.get("task", "top10"), place)
        pay = int(s.get("season", 0)) * (1.5 if hit else 0.4)
        c["budget"] += int(pay)
        if hit:
            add_news(w, f"{s['name']} bonus hit ({s['task']}). £{int(pay):,}.", "desk", True)
        else:
            add_news(w, f"{s['name']} task missed. Partial £{int(pay):,}.", "desk", True)
        kind = s.get("award")
        winner = awards.get(kind)
        if winner and winner.get("club_id") == c["id"]:
            extra = int(s.get("award_pay", 0))
            c["budget"] += extra
            add_news(w, f"{s['name']} award bonus — {winner['last_name']} (£{extra:,}).", "desk", True)
        s["left"] = int(s.get("left", 1)) - 1
        if s["left"] > 0:
            kept.append(s)
        else:
            add_news(w, f"{s['name']} contract expired.", "desk", True)
    w["user"]["sponsors"] = kept
    offer_sponsors(w)


def offer_sponsors(w: dict) -> None:
    rank = team_rank(w, w["user"]["club_id"])
    have = {s["id"] for s in w["user"].get("sponsors", [])}
    pool = [dict(s) for s in SPON.CATALOG if s["id"] not in have and SPON.rank_ok(rank, s.get("min_rank", "E"))]
    random.shuffle(pool)
    w["user"]["sponsor_mail"] = pool[:3]
    if pool:
        add_news(w, f"{len(pool[:3])} sponsor houses want talks.", "desk", True)


def pay_sponsor_cup(w: dict, title: str) -> None:
    c = club(w, w["user"]["club_id"])
    extra = 0
    for s in w["user"].get("sponsors", []):
        extra += int(s.get("season", 0)) // 8
    if extra:
        c["budget"] += extra
        add_news(w, f"{title} win — sponsor extras £{extra:,}.", "desk", True)


def place_word(n: int) -> str:
    suf = "th"
    if n % 10 == 1 and n % 100 != 11:
        suf = "st"
    elif n % 10 == 2 and n % 100 != 12:
        suf = "nd"
    elif n % 10 == 3 and n % 100 != 13:
        suf = "rd"
    return f"{n}{suf}"


def table_for(w: dict, league_id: int) -> list[dict]:
    rows = {}
    for c in league_clubs(w, league_id):
        rows[c["id"]] = {
            "club_id": c["id"],
            "name": c["name"],
            "short": c.get("short", c["name"][:3].upper()),
            "p": 0,
            "w": 0,
            "d": 0,
            "l": 0,
            "gf": 0,
            "ga": 0,
            "gd": 0,
            "pts": 0,
        }
    for fx in w["fixtures"]:
        if not fx.get("played") or fx.get("league_id") != league_id:
            continue
        h, a = rows[fx["home_id"]], rows[fx["away_id"]]
        hg, ag = fx["home_goals"], fx["away_goals"]
        h["p"] += 1
        a["p"] += 1
        h["gf"] += hg
        h["ga"] += ag
        a["gf"] += ag
        a["ga"] += hg
        if hg > ag:
            h["w"] += 1
            a["l"] += 1
            h["pts"] += 3
        elif ag > hg:
            a["w"] += 1
            h["l"] += 1
            a["pts"] += 3
        else:
            h["d"] += 1
            a["d"] += 1
            h["pts"] += 1
            a["pts"] += 1
    for r in rows.values():
        r["gd"] = r["gf"] - r["ga"]
    return sorted(rows.values(), key=lambda r: (r["pts"], r["gd"], r["gf"]), reverse=True)


def public_player(w: dict, p: dict) -> dict:
    today = w["meta"]["current_date"]
    age = age_from_birth(p["birthdate"], today)
    return {
        **{k: p.get(k) for k in (
            "id", "first_name", "last_name", "overall", "potential", "nation",
            "height_cm", "foot", "roles", "club_id", "condition", "form",
            "value", "adaptation", "injury", "season_stats",
        )},
        "age": age,
        "name": f"{p['first_name']} {p['last_name']}",
        "pos": p["roles"][0]["code"] if p.get("roles") else "CM",
    }
