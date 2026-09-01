"""Kit-colour club marks. Not official crests. Keyed by club id so shorts can clash."""

from __future__ import annotations

# id → (primary, secondary, accent, shape, pattern)
# shape: circle shield hex squircle diamond pennant oval
# pattern: solid ring hoop vsplit hsplit vstripe hstripe zebra sash diag chevron triband canton saltire check

BY_ID: dict[int, tuple[str, str, str, str, str]] = {
    # Premier League 2026-27
    1: ("#EF0107", "#FFFFFF", "#9C824A", "shield", "vsplit"),       # Arsenal
    2: ("#670E36", "#95BFE5", "#FFFFFF", "shield", "sash"),         # Villa
    3: ("#DA291C", "#000000", "#FFFFFF", "circle", "zebra"),        # Bournemouth
    4: ("#E30613", "#FBB800", "#FFFFFF", "squircle", "vsplit"),     # Brentford
    5: ("#0057B8", "#FFFFFF", "#FFCD00", "circle", "vstripe"),      # Brighton
    6: ("#034694", "#FFFFFF", "#D1D3D4", "circle", "ring"),         # Chelsea
    7: ("#77B3D9", "#1D3A6C", "#FFFFFF", "hex", "hsplit"),          # Coventry
    8: ("#1B458F", "#C4122E", "#FFFFFF", "shield", "vsplit"),       # Palace
    9: ("#003399", "#FFFFFF", "#FFD100", "shield", "ring"),         # Everton
    10: ("#000000", "#FFFFFF", "#CC0000", "squircle", "zebra"),     # Fulham
    11: ("#F5A12A", "#000000", "#FFFFFF", "diamond", "hsplit"),     # Hull
    12: ("#0033A0", "#DE2C37", "#FFFFFF", "circle", "hsplit"),      # Ipswich
    13: ("#FFCD00", "#1D1D1B", "#FFFFFF", "squircle", "saltire"),   # Leeds
    14: ("#C8102E", "#00B2A9", "#F6EB61", "shield", "solid"),       # Liverpool
    15: ("#6CABDD", "#1C2C5B", "#FFFFFF", "circle", "ring"),        # City
    16: ("#DA291C", "#FBE122", "#000000", "shield", "ring"),        # United
    17: ("#241F20", "#FFFFFF", "#00A3E0", "shield", "zebra"),       # Newcastle
    18: ("#DD0000", "#FFFFFF", "#000000", "circle", "solid"),       # Forest
    19: ("#EB172B", "#FFFFFF", "#000000", "diamond", "hsplit"),     # Sunderland
    20: ("#132257", "#FFFFFF", "#FFFFFF", "pennant", "hoop"),       # Spurs
    # La Liga
    21: ("#FFFFFF", "#FEBE10", "#00529F", "shield", "ring"),        # Real Madrid
    22: ("#A50044", "#004D98", "#FFED02", "squircle", "vstripe"),   # Barça
    23: ("#CB3524", "#FFFFFF", "#271E1F", "shield", "hstripe"),     # Atlético
    24: ("#EE2523", "#FFFFFF", "#000000", "shield", "zebra"),       # Athletic
    25: ("#0067C7", "#FFFFFF", "#C4A35A", "oval", "ring"),          # Sociedad
    26: ("#FFE667", "#0057B7", "#FFFFFF", "hex", "solid"),          # Villarreal
    27: ("#0BB363", "#FFFFFF", "#000000", "circle", "vstripe"),     # Betis
    28: ("#FFFFFF", "#D21034", "#F3A000", "circle", "hsplit"),      # Sevilla
    29: ("#FFFFFF", "#EE3524", "#000000", "shield", "hsplit"),      # Valencia
    30: ("#8AC3E3", "#FFFFFF", "#D01C22", "circle", "hoop"),        # Celta
    31: ("#D91A2A", "#0A2240", "#FFFFFF", "diamond", "vsplit"),     # Osasuna
    32: ("#FFFFFF", "#E30613", "#000000", "circle", "diag"),        # Rayo
    33: ("#004FA3", "#FFFFFF", "#C4A35A", "circle", "solid"),       # Getafe
    34: ("#0072CE", "#FFFFFF", "#E30613", "shield", "hstripe"),     # Espanyol
    35: ("#0067B1", "#FFFFFF", "#E30613", "squircle", "vstripe"),   # Alaves
    36: ("#B81D23", "#0057B8", "#FFFFFF", "pennant", "sash"),       # Levante
    37: ("#007A33", "#FFFFFF", "#000000", "hex", "ring"),           # Elche
    38: ("#003087", "#FFFFFF", "#E30613", "shield", "sash"),        # Deportivo
    39: ("#007A33", "#000000", "#FFFFFF", "diamond", "solid"),      # Racing
    40: ("#003087", "#E30613", "#FFFFFF", "squircle", "hsplit"),    # Malaga
    41: ("#010E80", "#000000", "#FFFFFF", "circle", "zebra"),       # Inter
    42: ("#12A0D7", "#FFFFFF", "#003087", "oval", "ring"),          # Napoli
    43: ("#FB090B", "#000000", "#FFFFFF", "circle", "zebra"),       # Milan
    44: ("#000000", "#FFFFFF", "#C4A35A", "squircle", "zebra"),     # Juventus
    45: ("#8E1F2F", "#F0A00C", "#FFFFFF", "shield", "solid"),
    46: ("#87D8F7", "#FFFFFF", "#8B1E3F", "shield", "ring"),
    47: ("#1E71B8", "#000000", "#FFFFFF", "circle", "vstripe"),
    48: ("#482E92", "#FFFFFF", "#C4A35A", "diamond", "solid"),
    49: ("#1A2F6B", "#CC0000", "#FFFFFF", "shield", "vsplit"),
    50: ("#8B1A1A", "#FFFFFF", "#C4A35A", "circle", "ring"),
    51: ("#000000", "#FFFFFF", "#C4A35A", "squircle", "hsplit"),
    52: ("#C8102E", "#003087", "#FFFFFF", "circle", "hsplit"),
    53: ("#00A651", "#000000", "#FFFFFF", "hex", "solid"),
    54: ("#AD172B", "#003087", "#FFFFFF", "shield", "vsplit"),
    55: ("#FFD100", "#002B5C", "#FFFFFF", "diamond", "hsplit"),
    56: ("#003087", "#FFFFFF", "#C4A35A", "circle", "ring"),
    57: ("#FFD100", "#003087", "#FFFFFF", "squircle", "hsplit"),
    58: ("#8B1A1A", "#FFD100", "#FFFFFF", "shield", "solid"),
    59: ("#000000", "#FF6A00", "#00843D", "hex", "triband"),
    60: ("#1B3A6B", "#FFFFFF", "#C4A35A", "oval", "hoop"),
    # Bundesliga 61-78
    61: ("#DC052D", "#FFFFFF", "#0066B2", "circle", "ring"),
    62: ("#FDE100", "#000000", "#FFFFFF", "hex", "solid"),
    63: ("#E32221", "#000000", "#FFFFFF", "squircle", "vstripe"),
    64: ("#DD0741", "#FFFFFF", "#0A2240", "circle", "ring"),
    65: ("#FFFFFF", "#E30613", "#000000", "shield", "hstripe"),
    66: ("#003087", "#FFFFFF", "#C4A35A", "circle", "ring"),
    67: ("#E1000F", "#000000", "#FFFFFF", "shield", "vsplit"),
    68: ("#65B32E", "#FFFFFF", "#000000", "hex", "solid"),
    69: ("#000000", "#FFFFFF", "#00A651", "circle", "zebra"),
    70: ("#1C63B7", "#FFFFFF", "#C4A35A", "squircle", "ring"),
    71: ("#E30613", "#FFFFFF", "#000000", "shield", "solid"),
    72: ("#BA3733", "#0077C8", "#FFFFFF", "circle", "vsplit"),
    73: ("#C3102E", "#FFFFFF", "#000000", "diamond", "solid"),
    74: ("#000000", "#FFFFFF", "#C4A35A", "squircle", "zebra"),
    75: ("#009639", "#FFFFFF", "#000000", "circle", "ring"),
    76: ("#ED1C24", "#FFFFFF", "#000000", "shield", "vstripe"),
    77: ("#004B87", "#FFFFFF", "#C4A35A", "hex", "hsplit"),
    78: ("#005CA9", "#E30613", "#FFFFFF", "circle", "hsplit"),
    # Ligue 1 79-96
    79: ("#004170", "#DA291C", "#FFFFFF", "shield", "vsplit"),
    80: ("#FFFFFF", "#003DA5", "#C8102E", "circle", "ring"),
    81: ("#2FAEE0", "#FFFFFF", "#000000", "circle", "hoop"),
    82: ("#E30613", "#FFFFFF", "#C4A35A", "diamond", "hsplit"),
    83: ("#E2012C", "#001E62", "#FFFFFF", "shield", "vsplit"),
    84: ("#E30613", "#000000", "#FFFFFF", "circle", "vstripe"),
    85: ("#000000", "#E30613", "#FFFFFF", "squircle", "zebra"),
    86: ("#FFD100", "#E30613", "#000000", "hex", "hsplit"),
    87: ("#009FE3", "#FFFFFF", "#E30613", "circle", "ring"),
    88: ("#FFED00", "#006837", "#FFFFFF", "shield", "hsplit"),
    89: ("#E30613", "#FFFFFF", "#000000", "circle", "solid"),
    90: ("#5A2D81", "#FFFFFF", "#C4A35A", "diamond", "ring"),
    91: ("#E30613", "#FBB800", "#FFFFFF", "pennant", "sash"),
    92: ("#E30613", "#FFFFFF", "#C4A35A", "shield", "hsplit"),
}

# Serie A first clubs — fix Napoli/Inter/Milan by name later in kit_for


PAL = [
    ("#E30613", "#FFFFFF", "#000000"),
    ("#003087", "#FFFFFF", "#C4A35A"),
    ("#007A33", "#FFFFFF", "#000000"),
    ("#FFD100", "#000000", "#FFFFFF"),
    ("#5A2D81", "#FFFFFF", "#000000"),
    ("#000000", "#FFFFFF", "#E30613"),
    ("#FF6A00", "#000000", "#FFFFFF"),
    ("#0B6E3D", "#FFD100", "#FFFFFF"),
    ("#6CABDD", "#1C2C5B", "#FFFFFF"),
    ("#8B1A1A", "#FFD100", "#FFFFFF"),
    ("#034694", "#FFFFFF", "#D1D3D4"),
    ("#A50044", "#004D98", "#FFED02"),
]
SHAPES = ("circle", "shield", "hex", "squircle", "diamond", "pennant", "oval")
PATS = (
    "solid", "ring", "hoop", "vsplit", "hsplit", "vstripe", "hstripe",
    "zebra", "sash", "diag", "chevron", "triband", "canton", "saltire", "check",
)

# Famous names win over id if the datapack order shifts
BY_NAME = {
    "newcastle united": ("#241F20", "#FFFFFF", "#00A3E0", "shield", "zebra"),
    "juventus": ("#000000", "#FFFFFF", "#C4A35A", "squircle", "zebra"),
    "inter": ("#010E80", "#000000", "#FFFFFF", "circle", "zebra"),
    "internazionale": ("#010E80", "#000000", "#FFFFFF", "circle", "zebra"),
    "ac milan": ("#FB090B", "#000000", "#FFFFFF", "circle", "zebra"),
    "milan": ("#FB090B", "#000000", "#FFFFFF", "circle", "zebra"),
    "napoli": ("#12A0D7", "#FFFFFF", "#003087", "oval", "ring"),
    "barcelona": ("#A50044", "#004D98", "#FFED02", "squircle", "vstripe"),
    "real madrid": ("#FFFFFF", "#FEBE10", "#00529F", "shield", "ring"),
    "chelsea": ("#034694", "#FFFFFF", "#D1D3D4", "circle", "ring"),
    "arsenal": ("#EF0107", "#FFFFFF", "#9C824A", "shield", "vsplit"),
    "liverpool": ("#C8102E", "#00B2A9", "#F6EB61", "shield", "solid"),
    "manchester city": ("#6CABDD", "#1C2C5B", "#FFFFFF", "circle", "ring"),
    "manchester united": ("#DA291C", "#FBE122", "#000000", "shield", "ring"),
    "tottenham hotspur": ("#132257", "#FFFFFF", "#FFFFFF", "pennant", "hoop"),
    "bayern munich": ("#DC052D", "#FFFFFF", "#0066B2", "circle", "ring"),
    "borussia dortmund": ("#FDE100", "#000000", "#FFFFFF", "hex", "solid"),
    "paris saint-germain": ("#004170", "#DA291C", "#FFFFFF", "shield", "vsplit"),
    "psg": ("#004170", "#DA291C", "#FFFFFF", "shield", "vsplit"),
    "ajax": ("#D2122E", "#FFFFFF", "#000000", "circle", "solid"),
    "psv": ("#E30613", "#FFFFFF", "#000000", "circle", "vstripe"),
    "feyenoord": ("#E30613", "#FFFFFF", "#000000", "shield", "hsplit"),
    "benfica": ("#E30613", "#FFFFFF", "#000000", "shield", "hoop"),
    "porto": ("#003087", "#FFFFFF", "#C4A35A", "circle", "ring"),
    "sporting cp": ("#007A33", "#FFFFFF", "#000000", "shield", "hoop"),
    "club brugge": ("#003087", "#000000", "#FFFFFF", "shield", "zebra"),
    "al ahly": ("#E30613", "#FFFFFF", "#C4A35A", "shield", "solid"),
    "zamalek": ("#FFFFFF", "#E30613", "#000000", "circle", "hsplit"),
    "esperance de tunis": ("#E30613", "#FFD100", "#000000", "shield", "vsplit"),
    "espérance de tunis": ("#E30613", "#FFD100", "#000000", "shield", "vsplit"),
    "mamelodi sundowns": ("#FFD100", "#007A33", "#000000", "diamond", "solid"),
    "kaizer chiefs": ("#FFD100", "#000000", "#FFFFFF", "hex", "hsplit"),
    "orlando pirates": ("#000000", "#FFFFFF", "#C4A35A", "shield", "zebra"),
    "wydad": ("#E30613", "#FFFFFF", "#000000", "shield", "solid"),
    "raja casablanca": ("#007A33", "#FFFFFF", "#E30613", "circle", "hoop"),
}


def kit_for(club: dict) -> tuple[str, str, str, str, str]:
    name = (club.get("name") or "").strip().lower()
    if name in BY_NAME:
        return BY_NAME[name]
    for key, kit in BY_NAME.items():
        if key in name or name in key:
            return kit
    cid = int(club.get("id") or 0)
    if cid in BY_ID:
        return BY_ID[cid]
    h = cid * 17 + sum(ord(c) for c in name)
    p, s, a = PAL[h % len(PAL)]
    # lock unique cut so two red clubs never share shape+pattern
    return p, s, a, SHAPES[h % len(SHAPES)], PATS[(h // 3 + cid) % len(PATS)]


def _clip(shape: str, cid: str) -> str:
    if shape == "shield":
        return f'<path id="{cid}" d="M4 5 L20 1.5 L36 5 L36 22 Q20 39 4 22 Z"/>'
    if shape == "hex":
        return f'<path id="{cid}" d="M20 2 L36 11 L36 29 L20 38 L4 29 L4 11 Z"/>'
    if shape == "diamond":
        return f'<path id="{cid}" d="M20 2 L38 20 L20 38 L2 20 Z"/>'
    if shape == "squircle":
        return f'<rect id="{cid}" x="3" y="3" width="34" height="34" rx="9"/>'
    if shape == "pennant":
        return f'<path id="{cid}" d="M6 4 L34 20 L6 36 Z"/>'
    if shape == "oval":
        return f'<ellipse id="{cid}" cx="20" cy="20" rx="16" ry="18"/>'
    return f'<circle id="{cid}" cx="20" cy="20" r="17"/>'


def _light(hexcol: str) -> bool:
    h = hexcol.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r * 299 + g * 587 + b * 114) / 1000 > 168


def _fill(pat: str, p: str, s: str, a: str) -> str:
    if pat == "ring":
        return f'<rect width="40" height="40" fill="{p}"/><circle cx="20" cy="20" r="11" fill="{s}"/>'
    if pat == "hoop":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<circle cx="20" cy="20" r="13" fill="none" stroke="{s}" stroke-width="4"/>'
        )
    if pat == "vsplit":
        return f'<rect width="20" height="40" fill="{p}"/><rect x="20" width="20" height="40" fill="{s}"/>'
    if pat == "hsplit":
        return f'<rect width="40" height="20" fill="{p}"/><rect y="20" width="40" height="20" fill="{s}"/>'
    if pat == "vstripe":
        return "".join(
            f'<rect x="{x}" width="6" height="40" fill="{s if i % 2 else p}"/>'
            for i, x in enumerate(range(0, 42, 6))
        )
    if pat == "hstripe":
        return "".join(
            f'<rect y="{y}" width="40" height="6" fill="{s if i % 2 else p}"/>'
            for i, y in enumerate(range(0, 42, 6))
        )
    if pat == "zebra":
        return "".join(
            f'<rect x="{x}" width="4" height="40" fill="{s if i % 2 else p}"/>'
            for i, x in enumerate(range(0, 44, 4))
        )
    if pat == "sash":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<polygon points="0,28 0,40 40,12 40,0" fill="{s}"/>'
        )
    if pat == "diag":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<polygon points="0,40 40,0 40,14 14,40" fill="{s}"/>'
        )
    if pat == "chevron":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<polygon points="20,5 38,34 2,34" fill="{s}"/>'
        )
    if pat == "triband":
        return (
            f'<rect width="13" height="40" fill="{p}"/>'
            f'<rect x="13" width="14" height="40" fill="{s}"/>'
            f'<rect x="27" width="13" height="40" fill="{a}"/>'
        )
    if pat == "canton":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<rect width="16" height="16" fill="{s}"/>'
        )
    if pat == "saltire":
        return (
            f'<rect width="40" height="40" fill="{p}"/>'
            f'<line x1="4" y1="4" x2="36" y2="36" stroke="{s}" stroke-width="6"/>'
            f'<line x1="36" y1="4" x2="4" y2="36" stroke="{s}" stroke-width="6"/>'
        )
    if pat == "check":
        cells = []
        for r in range(4):
            for c in range(4):
                col = p if (r + c) % 2 == 0 else s
                cells.append(f'<rect x="{c*10}" y="{r*10}" width="10" height="10" fill="{col}"/>')
        return "".join(cells)
    return f'<rect width="40" height="40" fill="{p}"/>'


def svg(club: dict, size: int = 28) -> str:
    p, s, a, shape, pat = kit_for(club)
    letters = (club.get("short") or "FC")[:3]
    if _light(p) and pat in ("solid", "ring", "hoop"):
        ink = "#111"
    elif _light(s) and pat in ("vsplit", "hsplit", "zebra", "vstripe"):
        ink = "#111"
        # stroke so letters sit on mixed stripes
    else:
        ink = "#fff"
    uid = f"g{int(club.get('id', 0))}z{int(size)}"
    clip = _clip(shape, uid + "p")
    body = _fill(pat, p, s, a)
    edge = a if a and a not in (p, s) else "rgba(0,0,0,.5)"
    return (
        f'<svg class="badge" width="{size}" height="{size}" viewBox="0 0 40 40" aria-hidden="true">'
        f"<defs><clipPath id=\"{uid}\">{clip}</clipPath></defs>"
        f"<g clip-path=\"url(#{uid})\">{body}</g>"
        f'<use href="#{uid}p" fill="none" stroke="{edge}" stroke-width="1.6"/>'
        f'<text x="20" y="25" text-anchor="middle" font-size="8.5" font-weight="800" '
        f'font-family="system-ui,sans-serif" fill="{ink}" stroke="rgba(0,0,0,.35)" stroke-width="0.6">'
        f"{letters}</text></svg>"
    )
