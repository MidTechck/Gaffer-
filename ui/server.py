#!/usr/bin/env python3
"""Stdlib HTTP server — no pip required."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import world as W
from engine import accounts as A
from engine.sponsors import CATALOG
from engine.match import FORMATIONS, auto_xi, xi_strength


def mark(cr: dict, cid: int, size: int = 28) -> str:
    return W.badge(W.club(cr, cid), size)

STATE: dict = {"career": None, "lan": "", "worlds": {}}
PACK = None


def lan_ip() -> str:
    if STATE.get("lan"):
        return STATE["lan"]
    import socket
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        pass
    STATE["lan"] = ip
    return ip


def pack() -> dict:
    global PACK
    if PACK is None:
        PACK = W.load_json(ROOT / "data" / "world.json")
    return PACK


def bind_seat(w: dict | None, account: str | None, seat: str | None) -> dict | None:
    if not w:
        return None
    seats = w.setdefault("seats", {})
    if account:
        for k, s in seats.items():
            if s.get("account") == account:
                w["user"] = s
                return w
    if seat and seat in seats:
        w["user"] = seats[seat]
        return w
    if w.get("user"):
        return w
    return w


def career_for(handler) -> dict | None:
    ck = cookies_of(handler)
    account = A.user_of(ck.get("tok"))
    room = ck.get("room") or ""
    seat = ck.get("seat") or ""
    if room and room in STATE.get("worlds", {}):
        return bind_seat(STATE["worlds"][room], account, seat)
    if account:
        key = f"solo_{account}"
        worlds = STATE.setdefault("worlds", {})
        if key not in worlds:
            fp = ROOT / "saves" / f"user_{account}.json"
            if fp.is_file():
                worlds[key] = W.load_json(fp)
        if key in worlds:
            return bind_seat(worlds[key], account, seat)
    return bind_seat(STATE.get("career"), account, seat)


def career() -> dict | None:
    return STATE.get("career")


def set_career(c: dict, account: str | None = None) -> None:
    STATE["career"] = c
    if account:
        STATE.setdefault("worlds", {})[f"solo_{account}"] = c


def cookies_of(handler) -> dict:
    out = {}
    raw = handler.headers.get("Cookie", "")
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            out[k] = v
    return out


def who(handler) -> str | None:
    return A.user_of(cookies_of(handler).get("tok"))


def html_page(title: str, body: str, cr: dict | None, body_class: str = "") -> str:
    nav = ""
    status = ""
    if cr:
        club = W.club(cr, cr["user"]["club_id"])
        nxt = W.next_user_fixture(cr)
        nxt_s = "—"
        if nxt:
            opp = nxt["away_id"] if nxt["home_id"] == club["id"] else nxt["home_id"]
            ha = "H" if nxt["home_id"] == club["id"] else "A"
            nxt_s = f"{W.club_name(cr, opp)} ({ha}) · {nxt['date'][5:]}"
        win = "OPEN" if W.window_open(cr) else "SHUT"
        status = f"""
        <header class="top">
          <div class="brand">GAFFER</div>
          <div class="meta">
            <span>{club['name']} · {W.team_rank(cr, club['id'])}</span>
            <span>{cr['meta']['current_date']}</span>
            <span>£{club['budget']:,}</span>
            <span>Window {win}</span>
            <span>Next {nxt_s}</span>
          </div>
        </header>
        <nav class="tabs">
          <a href="/home">Home</a>
          <a href="/plan">Game plan</a>
          <a href="/team">Team</a>
          <a href="/matchday">Matchday</a>
          <a href="/table">Table</a>
          <a href="/schedule">Schedule</a>
          <a href="/market">Market</a>
          <a href="/news">News</a>
          <a href="/club">Club</a>
          <a href="/trophies">Trophies</a>
          <a href="/cups">Cups</a>
          <a href="/ucl">UCL</a>
        </nav>
        """
    lock = "desk-lock"
    if body_class:
        lock = f"desk-lock {body_class}"
    turn = '<div class="turn"><p>Turn the device sideways</p></div>' if cr else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{title} · Gaffer</title>
<link rel="stylesheet" href="/static/css/app.css">
</head>
<body class="{lock}">
{status}
<main class="page">{body}</main>
{turn}
<script src="/static/js/plan.js"></script>
<script src="/static/js/desk.js"></script>
</body></html>"""


def page_login(msg: str = "") -> str:
    return html_page("Sign in", f"""
    <section class="panel start">
      <h1>Gaffer</h1>
      <p class="lede">One account on this phone or on the hosted server.</p>
      <p class="warn">{msg}</p>
      <form method="post" action="/login" class="stack">
        <label>Username <input name="user" required minlength="3"></label>
        <button class="primary">Enter</button>
      </form>
      <p>No password. Each name keeps its own career.</p>
    </section>
    """, None)


def page_register(msg: str = "") -> str:
    return html_page("Create account", f"""
    <section class="panel start">
      <h1>Create account</h1>
      <p class="warn">{msg}</p>
      <form method="post" action="/register" class="stack">
        <label>Username <input name="user" required minlength="3"></label>
        <button class="primary">Create</button>
      </form>
      <p><a href="/">Back</a></p>
    </section>
    """, None)


def page_menu(user: str | None = None) -> str:
    if not user:
        return page_login()
    saves = []
    folder = ROOT / "saves"
    if folder.is_dir():
        for fp in sorted(folder.glob("*.json")):
            if fp.stem in ("accounts",):
                continue
            saves.append(
                f"<form method='post' action='/load' class='row tight'>"
                f"<input type='hidden' name='slot' value='{fp.stem}'>"
                f"<button>Load {fp.stem}</button></form>"
            )
    load = "".join(saves) or "<p class='muted'>No saved careers.</p>"
    pals = "".join(f"<li>{f}</li>" for f in A.friends_of(user)) or "<li class='muted'>None yet.</li>"
    port = A.port()
    link = f"http://{lan_ip()}:{port}"
    return html_page("Gaffer", f"""
    <section class="panel start office">
      <h1>Office · {user}</h1>
      <p class="lede">Same world, two clubs, one league. Season keeps looping.</p>
      <p class="muted">{link}</p>
      <div class="hub-grid">
        <a class="tile-btn" href="/new">New career</a>
        <form method="post" action="/room-create"><button class="tile-btn" type="submit">Create room</button></form>
        <a class="tile-btn" href="/lobby">Open lobby</a>
        <form method="post" action="/logout"><button class="tile-btn ghost" type="submit">Sign out</button></form>
      </div>
      <form method="post" action="/room-join" class="join-row">
        <input name="code" placeholder="6-letter room code" maxlength="6" autocomplete="off">
        <button type="submit">Join room</button>
      </form>
      <h2>Friends</h2>
      <form method="post" action="/friend" class="join-row">
        <input name="name" placeholder="Their username">
        <button type="submit">Add</button>
      </form>
      <ul class="feed">{pals}</ul>
      <h2>Saved games</h2>
      {load}
    </section>
    """, None)


def page_new() -> str:
    groups = []
    for lg in pack()["leagues"]:
        clubs = [c for c in pack()["clubs"] if c["league_id"] == lg["id"]]
        if not clubs:
            continue
        opts = "\n".join(f'<option value="{c["id"]}">{c["name"]}</option>' for c in clubs)
        groups.append(f'<optgroup label="{lg["name"]}">{opts}</optgroup>')
    return html_page("New career", f"""
    <section class="panel start office">
      <h1>New career</h1>
      <p><a href="/">Back</a></p>
      <form method="post" action="/start" class="career-form">
        <label>First name <input name="first" value="Alex" required></label>
        <label>Surname <input name="last" value="Reed" required></label>
        <label>Age <input name="age" type="number" min="25" max="70" value="38" required></label>
        <label>Nationality
          <select name="nation">
            <option>England</option><option>Scotland</option><option>Wales</option>
            <option>Ireland</option><option>France</option><option>Spain</option>
            <option>Italy</option><option>Germany</option><option>Portugal</option>
            <option>Netherlands</option><option>Brazil</option><option>Argentina</option>
            <option>Nigeria</option><option>Egypt</option><option>Japan</option>
            <option>Kenya</option><option>Ghana</option><option>South Africa</option>
            <option>Morocco</option><option>Senegal</option><option>Ivory Coast</option>
            <option>USA</option><option>Mexico</option><option>Canada</option>
            <option>Belgium</option><option>Croatia</option><option>Sweden</option>
            <option>Norway</option><option>Denmark</option><option>Poland</option>
            <option>Turkey</option><option>Greece</option><option>Serbia</option>
            <option>Australia</option><option>South Korea</option><option>China</option>
            <option>India</option><option>Saudi Arabia</option><option>UAE</option>
            <option>Colombia</option><option>Uruguay</option><option>Chile</option>
            <option>Cameroon</option><option>Algeria</option><option>Tunisia</option>
            <option>Zambia</option><option>Zimbabwe</option><option>Uganda</option>
          </select>
        </label>
        <label class="span2">Club
          <select name="club">{''.join(groups)}</select>
        </label>
        <div class="span2 stick-act">
          <button class="tile-btn" type="submit">Take the job</button>
        </div>
      </form>
    </section>
    """, None)


def page_home(cr: dict) -> str:
    W.repair_home_away(cr)
    W.ensure_cups(cr)
    W.ensure_xi(cr)
    cr.setdefault("seats", {})
    cr["seats"].setdefault(str(cr["user"]["club_id"]), cr["user"])
    club = W.club(cr, cr["user"]["club_id"])
    cid = club["id"]
    table = W.table_for(cr, club["league_id"])
    place = next((i for i, r in enumerate(table, 1) if r["club_id"] == cid), 1)
    me_row = next((r for r in table if r["club_id"] == cid), {"pts": 0, "p": 0})
    sq = W.squad(cr, cid)
    injured = [p for p in sq if p.get("injury")]
    fit = 0
    if sq:
        fit = int(sum(float(p.get("condition", 88)) for p in sq) / len(sq))
    nxt = W.next_user_fixture(cr)
    today = cr["meta"]["current_date"]
    hx = ax = None
    hs = aws = {"total": 0}
    actions = ""
    if nxt:
        hid, aid = nxt["home_id"], nxt["away_id"]
        hx = W.resolve_xi(cr, hid)
        ax = W.resolve_xi(cr, aid)
        hs = xi_strength(hx, cr["user"]["style"] if hid == cid else "balanced")
        aws = xi_strength(ax, cr["user"]["style"] if aid == cid else "balanced")
        venue = "Home" if hid == cid else "Away"
        if today >= nxt["date"]:
            actions = (
                f'<a class="btn" href="/plan">Set XI</a>'
                f'<a class="btn primary" href="/matchday">Play match</a>'
            )
        else:
            actions = (
                f'<a class="btn" href="/plan">Set XI</a>'
                f'<form method="post" action="/goto-match" class="inline">'
                f'<button class="primary" type="submit">Advance to match</button></form>'
            )
        match = f"""
        <div class="hero-fx">
          <div class="club-col">
            <div class="club-name">{mark(cr, hid, 36)} {W.club_name(cr, hid)}</div>
            <div class="st">{hs['total']:.1f}</div>
          </div>
          <div class="fx-mid">
            <div class="kick">{venue} · MD {nxt.get('week','')} · {nxt['date'][5:]}</div>
            <div class="versus">v</div>
          </div>
          <div class="club-col">
            <div class="club-name">{mark(cr, aid, 36)} {W.club_name(cr, aid)}</div>
            <div class="st">{aws['total']:.1f}</div>
          </div>
        </div>
        <div class="hero-actions">{actions}</div>
        """
    else:
        rev = W.season_review(cr)
        match = f"""
        <div class="hero-fx">
          <div class="club-col">
            <div class="club-name">Season complete</div>
            <div class="st">{W.place_word(rev['place'])}</div>
          </div>
          <div class="fx-mid">
            <div class="kick">{rev['row'].get('w',0)}W {rev['row'].get('d',0)}D {rev['row'].get('l',0)}L · {rev['row'].get('pts',0)} pts</div>
            <div class="versus">{rev['grade']}</div>
          </div>
          <div class="club-col">
            <div class="club-name">{rev['champ']}</div>
            <div class="kick">champions</div>
          </div>
        </div>
        <div class="hero-actions">
          <form method="post" action="/next-season" class="inline">
            <button class="primary" type="submit">Start next season</button>
          </form>
        </div>
        """

    idx = place - 1
    start = max(0, min(idx - 2, len(table) - 5))
    shown = table[start:start + 5] or table[:5]
    trows = []
    for r in shown:
        i = next(n for n, x in enumerate(table, 1) if x["club_id"] == r["club_id"])
        cls = "me" if r["club_id"] == cid else ""
        trows.append(f"<tr class='{cls}'><td>{i}</td><td>{mark(cr, r['club_id'], 22)} {r['short']}</td><td>{r['pts']}</td></tr>")

    played = [
        f for f in cr["fixtures"]
        if f.get("played") and (f["home_id"] == cid or f["away_id"] == cid)
    ]
    played.sort(key=lambda f: f["date"])
    form_html = []
    for fx in played[-5:]:
        hg, ag = fx["home_goals"], fx["away_goals"]
        mine = hg if fx["home_id"] == cid else ag
        theirs = ag if fx["home_id"] == cid else hg
        letter = "W" if mine > theirs else "L" if mine < theirs else "D"
        form_html.append(f"<span class='res {letter.lower()}'>{letter}</span>")
    while len(form_html) < 5:
        form_html.insert(0, "<span class='res none'>—</span>")

    news = "".join(
        f"<li><span>{n['date'][5:]}</span>{n['text']}</li>"
        for n in W.desk_news(cr)
    ) or "<li>Desk is quiet.</li>"
    inj_s = f"{len(injured)} out" if injured else "No injuries"
    return html_page("Home", f"""
    <div class="desk-top">
      <div>
        <h1>{club['name']} · {W.team_rank(cr, cid)}</h1>
        <p class="plan-sub">{place}{ 'st' if place==1 else 'nd' if place==2 else 'rd' if place==3 else 'th'} · {me_row['pts']} pts · {me_row['p']} played</p>
        <div class="meter"><i style="width:{W.form_meter(cr, cid)}%"></i></div>
        <p class="muted">Club rise {W.form_meter(cr, cid)}/100 · starts at E and climbs with results</p>
      </div>
    </div>
    <div class="desk">
      <section class="hero">{match}</section>
      <aside class="desk-side">
        <div class="tile grow">
          <h2>Table</h2>
          <table class="grid slim"><tbody>{''.join(trows)}</tbody></table>
        </div>
        <div class="tile">
          <h2>Last 5</h2>
          <div class="form-row">{''.join(form_html)}</div>
        </div>
        <div class="tile">
          <h2>Squad</h2>
          <p>{inj_s} · fit {fit}%</p>
        </div>
        <div class="tile">
          <h2>Board</h2>
          <p>Finish in the top four.</p>
        </div>
      </aside>
      <section class="inbox">
        <h2>Inbox</h2>
        <ul class="feed">{news}</ul>
      </section>
    </div>
    """, cr, body_class="home-lock")


def page_team(cr: dict) -> str:
    cards = []
    for p in sorted(W.squad(cr, cr["user"]["club_id"]), key=lambda x: -x["overall"]):
        pp = W.public_player(cr, p)
        fit = 12 if p.get("injury") else int(p.get("condition", 90))
        bar = "red" if fit < 40 else "amber" if fit < 70 else "green"
        wage = W.player_wage(cr, p)
        g = int(p.get("season_stats", {}).get("goals", 0))
        a = int(p.get("season_stats", {}).get("assists", 0))
        sell = (
            f"<form method='post' action='/sell/{p['id']}' class='inline'><button>List</button></form>"
            if W.window_open(cr) else ""
        )
        cards.append(
            f"<div class='squad-row'>"
            f"<a class='pcard wide {rarity(float(p['overall']))}' href='/player/{p['id']}'>"
            f"<span class='pc-ovr'>{p['overall']:.0f}</span>"
            f"<span class='pc-main'><span class='pc-pos'>{pp['pos']}</span>"
            f"<span class='pc-name'>{pp['name']}</span>"
            f"<span class='pc-meta'>{pp['age']} · {p.get('nation','')} · {g}G {a}A</span>"
            f"<span class='pc-meta'>value {money_s(p.get('value',0))} · wage £{wage:,.0f}</span></span>"
            f"<span class='pc-side'><span class='pc-bar {bar}' style='--fit:{fit}%'></span></span>"
            f"</a>{sell}</div>"
        )
    retired = "".join(
        f"<li>{p['first_name']} {p['last_name']} · last {p.get('overall',0):.0f}</li>"
        for p in cr["players"] if p.get("retired") and p.get("club_id") == cr["user"]["club_id"]
    )
    return html_page("Team", f"""
    <h1>Squad</h1>
    <div class="squad-list">{''.join(cards)}</div>
    <h2>Retired</h2>
    <ul class="feed">{retired or "<li>No retirements yet.</li>"}</ul>
    """, cr)


def page_player(cr: dict, pid: int) -> str:
    p = W.player(cr, pid)
    pp = W.public_player(cr, p)
    sk = p.get("skills") or {}
    skills = "".join(
        f"<tr><td>{k.title()}</td><td class='n {band(v)}'>{v:.0f}</td></tr>"
        for k, v in sk.items() if k != "gk" or pp["pos"] == "GK"
    )
    st = p.get("season_stats") or {}
    inj = p.get("injury")
    inj_s = f"Out until {inj['return']}" if inj else "Fit"
    return html_page(pp["name"], f"""
    <p class="crumb"><a href="/team">Team</a> / {pp['name']}</p>
    <h1>{pp['name']}</h1>
    <section class="grid2">
      <div class="panel">
        <p class="ovr">{p['overall']:.1f} <small>{pp['pos']}</small></p>
        <dl class="kv">
          <dt>Age / height</dt><dd>{pp['age']} / {p['height_cm']} cm</dd>
          <dt>Foot</dt><dd>{p['foot']}</dd>
          <dt>Nation</dt><dd>{p['nation']}</dd>
          <dt>Condition</dt><dd>{inj_s} · {int(p.get('condition',90))}%</dd>
          <dt>Value</dt><dd>£{p['value']:,}</dd>
          <dt>Potential</dt><dd>{p.get('potential', p['overall']):.1f}</dd>
        </dl>
      </div>
      <div class="panel">
        <h2>Season</h2>
        <dl class="kv">
          <dt>Apps</dt><dd>{st.get('apps',0)}</dd>
          <dt>Goals</dt><dd>{st.get('goals',0)}</dd>
          <dt>Form</dt><dd>{p.get('form',6.6):.1f}</dd>
        </dl>
        <h2>Skills</h2>
        <table class="grid slim">{skills}</table>
      </div>
    </section>
    """, cr)


def band(v: float) -> str:
    if v >= 80:
        return "hi"
    if v >= 65:
        return "mid"
    return "lo"


LINE_CLASS = {
    "GK": "pos-gk",
    "LB": "pos-def", "CB": "pos-def", "RB": "pos-def", "LWB": "pos-def", "RWB": "pos-def",
    "CDM": "pos-mid", "CM": "pos-mid", "CAM": "pos-mid", "LM": "pos-mid", "RM": "pos-mid",
    "LW": "pos-att", "RW": "pos-att", "ST": "pos-att",
}

# left %, top %  — attack at top, GK at bottom
PITCH_POS = {
    "4-3-3": {
        "GK": (50, 93), "LB": (11, 71), "CB1": (35, 73), "CB2": (65, 73), "RB": (89, 71),
        "CM1": (22, 40), "CM2": (50, 44), "CM3": (78, 40),
        "LW": (12, 14), "ST": (50, 8), "RW": (88, 14),
    },
    "4-4-2": {
        "GK": (50, 93), "LB": (11, 71), "CB1": (35, 73), "CB2": (65, 73), "RB": (89, 71),
        "LM": (11, 39), "CM1": (35, 42), "CM2": (65, 42), "RM": (89, 39),
        "ST1": (33, 9), "ST2": (67, 9),
    },
    "4-2-3-1": {
        "GK": (50, 93), "LB": (11, 73), "CB1": (35, 75), "CB2": (65, 75), "RB": (89, 73),
        "CDM1": (33, 50), "CDM2": (67, 50),
        "LW": (12, 22), "CAM": (50, 26), "RW": (88, 22),
        "ST": (50, 7),
    },
    "3-5-2": {
        "GK": (50, 93), "CB1": (24, 73), "CB2": (50, 75), "CB3": (76, 73),
        "LM": (9, 40), "CM1": (30, 42), "CDM": (50, 52), "CM2": (70, 42), "RM": (91, 40),
        "ST1": (33, 9), "ST2": (67, 9),
    },
    "4-1-4-1": {
        "GK": (50, 93), "LB": (11, 72), "CB1": (35, 74), "CB2": (65, 74), "RB": (89, 72),
        "CDM": (50, 55),
        "LM": (12, 34), "CM1": (34, 38), "CM2": (66, 38), "RM": (88, 34),
        "ST": (50, 8),
    },
    "4-4-1-1": {
        "GK": (50, 93), "LB": (11, 72), "CB1": (35, 74), "CB2": (65, 74), "RB": (89, 72),
        "LM": (12, 42), "CM1": (35, 46), "CM2": (65, 46), "RM": (88, 42),
        "CAM": (50, 24), "ST": (50, 8),
    },
    "4-5-1": {
        "GK": (50, 93), "LB": (11, 72), "CB1": (35, 74), "CB2": (65, 74), "RB": (89, 72),
        "LM": (10, 36), "CM1": (30, 42), "CDM": (50, 50), "CM2": (70, 42), "RM": (90, 36),
        "ST": (50, 8),
    },
    "3-4-3": {
        "GK": (50, 93), "CB1": (24, 74), "CB2": (50, 76), "CB3": (76, 74),
        "LM": (12, 44), "CM1": (36, 46), "CM2": (64, 46), "RM": (88, 44),
        "LW": (16, 14), "ST": (50, 8), "RW": (84, 14),
    },
    "5-3-2": {
        "GK": (50, 93), "LB": (8, 68), "CB1": (28, 76), "CB2": (50, 78), "CB3": (72, 76), "RB": (92, 68),
        "CM1": (28, 40), "CM2": (50, 44), "CM3": (72, 40),
        "ST1": (36, 10), "ST2": (64, 10),
    },
}


def _slot_keys(slots: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    keys = []
    for s in slots:
        counts[s] = counts.get(s, 0) + 1
        keys.append(s if slots.count(s) == 1 else f"{s}{counts[s]}")
    return keys


def _role_of(key: str) -> str:
    return "".join(ch for ch in key if not ch.isdigit())


def rarity(ovr: float) -> str:
    if ovr >= 100:
        return "r-icon"
    if ovr >= 97:
        return "r-dia"
    if ovr >= 85:
        return "r-gold"
    if ovr >= 75:
        return "r-blue"
    return "r-bronze"


def money_s(n: int) -> str:
    n = int(n or 0)
    if n >= 1_000_000:
        return f"£{n/1_000_000:.1f}m"
    if n >= 1_000:
        return f"£{n/1_000:.0f}k"
    return f"£{n}"


def player_card(p: dict | None, role: str, href: str = "", small: bool = False, slot: str = "", in_xi: bool = False) -> str:
    cls = "slot-card pcard pitch" + (" mini" if small else "") + (" inxi" if in_xi else "")
    if p is None:
        return (
            f"<div class='{cls} empty' data-slot='{slot}' data-pid=''>"
            f"<span class='pc-ovr'>—</span><span class='pc-pos'>{role}</span>"
            f"<span class='pc-name'>empty</span></div>"
        )
    ovr = float(p.get("overall", 70))
    fit = max(0, min(100, float(p.get("condition", 88))))
    bar = "red" if p.get("injury") or fit < 40 else "amber" if fit < 70 else "green"
    inj = " inj" if p.get("injury") else ""
    st = p.get("season_stats") or {}
    try:
        bd = p.get("birthdate") or p.get("born") or ""
        if bd and hasattr(W, "age_from_birth"):
            age = W.age_from_birth(bd)
        else:
            age = p.get("age") or (2026 - int(str(bd)[:4]) if str(bd)[:4].isdigit() else "?")
    except Exception:
        age = p.get("age") or "?"
    nat = (p.get("nation") or "")[:12]
    extra = f" data-pid='{p['id']}' data-slot='{slot or 'bench'}'"
    g = int(st.get("goals", 0))
    a = int(st.get("assists", 0))
    if small:
        return (
            f"<div class='{cls} bench-card {rarity(ovr)}{inj}'{extra}>"
            f"<span class='pc-ovr'>{ovr:.0f}</span>"
            f"<span class='pc-pos'>{role}</span>"
            f"<span class='pc-name'>{p['last_name']}</span>"
            f"<span class='pc-bar {bar}' style='--fit:{fit}%'></span></div>"
        )
    return (
        f"<div class='{cls} {rarity(ovr)}{inj}'{extra}>"
        f"<span class='pc-ovr'>{ovr:.0f}</span>"
        f"<span class='pc-pos'>{role}</span>"
        f"<span class='pc-name'>{p['last_name']}</span>"
        f"<span class='pc-bar {bar}' style='--fit:{fit}%'></span></div>"
    )


def page_plan(cr: dict) -> str:
    W.ensure_xi(cr)
    u = cr["user"]
    form = u.get("formation", "4-3-3")
    style = u.get("style", "balanced")
    slots = FORMATIONS.get(form, FORMATIONS["4-3-3"])
    keys = _slot_keys(slots)
    coords = PITCH_POS.get(form, PITCH_POS["4-3-3"])
    sq = {p["id"]: p for p in W.squad(cr, u["club_id"])}
    used = set(u.get("xi", {}).values())
    mapped = {}
    placed = []
    for key, role in zip(keys, slots):
        x, y = coords.get(key, (50, 50))
        pid = u["xi"].get(key)
        p = sq.get(pid)
        if p:
            mapped[key] = p
        placed.append(
            f"<div class='slot drop-slot' data-slot='{key}' style='left:{x}%;top:{y}%'>"
            f"{player_card(p, role, slot=key)}</div>"
        )
    bench = []
    for p in sorted(W.squad(cr, u["club_id"]), key=lambda x: -x["overall"]):
        if p["id"] in used:
            continue
        role = p["roles"][0]["code"] if p.get("roles") else "CM"
        bench.append(player_card(p, role, small=True, slot="bench"))
    st = xi_strength(mapped, style)
    opts_f = "".join(f"<option {'selected' if f==form else ''} value='{f}'>{f}</option>" for f in FORMATIONS)
    opts_s = "".join(
        f"<option {'selected' if s==style else ''} value='{s}'>{s}</option>"
        for s in ("possession", "tiki_taka", "balanced", "quick_counter", "gegenpress", "harambee", "long_ball", "out_wide", "park_bus", "low_block")
    )
    stance = u.get("stance", "balanced")
    opts_t = "".join(
        f"<option {'selected' if t==stance else ''} value='{t}'>{t}</option>"
        for t in ("attacking", "balanced", "defensive")
    )
    club = W.club(cr, u["club_id"])
    return html_page("Game plan", f"""
    <div class="plan-head">
      <div>
        <h1>Game plan</h1>
        <p class="plan-sub">{club['name']} · {form} · {stance} · {style}</p>
      </div>
      <form class="row tight" method="post" action="/plan">
        <label>Shape <select name="formation">{opts_f}</select></label>
        <label>Stance <select name="stance">{opts_t}</select></label>
        <label>Style <select name="style">{opts_s}</select></label>
        <button>Apply</button>
        <button name="autopick" value="1">Auto-pick</button>
      </form>
    </div>
    <p class="strength">XI strength <b>{st['total']:.1f}</b>
      · GK {st['gk']:.0f} · DEF {st['def']:.0f} · MID {st['mid']:.0f} · ATT {st['att']:.0f}
    </p>
    <div class="plan-board">
      <aside class="bench">
        <h2>Bench</h2>
        <div class="bench-list drop-slot" data-slot="bench">{''.join(bench) or '<p class="hint">XI is full.</p>'}</div>
      </aside>
      <div class="pitch-wrap">
        <div class="pitch-board">
          <div class="plines"></div>
          {''.join(placed)}
        </div>
      </div>
    </div>
    """, cr, body_class="plan-lock")


def page_pick(cr: dict, slot: str) -> str:
    sq = W.squad(cr, cr["user"]["club_id"])
    used = set(cr["user"].get("xi", {}).values())
    role = _role_of(slot)
    rows = []
    for p in sorted(sq, key=lambda x: -x["overall"]):
        if p.get("injury"):
            continue
        mark = " inxi" if p["id"] in used else ""
        rows.append(
            f"<form method='post' action='/pick/{slot}' class='pick-form{mark}'>"
            f"<input type='hidden' name='pid' value='{p['id']}'>"
            f"<button class='ghost'>{player_card(p, p['roles'][0]['code'] if p.get('roles') else role)}</button>"
            f"</form>"
        )
    return html_page("Pick", f"""
    <p class="crumb"><a href="/plan">Game plan</a> / Slot {role}</p>
    <h1>Choose {role}</h1>
    <div class="pick-grid">{''.join(rows)}</div>
    """, cr)


def _scout_pitch(cr: dict, cid: int) -> str:
    form = cr["user"].get("formation") if cid == cr["user"]["club_id"] else W.club(cr, cid).get("formation", "4-3-3")
    xi = W.resolve_xi(cr, cid, form)
    coords = PITCH_POS.get(form, PITCH_POS["4-3-3"])
    dots = []
    for key, (x, y) in coords.items():
        role = _role_of(key)
        p = xi.get(key) or next((v for k, v in xi.items() if _role_of(k) == role), None)
        name = p["last_name"] if p else "—"
        ovr = f"{p['overall']:.0f}" if p else ""
        dots.append(f"<div class='dot' style='left:{x}%;top:{y}%'><b>{ovr}</b><span>{name}</span></div>")
    bench = W.squad(cr, cid)
    used = {p["id"] for p in xi.values()}
    subs = [p for p in sorted(bench, key=lambda x: -x["overall"]) if p["id"] not in used][:7]
    sub_h = "".join(f"<li>{p['last_name']} {p['overall']:.0f}</li>" for p in subs)
    return f"<div class='scout'><h3>{W.club_name(cr, cid)} · {form}</h3><div class='mini-pitch'>{''.join(dots)}</div><ol class='subs'>{sub_h}</ol></div>"


def page_matchday(cr: dict) -> str:
    W.ensure_cups(cr)
    nxt = W.next_user_fixture(cr)
    if not nxt:
        return html_page("Matchday", "<p>Season fixtures complete.</p>", cr)
    if nxt.get("played"):
        return page_report(cr, nxt["id"])
    hid, aid = nxt["home_id"], nxt["away_id"]
    hx = W.resolve_xi(cr, hid)
    ax = W.resolve_xi(cr, aid)
    hs = xi_strength(hx, cr["user"]["style"] if hid == cr["user"]["club_id"] else "balanced")
    aws = xi_strength(ax, cr["user"]["style"] if aid == cr["user"]["club_id"] else "balanced")
    label = nxt.get("cup") or f"Matchday {nxt.get('week','')}"
    hold = W.next_human_fixture(cr)
    mystyle = cr["user"].get("style", "balanced")
    myform = cr["user"].get("formation", "4-3-3")
    opp = W.club(cr, aid if hid == cr["user"]["club_id"] else hid)
    opp_style = opp.get("style", "balanced")
    opp_form = opp.get("formation", "4-3-3")
    from engine.match import STYLE_MATCHUP, shape_mod
    swing = STYLE_MATCHUP.get((mystyle, opp_style), 0) + shape_mod(mystyle, opp_form)
    if swing > 0.08:
        edge = "Advantage — style and shape lean your way."
    elif swing < -0.08:
        edge = "Disadvantage — their shape hits our style."
    else:
        edge = "Even matchup."
    card = (
        f"<div class='mu-row'><span class='chip'>{mystyle} {myform}</span>"
        f"<span class='chip dim'>{edge}</span>"
        f"<span class='chip'>{opp_style} {opp_form}</span></div>"
    )
    lock = ""
    if hold and hold["id"] != nxt["id"] and hold["date"] <= nxt["date"]:
        lock = f"<p class='warn'>Same calendar. {W.club_name(cr, hold['home_id'])} vs {W.club_name(cr, hold['away_id'])} is first.</p>"
    return html_page("Matchday", f"""
    <h1>{label} · {nxt['date']}</h1>
    {lock}
    <div class="fixture big">
      <div><div class="club">{mark(cr, hid, 52)} {W.club_name(cr, hid)}</div><div class="st">{hs['total']:.1f}</div></div>
      <div class="mid">v</div>
      <div><div class="club">{mark(cr, aid, 52)} {W.club_name(cr, aid)}</div><div class="st">{aws['total']:.1f}</div></div>
    </div>
    {card}
    <form method="post" action="/play/{nxt['id']}" class="play-bar">
      <button class="tile-btn" type="submit">Play match</button>
    </form>
    <div class="scout-row">{_scout_pitch(cr, hid)}{_scout_pitch(cr, aid)}</div>
    <p class="hint"><a href="/plan">Change lineup</a> · XI includes fitness and morale.</p>
    """, cr)


def page_report(cr: dict, fid: int) -> str:
    fx = next(f for f in cr["fixtures"] if f["id"] == fid)
    ev = "".join(
        f"<li>{e.get('text') or e.get('name','')}</li>"
        for e in (fx.get("report") or {}).get("events", [])
    )
    return html_page("Report", f"""
    <h1>{W.club_name(cr, fx['home_id'])} {fx.get('home_goals',0)}–{fx.get('away_goals',0)} {W.club_name(cr, fx['away_id'])}</h1>
    <ul class="feed">{ev or '<li>No goals.</li>'}</ul>
    <p><a class="btn" href="/home">Office</a> <a class="btn" href="/table">Table</a></p>
    """, cr)


def page_table(cr: dict) -> str:
    club = W.club(cr, cr["user"]["club_id"])
    rows = []
    for i, r in enumerate(W.table_for(cr, club["league_id"]), 1):
        cls = "me" if r["club_id"] == club["id"] else ""
        rows.append(
            f"<tr class='{cls}'><td>{i}</td><td>{r['name']}</td><td>{r['p']}</td><td>{r['w']}</td>"
            f"<td>{r['d']}</td><td>{r['l']}</td><td>{r['gf']}</td><td>{r['ga']}</td>"
            f"<td>{r['gd']}</td><td>{r['pts']}</td></tr>"
        )
    league = next((l["name"] for l in cr["leagues"] if l["id"] == club["league_id"]), "League")
    sc = "".join(
        f"<tr><td>{i}</td><td>{p['last_name']}</td><td>{W.club_name(cr, p['club_id'])}</td><td>{n}</td></tr>"
        for i, (n, p) in enumerate(W.leaders(cr, club["league_id"], "goals"), 1)
    ) or "<tr><td colspan='4'>No goals yet.</td></tr>"
    ac = "".join(
        f"<tr><td>{i}</td><td>{p['last_name']}</td><td>{W.club_name(cr, p['club_id'])}</td><td>{n}</td></tr>"
        for i, (n, p) in enumerate(W.leaders(cr, club["league_id"], "assists"), 1)
    ) or "<tr><td colspan='4'>No assists yet.</td></tr>"
    return html_page("Table", f"""
    <h1>{league}</h1>
    <div class="panel scroll">
    <table class="grid">
      <thead><tr><th>#</th><th>Club</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead>
      <tbody>{''.join(rows)}</tbody>
    </table>
    <h2>Top scorers</h2>
    <table class="grid slim"><thead><tr><th>#</th><th>Player</th><th>Club</th><th>G</th></tr></thead><tbody>{sc}</tbody></table>
    <h2>Top assists</h2>
    <table class="grid slim"><thead><tr><th>#</th><th>Player</th><th>Club</th><th>A</th></tr></thead><tbody>{ac}</tbody></table>
    </div>
    """, cr)


def page_schedule(cr: dict, raw_q: str = "") -> str:
    from datetime import date
    from urllib.parse import parse_qs
    import calendar as cal
    W.repair_home_away(cr)
    W.ensure_cups(cr)
    cid = cr["user"]["club_id"]
    club = W.club(cr, cid)
    today = W.parse_d(cr["meta"]["current_date"])
    qs = parse_qs(raw_q or "")
    try:
        ys, ms = (qs.get("m") or [""])[0].split("-")
        view = date(int(ys), int(ms), 1)
    except Exception:
        view = date(today.year, today.month, 1)
    mine = [f for f in cr["fixtures"] if f["home_id"] == cid or f["away_id"] == cid]
    mine.sort(key=lambda f: f["date"])
    by_day: dict[int, dict] = {}
    for fx in mine:
        d = W.parse_d(fx["date"])
        if d.year == view.year and d.month == view.month:
            by_day[d.day] = fx
    months = []
    y0 = int(cr["meta"].get("season_start_year", today.year))
    for i, name in enumerate(["Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"]):
        yy = y0 if i < 6 else y0 + 1
        mm = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5][i]
        on = " on" if yy == view.year and mm == view.month else ""
        months.append(f'<a class="mo{on}" href="/schedule?m={yy}-{mm:02d}">{name}</a>')
    cells = []
    for week in cal.monthcalendar(view.year, view.month):
        row = []
        for day in week:
            if day == 0:
                row.append("<td class='empty'></td>")
                continue
            fx = by_day.get(day)
            cls = "day"
            inner = f"<b>{day}</b>"
            if fx:
                ha = "Home" if fx["home_id"] == cid else "Away"
                opp = fx["away_id"] if ha == "Home" else fx["home_id"]
                tag = {"UCL": "UCL", "Europa League": "UEL", "Conference League": "UECL",
                       "CAF Champions League": "CAF"}.get(fx.get("cup"), "CUP" if fx.get("cup") else "LEAGUE")
                if fx.get("ko_round") == "playoff":
                    tag = "PO"
                elif fx.get("ko_round") == "final":
                    tag = tag + " F"
                cls += " match " + ("home" if ha == "Home" else "away")
                if fx.get("played"):
                    gf = fx["home_goals"] if ha == "Home" else fx["away_goals"]
                    ga = fx["away_goals"] if ha == "Home" else fx["home_goals"]
                    inner += (
                        f"<span class='pip'></span><span class='sc'>{gf}-{ga}</span>"
                        f"<span class='tg'>{tag}</span>{W.badge(W.club(cr, opp), 18)}"
                    )
                else:
                    inner += (
                        f"<span class='ha'>{ha}</span><span class='tg'>{tag}</span>"
                        f"{W.badge(W.club(cr, opp), 20)}"
                    )
            if day == today.day and view.month == today.month and view.year == today.year:
                cls += " today"
            row.append(f"<td class='{cls}'>{inner}</td>")
        cells.append("<tr>" + "".join(row) + "</tr>")
    focus = next((f for f in mine if not f.get("played") and f["date"] >= cr["meta"]["current_date"]), None)
    if focus:
        ha = "Home" if focus["home_id"] == cid else "Away"
        opp = focus["away_id"] if ha == "Home" else focus["home_id"]
        oc = W.club(cr, opp)
        tag = focus.get("cup") or next((l["name"] for l in cr["leagues"] if l["id"] == club["league_id"]), "League")
        fd = W.parse_d(focus["date"])
        left = (
            f"<div class='cal-date'>{fd.strftime('%A, %b %d').upper()}</div>"
            f"<div class='cal-comp'>{tag}</div>"
            f"{W.badge(oc, 72)}"
            f"<div class='cal-opp'>{oc['name']}</div>"
            f"<div class='cal-ha'>{ha}</div>"
        )
    else:
        left = f"<div class='cal-date'>{today.strftime('%A, %b %d').upper()}</div><p class='muted'>No match this month.</p>"
    win = W.window_open(cr)
    close = date(today.year if today.month >= 7 else today.year, 9, 1) if today.month >= 6 else date(today.year, 2, 1)
    days_left = max(0, (close - today).days)
    win_s = (
        f"<p class='win-open'>Transfer window opened</p><div class='win-days'>{days_left} Days</div><p>Until window closes</p>"
        if win else
        f"<p class='win-shut'>Transfer window closed</p>"
    )
    euro = "" if cr["meta"].get("europe_on") else "<p class='muted'>Europe starts next season. This year is league + domestic cups only.</p>"
    return html_page("Schedule", f"""
    <div class="fc-cal">
      <nav class="mo-row">{''.join(months)}</nav>
      <div class="fc-body">
        <aside class="cal-rail">
          {left}
          {win_s}
          {euro}
        </aside>
        <div class="cal-grid-wrap">
          <table class="fc-grid">
            <thead><tr><th></th><th></th><th></th><th></th><th></th><th></th><th></th></tr></thead>
            <tbody>{''.join(cells)}</tbody>
          </table>
        </div>
      </div>
    </div>
    """, cr)


def page_market(cr: dict, raw_q: str = "") -> str:
    from urllib.parse import parse_qs
    qs = parse_qs(raw_q)
    q = (qs.get("q") or [""])[0].strip().lower()
    team = (qs.get("team") or [""])[0].strip().lower()
    nation = (qs.get("nation") or [""])[0].strip().lower()
    omin = (qs.get("omin") or [""])[0].strip()
    omax = (qs.get("omax") or [""])[0].strip()
    W.ensure_staff(cr)
    W.resolve_scout(cr)
    win = "open" if W.window_open(cr) else "closed"
    my = cr["user"]["club_id"]
    cap = W.max_buy_ovr(cr, my)
    listed = [p for p in cr["players"] if p["club_id"] != my and not p.get("retired")]
    if q:
        listed = [p for p in listed if q in f"{p['first_name']} {p['last_name']}".lower()]
    if team:
        listed = [p for p in listed if team in W.club_name(cr, p["club_id"]).lower()]
    if nation:
        listed = [p for p in listed if nation in str(p.get("nation", "")).lower()]
    if omin.isdigit():
        listed = [p for p in listed if p["overall"] >= int(omin)]
    if omax.isdigit():
        listed = [p for p in listed if p["overall"] <= int(omax)]
    listed.sort(key=lambda p: -p["overall"])
    sc = cr["user"].get("scout") or {}
    scout_rows = []
    for pid in sc.get("names") or []:
        try:
            p = W.player(cr, pid)
        except StopIteration:
            continue
        ok, why, fee = W.can_buy(cr, my, p)
        btn = f"<form method='post' action='/buy/{p['id']}' class='inline'><button>Bid £{fee:,}</button></form>" if ok else why
        scout_rows.append(f"<li>{p['last_name']} {p['overall']:.0f} · {W.club_name(cr, p['club_id'])} · {btn}</li>")
    rows = []
    for p in listed[:60]:
        ok, why, fee = W.can_buy(cr, my, p)
        btn = (
            f"<form method='post' action='/buy/{p['id']}' class='inline'>"
            f"<select name='years'><option value='2'>2y</option><option value='3' selected>3y</option>"
            f"<option value='4'>4y</option><option value='5'>5y</option></select> "
            f"<input name='fee' placeholder='£ bid' size='8'> "
            f"<button>Bid £{fee:,}</button></form>"
            if ok else f"<span class='muted'>{why}</span>"
        )
        rows.append(
            f"<tr><td>{p['roles'][0]['code']}</td><td>{p['first_name']} {p['last_name']}</td>"
            f"<td>{W.club_name(cr, p['club_id'])}</td><td>{p['overall']:.0f}</td>"
            f"<td>£{p['value']:,}</td><td>{btn}</td></tr>"
        )
    incoming = []
    outgoing = []
    for off in reversed(cr.get("offers", [])[-12:]):
        try:
            pl = W.player(cr, off["pid"])
        except StopIteration:
            continue
        line = f"{pl['last_name']} · {W.club_name(cr, off['buyer_id'])} · £{off['fee']:,} · {off['status']}"
        if off["status"] == "awaiting" and off["seller_id"] == my:
            incoming.append(
                f"<li>{line}<div class='row tight'>"
                f"<form method='post' action='/offer/{off['id']}/accept'><button>Accept</button></form>"
                f"<form method='post' action='/offer/{off['id']}/reject'><button>Reject</button></form>"
                f"<form method='post' action='/offer/{off['id']}/raise'>"
                f"<input name='ask' placeholder='Ask £'>"
                f"<button>Ask more</button></form>"
                f"<form method='post' action='/offer/{off['id']}/accept'><button>Discount / accept</button></form>"
                f"</div></li>"
            )
        elif off["status"] == "counter" and off["buyer_id"] == my:
            want = int(off.get("want") or off["fee"])
            outgoing.append(
                f"<li>{line} — {off.get('reply','')}"
                f"<div class='row tight'>"
                f"<form method='post' action='/offer/{off['id']}/meet'><button>Meet £{want:,}</button></form>"
                f"<form method='post' action='/offer/{off['id']}/counter'>"
                f"<input name='ask' placeholder='Your bid'>"
                f"<button>Send new bid</button></form>"
                f"<form method='post' action='/offer/{off['id']}/reject'><button>Walk away</button></form>"
                f"</div></li>"
            )
        else:
            outgoing.append(f"<li>{line} — {off.get('reply','')}</li>")
    return html_page("Market", f"""
    <h1>Market</h1>
    <p>Window <b>{win}</b> · Ceiling <b>{cap:.0f}</b> · Bank £{W.club(cr, my)['budget']:,}</p>
    <div class="market-grid">
      <section class="panel bids">
        <h2>Incoming</h2>
        <ul class="feed">{''.join(incoming) or '<li>No bids for your players.</li>'}</ul>
        <h2>Your bids</h2>
        <ul class="feed slim">{''.join(outgoing) or '<li>None live.</li>'}</ul>
      </section>
      <section class="panel scroll list">
        <form method="post" action="/scout" class="row tight">
          <select name="who">
            <option value="peter">Peter · E clubs · growth</option>
            <option value="oblak">Oblak · D/C</option>
            <option value="brent">Brent · A/A+</option>
            <option value="s2g">S2G · B to S</option>
          </select>
          <select name="region"><option value="africa">Africa</option><option value="europe">Europe</option></select>
          <button>Send scout</button>
        </form>
        <ul class="feed">{''.join(scout_rows) or "<li>No scout report yet. Send one — they hunt a weak line you can actually sign.</li>"}</ul>
        <form class="row tight" method="get" action="/market">
          <input name="q" value="{q}" placeholder="Player">
          <input name="team" value="{team}" placeholder="Club">
          <input name="nation" value="{nation}" placeholder="Nation">
          <input name="omin" value="{omin}" placeholder="Min OVR" size="4">
          <input name="omax" value="{omax}" placeholder="Max OVR" size="4">
          <button>Search</button>
        </form>
        <table class="grid">
          <thead><tr><th>Pos</th><th>Player</th><th>Club</th><th>OVR</th><th>Value</th><th></th></tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </section>
    </div>
    """, cr)


def page_news(cr: dict) -> str:
    import re
    score = re.compile(r"\d+\s*[–-]\s*\d+")
    items = "".join(
        f"<li><span>{n['date'][5:]}</span> {n['text']}</li>"
        for n in W.wire_news(cr, 40)
        if not score.search(n.get("text", "") or "")
    ) or "<li>No wire stories yet.</li>"
    return html_page("News", f"""
    <h1>News</h1>
    <p class="plan-sub">Wire — moves, rumours, injuries. Club mail stays on Home.</p>
    <div class="panel scroll"><ul class="feed">{items}</ul></div>
    """, cr)


def page_club(cr: dict) -> str:
    cid = cr["user"]["club_id"]
    c = W.club(cr, cid)
    bill = W.wage_bill(cr, cid)
    staff = W.club_staff_wage(cr, cid)
    signed = "".join(
        f"<li>{s['name']} · {s.get('left', s.get('years',1))}y · home £{s['per_home_win']:,} · {s['task']}</li>"
        for s in cr["user"].get("sponsors", [])
    ) or "<li class='muted'>None signed.</li>"
    cards = "".join(
        f"<form method='post' action='/sponsor/{s['id']}' class='spon-card'>"
        f"<button>Sign {s['name']}<small>£{s['per_home_win']:,} home · need {s.get('min_rank','E')} · {s['task']}</small></button></form>"
        for s in CATALOG
        if s["id"] not in {x["id"] for x in cr["user"].get("sponsors", [])}
    )
    return html_page("Club", f"""
    <h1>Club</h1>
    <div class="club-bar">
      <form method="post" action="/save"><input type="hidden" name="slot" value="career1"><button class="tile-btn" type="submit">Save</button></form>
      <form method="post" action="/advance"><button class="tile-btn" type="submit">Advance day</button></form>
      <form method="post" action="/goto-match"><button class="tile-btn" type="submit">Skip to match</button></form>
      <a class="tile-btn" href="/lobby">Lobby</a>
      <form method="post" action="/exit"><button class="tile-btn ghost" type="submit">Exit</button></form>
    </div>
    <div class="panel">
      <p><b>Rank {W.team_rank(cr, cid)}</b> · cap {W.max_buy_ovr(cr, cid):.0f} OVR · Bank £{c['budget']:,}</p>
      <p>wages £{bill:,}/w · staff £{staff:,}/w</p>
      <p>Ceiling {W.max_buy_ovr(cr, cid):.0f} OVR · {c.get('coach','—')} · {cr['user'].get('manager_name','')}</p>
    </div>
    <div class="panel scroll club-sheet">
      <h2>Sponsors (max 3)</h2>
      <ul class="feed">{signed}</ul>
      <div class="spon-grid">{cards}</div>
    </div>
    <p class="hint">{pack()['meta']['disclaimer']}</p>
    """, cr)


def page_trophies(cr: dict) -> str:
    items = "".join(
        f"<li>{t.get('season','')} — {t.get('title')}</li>"
        for t in cr["user"].get("trophies", [])
    ) or "<li>Empty cabinet. Win the league or an award.</li>"
    mood = int(cr["user"].get("fan_mood", 60))
    boards = []
    for lg in cr["leagues"]:
        aw = W.league_awards(cr, lg["id"])
        if not aw:
            continue
        boot = aw.get("golden_boot")
        play = aw.get("playmaker")
        young = aw.get("young")
        boards.append(
            f"<li><b>{lg['name']}</b> — boot {boot['last_name'] if boot else '—'} "
            f"({int((boot or {}).get('season_stats',{}).get('goals',0))}), "
            f"assists {play['last_name'] if play else '—'}, "
            f"young {young['last_name'] if young else '—'}</li>"
        )
    note = W.club(cr, cr["user"]["club_id"]).get("ai_note", "")
    return html_page("Trophies", f"""
    <h1>Trophy room</h1>
    <p>Fans {mood}/100 · rank {W.team_rank(cr, cr['user']['club_id'])} · <a href="/news">Open the wire</a></p>
    <p class="muted">{note}</p>
    <h2>This season — every league</h2>
    <ul class="feed">{''.join(boards)}</ul>
    <div class="panel scroll"><ul class="feed">{items}</ul></div>
    """, cr)


def page_cups(cr: dict) -> str:
    W.ensure_cups(cr)
    lid = W.club(cr, cr["user"]["club_id"])["league_id"]
    blocks = []
    cups = sorted({f.get("cup") for f in cr["fixtures"] if f.get("cup")})
    cid = cr["user"]["club_id"]
    mine = [
        t for t in cups
        if any(
            f.get("cup") == t and (
                f.get("league_id") == lid or f.get("home_id") == cid or f.get("away_id") == cid
            )
            for f in cr["fixtures"]
        )
    ]
    for title in mine:
        rounds: dict[int, list] = {}
        for fx in cr["fixtures"]:
            if fx.get("cup") != title:
                continue
            rounds.setdefault(int(fx.get("round", 1)), []).append(fx)
        cols = []
        for rnd in sorted(rounds):
            cells = []
            for fx in rounds[rnd]:
                score = ""
                if fx.get("played"):
                    score = f" {fx.get('home_goals',0)}–{fx.get('away_goals',0)}"
                cells.append(
                    f"<div class='br-m'>{W.club(cr, fx['home_id'])['short']} v "
                    f"{W.club(cr, fx['away_id'])['short']}{score}</div>"
                )
            cols.append(f"<div class='br-col'><h3>R{rnd}</h3>{''.join(cells)}</div>")
        rows = []
        for rnd in sorted(rounds):
            for fx in rounds[rnd]:
                sc = "—"
                if fx.get("played"):
                    sc = f"{fx.get('home_goals',0)}–{fx.get('away_goals',0)}"
                rows.append(
                    f"<tr><td>R{rnd}</td>"
                    f"<td>{W.badge(W.club(cr, fx['home_id']), 16)} {W.club(cr, fx['home_id'])['short']}</td>"
                    f"<td>{W.badge(W.club(cr, fx['away_id']), 16)} {W.club(cr, fx['away_id'])['short']}</td>"
                    f"<td>{sc}</td><td>{fx['date'][5:]}</td></tr>"
                )
        lines = "".join(
            f"<li>R{r} · {W.club_name(cr, fx['home_id'])} v {W.club_name(cr, fx['away_id'])} "
            f"· {fx['date']}"
            + (f" · {fx.get('home_goals',0)}–{fx.get('away_goals',0)}" if fx.get("played") else "")
            + "</li>"
            for r, fx in ((int(fx.get("round", 1)), fx) for fx in cr["fixtures"] if fx.get("cup") == title)
        ) or "<li>Draw still being printed.</li>"
        euro = {"UCL", "Europa League", "Conference League", "CAF Champions League"}
        if title in euro:
            continue
        draw = "".join(
            f"<li>{W.badge(W.club(cr, fx['home_id']), 16)} {W.club(cr, fx['home_id'])['short']} v "
            f"{W.badge(W.club(cr, fx['away_id']), 16)} {W.club(cr, fx['away_id'])['short']}"
            + (f" · {fx.get('home_goals',0)}–{fx.get('away_goals',0)}" if fx.get("played") else f" · {fx['date'][5:]}")
            + "</li>"
            for fx in sorted(
                (f for f in cr["fixtures"] if f.get("cup") == title),
                key=lambda x: (x.get("date", ""), x.get("round", 0)),
            )[:32]
        )
        table = "".join(rows) or "<tr><td colspan=5>Draw pending.</td></tr>"
        blocks.append(
            f"<h2>{title}</h2>"
            f"<div class='split-eu'>"
            f"<div class='panel scroll'><h3>Draw</h3><ul class='feed tight'>{draw or '<li>No ties yet.</li>'}</ul></div>"
            f"<div class='panel scroll'><h3>Ties</h3>"
            f"<table class='grid slim'><thead><tr><th>Rd</th><th>Home</th><th>Away</th><th>Score</th><th>Date</th></tr></thead>"
            f"<tbody>{table}</tbody></table></div></div>"
        )
    return html_page("Cups", f"""
    <h1>Domestic cups</h1>
    <p class="lede">League and national cups. Europe is on the UCL tab.</p>
    {''.join(blocks) or "<p>No cups drawn yet.</p>"}
    """, cr)


def page_ucl(cr: dict) -> str:
    W.ensure_cups(cr)
    def board(title: str) -> str:
        fx = [f for f in cr["fixtures"] if f.get("cup") == title]
        if not fx:
            return f"<p class='muted'>No {title} draw in this career yet. Open Cups once, or start a new season.</p>"
        pts: dict[int, list] = {}
        for f in fx:
            pts.setdefault(f["home_id"], [0, 0, 0, 0])
            pts.setdefault(f["away_id"], [0, 0, 0, 0])
            if f.get("phase") not in ("league", "group") or not f.get("played"):
                continue
            hg, ag = f.get("home_goals", 0), f.get("away_goals", 0)
            pts[f["home_id"]][3] += 1
            pts[f["away_id"]][3] += 1
            pts[f["home_id"]][1] += hg
            pts[f["home_id"]][2] += ag
            pts[f["away_id"]][1] += ag
            pts[f["away_id"]][2] += hg
            if hg > ag:
                pts[f["home_id"]][0] += 3
            elif ag > hg:
                pts[f["away_id"]][0] += 3
            else:
                pts[f["home_id"]][0] += 1
                pts[f["away_id"]][0] += 1
        order = sorted(pts.items(), key=lambda kv: (-kv[1][0], kv[1][1] - kv[1][2], -kv[1][1]))
        table = "".join(
            f"<tr><td>{i}</td><td>{W.badge(W.club(cr, cid), 18)} {W.club(cr, cid)['short']}</td>"
            f"<td>{s[3]}</td><td>{s[0]}</td><td>{s[1]-s[2]:+d}</td></tr>"
            for i, (cid, s) in enumerate(order, 1)
        )
        qual = "".join(
            f"<li>{W.badge(W.club(cr, f['home_id']), 16)} {W.club(cr, f['home_id'])['short']} "
            f"v {W.badge(W.club(cr, f['away_id']), 16)} {W.club(cr, f['away_id'])['short']}"
            + (f" · {f.get('home_goals',0)}–{f.get('away_goals',0)}" if f.get("played") else f" · {f['date'][5:]}")
            + f"</li>"
            for f in sorted(fx, key=lambda x: (x.get("date", ""), x.get("round", 0)))[:24]
        )
        order_l = []
        for rnd in ("playoff", "r16_po", "r16", "qf", "sf", "final"):
            rows = []
            for f in sorted((x for x in fx if x.get("ko_round") == rnd), key=lambda x: (x.get("tie", ""), x.get("leg", 1))):
                sc = f"{f.get('home_goals',0)}–{f.get('away_goals',0)}" if f.get("played") else f["date"][5:]
                rows.append(
                    f"<li>{W.badge(W.club(cr, f['home_id']), 16)} {W.club(cr, f['home_id'])['short']} "
                    f"v {W.badge(W.club(cr, f['away_id']), 16)} {W.club(cr, f['away_id'])['short']}"
                    f" · L{f.get('leg',1)} · {sc}</li>"
                )
            if rows:
                lab = {"playoff": "Aug playoff", "r16_po": "KO playoff", "r16": "Round of 16",
                       "qf": "Quarter-finals", "sf": "Semi-finals", "final": "Final"}[rnd]
                order_l.append(f"<h4>{lab}</h4><ul class='feed tight'>{''.join(rows)}</ul>")
        bracket = "".join(order_l) or "<p class='muted'>Knockout after the league phase.</p>"
        return (
            f"<h2>{title}</h2>"
            f"<div class='split-eu'>"
            f"<div class='panel scroll'><h3>Draw / KO</h3>{bracket}<h3>Fixtures</h3><ul class='feed tight'>{qual}</ul></div>"
            f"<div class='panel scroll'><h3>League phase</h3>"
            f"<table class='grid slim'><thead><tr><th>#</th><th>Club</th><th>P</th><th>Pts</th><th>GD</th></tr></thead>"
            f"<tbody>{table or '<tr><td colspan=5>Field empty.</td></tr>'}</tbody></table></div>"
            f"</div>"
        )
    note = (
        "<p class='lede'>Season 1 is domestic only. Finish the league — top 5 UCL, 6th Europa, 7th–8th Conference next year. One ticket each.</p>"
        if not cr["meta"].get("europe_on")
        else "<p class='lede'>League phase, then knockout. Out of Europe means out. Cup winners can take a Europa seat next season if they are not already in UCL.</p>"
    )
    return html_page("UCL", f"""
    <h1>Europe & Africa</h1>
    {note}
    {board("UCL")}
    {board("Europa League")}
    {board("Conference League")}
    {board("CAF Champions League")}
    """, cr)


def page_lobby() -> str:
    cr = career()
    if cr is None:
        return page_menu()
    n, need = W.lobby_count(cr)
    taken = {int(k) for k in cr.get("seats", {})}
    host_lid = W.club(cr, cr["user"]["club_id"])["league_id"]
    rows = []
    for key, seat in cr.get("seats", {}).items():
        flag = "READY" if seat.get("ready") else "picking"
        rows.append(
            f"<li>{mark(cr, int(key), 26)} <b>{seat.get('manager_name','?')}</b> — {W.club_name(cr, int(key))} · {flag}</li>"
        )
    opts = "".join(
        f'<option value="{c["id"]}" {"disabled" if c["id"] in taken else ""}>'
        f'{c["name"]}{" — taken" if c["id"] in taken else ""}</option>'
        for c in cr["clubs"] if c["league_id"] == host_lid
    )
    go = ""
    if n >= need:
        go = '<p class="lede">Both ready.</p><form method="post" action="/lobby-start"><button class="tile-btn" type="submit">Start</button></form>'
    code = cr.get("meta", {}).get("room", "—")
    mine = cr["user"].get("manager_name") or "Manager"
    return html_page("Lobby", f"""
    <section class="panel start office">
      {go}
      <h1>Room {code} · {n}/{need}</h1>
      <p class="lede">One seat each. Taking a new club moves you — it does not add another Guest.</p>
      <p><button type="button" class="tile-btn" onclick="navigator.clipboard.writeText('{code}')">Copy {code}</button></p>
      <ul class="feed">{''.join(rows) or "<li>Waiting for the other manager.</li>"}</ul>
      <form method="post" action="/join" class="career-form">
        <input type="hidden" name="name" value="{mine}">
        <label class="span2">Free club <select name="club">{opts}</select></label>
        <div class="span2 stick-act"><button class="tile-btn" type="submit">Sit here (once)</button></div>
      </form>
      <div class="hub-grid">
        <form method="post" action="/ready"><button class="tile-btn" type="submit">I'm ready</button></form>
        <form method="post" action="/leave"><button class="tile-btn ghost" type="submit">Leave</button></form>
      </div>
      <p><a href="/home">Play now</a></p>
    </section>
    """, cr if cr.get("user") else None)


def page_join() -> str:
    cr = career()
    if cr is None:
        return page_menu()
    taken = {int(k) for k in cr.get("seats", {})}
    opts = "\n".join(
        f'<option value="{c["id"]}">{c["name"]}</option>'
        for c in cr["clubs"] if c["id"] not in taken
    ) or '<option value="">No free clubs</option>'
    return html_page("Join", f"""
    <section class="panel start">
      <h1>Sit at the table</h1>
      <p>Same save. Pick a club nobody else has.</p>
      <form method="post" action="/join" class="stack">
        <label>Your name <input name="name" value="Guest" required></label>
        <label>Club <select name="club">{opts}</select></label>
        <button>Join</button>
      </form>
    </section>
    """, None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(" · " + (fmt % args) + "\n")

    def _send(self, code: int, body: str, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _redir(self, loc: str, extra: list | None = None):
        self.send_response(303)
        self.send_header("Location", loc)
        for h in extra or []:
            self.send_header("Set-Cookie", h)
        self.end_headers()

    def _read_form(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(n).decode("utf-8") if n else ""
        q = parse_qs(raw)
        return {k: v[0] if v else "" for k, v in q.items()}

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        if path.startswith("/static/"):
            fp = ROOT / "ui" / path.lstrip("/")
            if fp.is_file():
                if fp.suffix == ".css":
                    self._send(200, fp.read_text(encoding="utf-8"), "text/css")
                elif fp.suffix in (".jpg", ".jpeg", ".png", ".webp", ".wav"):
                    data = fp.read_bytes()
                    mime = "audio/wav" if fp.suffix == ".wav" else ("image/png" if fp.suffix == ".png" else "image/jpeg")
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                else:
                    self._send(200, fp.read_text(encoding="utf-8"), "text/javascript")
                return
            self._send(404, "missing")
            return
        user = who(self)
        ck = cookies_of(self)
        if ck.get("room") and ck["room"] in STATE.get("worlds", {}):
            set_career(STATE["worlds"][ck["room"]])
        if path == "/register":
            self._send(200, page_register())
            return
        if path in ("/", "/boot") and not user:
            self._send(200, page_login())
            return
        if path == "/new":
            self._send(200, page_new())
            return
        cr = career_for(self)
        STATE["career"] = cr
        if path == "/join" and cr is not None:
            self._send(200, page_join())
            return
        if path in ("/", "/boot") or cr is None:
            if path not in ("/", "/boot") and cr is None:
                self._redir("/")
                return
            if path in ("/", "/boot", "/menu"):
                self._send(200, page_menu(user))
                return
            if path == "/new":
                self._send(200, page_new())
                return
        routes = {
            "/home": lambda: page_home(cr),
            "/team": lambda: page_team(cr),
            "/plan": lambda: page_plan(cr),
            "/matchday": lambda: page_matchday(cr),
            "/table": lambda: page_table(cr),
            "/schedule": lambda: page_schedule(cr, u.query),
            "/market": lambda: page_market(cr, u.query),
            "/news": lambda: page_news(cr),
            "/club": lambda: page_club(cr),
            "/trophies": lambda: page_trophies(cr),
            "/cups": lambda: page_cups(cr),
            "/ucl": lambda: page_ucl(cr),
            "/join": lambda: page_lobby(),
            "/lobby": lambda: page_lobby(),
        }
        if path in routes:
            self._send(200, routes[path]())
            return
        if path.startswith("/player/"):
            self._send(200, page_player(cr, int(path.rsplit("/", 1)[-1])))
            return
        if path.startswith("/pick/"):
            self._send(200, page_pick(cr, path.rsplit("/", 1)[-1]))
            return
        if path.startswith("/report/"):
            self._send(200, page_report(cr, int(path.rsplit("/", 1)[-1])))
            return
        self._send(404, html_page("404", "<p>Not found.</p>", cr))

    def do_POST(self):
        u = urlparse(self.path)
        path = u.path
        form = self._read_form()
        if path == "/register":
            err = A.register(form.get("user") or "", form.get("pw") or "")
            if err:
                self._send(200, page_register(err))
                return
            tok = A.login(form.get("user") or "", form.get("pw") or "")
            self._redir("/", [f"tok={tok}; Path=/"])
            return
        if path == "/login":
            tok = A.login(form.get("user") or "", form.get("pw") or "")
            if not tok:
                self._send(200, page_login("Use 3 or more letters."))
                return
            name = (form.get("user") or "").strip().lower()
            fp = ROOT / "saves" / f"user_{name}.json"
            extra = [f"tok={tok}; Path=/"]
            if fp.is_file():
                set_career(W.load_json(fp))
                extra.append("room=; Path=/; Max-Age=0")
                self._redir("/home", extra)
                return
            self._redir("/", extra)
            return
        if path == "/logout":
            A.logout(cookies_of(self).get("tok") or "")
            self._redir("/", ["tok=; Path=/; Max-Age=0", "room=; Path=/; Max-Age=0"])
            return
        if path == "/friend":
            me = who(self)
            if not me:
                self._redir("/")
                return
            A.add_friend(me, form.get("name") or "")
            self._redir("/")
            return
        if path == "/room-create":
            me = who(self)
            if not me:
                self._redir("/")
                return
            crn = career_for(self)
            if crn is None:
                crn = W.new_career(pack(), 1, me, {"first": me, "last": "", "age": 36, "nation": "England"})
                set_career(crn)
            code = A.create_room(me)
            crn.setdefault("meta", {})["room"] = code
            from copy import deepcopy
            room_w = deepcopy(crn)
            room_w.setdefault("meta", {})["room"] = code
            STATE.setdefault("worlds", {})[code] = room_w
            W.save_json(ROOT / "saves" / f"room_{code}.json", room_w)
            self._redir("/lobby", [f"room={code}; Path=/"])
            return
        if path == "/room-join":
            me = who(self)
            if not me:
                self._redir("/")
                return
            code = (form.get("code") or "").strip().upper()
            err = A.join_room(code, me)
            if err:
                self._send(200, page_menu(me) if me else page_login(err))
                return
            fp = ROOT / "saves" / f"room_{code}.json"
            if fp.is_file():
                w = W.load_json(fp)
                STATE.setdefault("worlds", {})[code] = w
                set_career(w)
            self._redir("/lobby", [f"room={code}; Path=/"])
            return
        if path == "/start":
            cid = int(form.get("club", "1"))
            name = f"{form.get('first') or 'Alex'} {form.get('last') or 'Reed'}"
            crn = W.new_career(pack(), cid, name, {
                "first": form.get("first") or "Alex",
                "last": form.get("last") or "Reed",
                "age": form.get("age") or 38,
                "nation": form.get("nation") or "England",
            })
            me = who(self)
            crn["user"]["account"] = me or crn["user"].get("manager_name")
            set_career(crn, me)
            (ROOT / "saves").mkdir(exist_ok=True)
            W.save_json(ROOT / "saves" / "career1.json", crn)
            self.send_response(303)
            self.send_header("Location", "/home")
            self.send_header("Set-Cookie", f"seat={cid}; Path=/")
            me = who(self)
            if me:
                W.save_json(ROOT / "saves" / f"user_{me}.json", crn)
            self.end_headers()
            return
        if path == "/load":
            slot = form.get("slot") or "career1"
            fp = ROOT / "saves" / f"{slot}.json"
            if fp.is_file():
                set_career(W.load_json(fp))
                self._redir("/home")
            else:
                self._redir("/")
            return
        if path == "/exit":
            set_career(None)
            self._redir("/")
            return
        if path == "/join":
            crj = career_for(self)
            if crj is None:
                self._redir("/")
                return
            cid = int(form.get("club") or "0")
            if not cid:
                self._redir("/lobby")
                return
            acc = who(self)
            W.take_seat(crj, cid, acc or form.get("name") or "Guest", account=acc)
            self.send_response(303)
            self.send_header("Location", "/lobby")
            self.send_header("Set-Cookie", f"seat={cid}; Path=/")
            self.end_headers()
            return
        if path == "/ready":
            crx = career_for(self)
            if crx:
                ck = self.headers.get("Cookie", "")
                for part in ck.split(";"):
                    if part.strip().startswith("seat=") and part.strip().split("=")[-1] in crx.get("seats", {}):
                        crx["user"] = crx["seats"][part.strip().split("=")[-1]]
                W.set_ready(crx, True)
            self._redir("/lobby")
            return
        if path == "/unready":
            crx = career_for(self)
            if crx:
                ck = self.headers.get("Cookie", "")
                for part in ck.split(";"):
                    if part.strip().startswith("seat=") and part.strip().split("=")[-1] in crx.get("seats", {}):
                        crx["user"] = crx["seats"][part.strip().split("=")[-1]]
                W.set_ready(crx, False)
            self._redir("/lobby")
            return
        if path == "/leave":
            crx = career_for(self)
            if crx and crx.get("user"):
                W.leave_seat(crx, crx["user"]["club_id"])
            self._redir("/lobby")
            return
        if path == "/lobby-start":
            self._redir("/home")
            return
        if path.startswith("/sponsor/"):
            cr = career_for(self)
            if cr:
                W.sign_sponsor(cr, path.rsplit("/", 1)[-1])
                self._redir("/club")
            else:
                self._redir("/")
            return
        cr = career_for(self)
        if cr is None:
            self._redir("/")
            return
        if path == "/plan":
            new_form = form.get("formation") or "4-3-3"
            cr["user"]["style"] = form.get("style") or "balanced"
            cr["user"]["stance"] = form.get("stance") or "balanced"
            if form.get("autopick"):
                cr["user"]["formation"] = new_form
                picked = auto_xi(W.squad(cr, cr["user"]["club_id"]), new_form)
                cr["user"]["xi"] = {k: p["id"] for k, p in picked.items()}
                W.ensure_xi(cr)
            elif new_form != cr["user"].get("formation"):
                W.remap_xi(cr, new_form)
            else:
                W.ensure_xi(cr)
            self._redir("/plan")
            return
        if path == "/drop":
            pid = int(form.get("pid") or "0")
            to_slot = form.get("to") or "bench"
            if pid:
                W.place_player(cr, pid, to_slot)
            self._redir("/plan")
            return
        if path.startswith("/pick/"):
            slot = path.rsplit("/", 1)[-1]
            pid = int(form.get("pid"))
            # swap if already in XI
            for k, v in list(cr["user"]["xi"].items()):
                if v == pid:
                    cr["user"]["xi"][k] = cr["user"]["xi"].get(slot, v)
            cr["user"]["xi"][slot] = pid
            W.ensure_xi(cr)
            self._redir("/plan")
            return
        if path.startswith("/play/"):
            fid = int(path.rsplit("/", 1)[-1])
            fx = next(f for f in cr["fixtures"] if f["id"] == fid)
            cr["meta"]["current_date"] = fx["date"]
            W.heal(cr)
            W.sim_due_ai(cr)
            W.play_fixture(cr, fid)
            self._redir(f"/report/{fid}")
            return
        if path == "/advance":
            W.advance_day(cr)
            self._redir("/club")
            return
        if path == "/goto-match":
            W.advance_to_next_match(cr)
            self._redir("/home")
            return
        if path == "/next-season":
            W.start_next_season(cr)
            self._redir("/home")
            return
        if path == "/scout":
            W.hire_scout(cr, form.get("region") or "africa", form.get("who") or "peter")
            self._redir("/market")
            return
        if path.startswith("/buy/"):
            yrs = int(form.get("years") or 3)
            raw = "".join(ch for ch in (form.get("fee") or "") if ch.isdigit())
            W.try_buy(cr, int(path.rsplit("/", 1)[-1]), yrs, int(raw) if raw else None)
            self._redir("/market")
            return
        if path.startswith("/sell/"):
            W.try_sell(cr, int(path.rsplit("/", 1)[-1]))
            self._redir("/team")
            return
        if path.startswith("/offer/"):
            parts = path.strip("/").split("/")
            if len(parts) >= 3:
                off = next((o for o in cr.get("offers", []) if o["id"] == int(parts[1])), None)
                if off and form.get("ask"):
                    raw = "".join(ch for ch in form.get("ask") if ch.isdigit())
                    if raw:
                        off["ask"] = int(raw)
                W.user_offer_action(cr, int(parts[1]), parts[2])
            self._redir("/market")
            return
        if path == "/save":
            slot = form.get("slot") or "career1"
            W.save_json(ROOT / "saves" / f"{slot}.json", cr)
            cr["news"].insert(0, {"date": cr["meta"]["current_date"], "text": f"Saved {slot}."})
            self._redir("/club")
            return
        self._redir("/home")


def main():
    if not (ROOT / "data" / "world.json").exists():
        print("Building world…")
        sys.path.insert(0, str(ROOT))
        from data.build_world import main as build
        build()
    host, port = "0.0.0.0", A.port()
    ip = lan_ip()
    print(f"This device:  http://127.0.0.1:{port}")
    print(f"Wi-Fi / TV:   http://{ip}:{port}")
    print("Sign in → Create room → give friends the 6-letter code")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
