"""Original wire copy. No other company's name or logo."""

from __future__ import annotations

import random

OUTLETS = (
    "The Whistle",
    "Pitchline",
    "Saturday Desk",
    "North Stand",
    "Capitol Sport",
    "Late Kick",
    "Touchline AM",
    "Second Ball",
)

RUMOUR = [
    "{out}: {buyer} have held quiet talks for {player}.",
    "{out}: A bid for {player} is said to be on the table at {buyer}.",
    "{out} understands {buyer} want {player} before the window shuts.",
    "{out}: {player} is 'open to the move' if {buyer} meet the fee.",
    "{out} hears {seller} will not sell {player} cheaply.",
    "{out}: Two clubs, including {buyer}, are tracking {player}.",
    "{out} exclusive — {buyer} scouts were at {seller}'s last home game.",
    "{out}: {player}'s camp has taken a call from {buyer}.",
]

SIGNED = [
    "{out} BREAKING — {player} signs for {buyer} from {seller} ({years} yrs, £{fee}).",
    "{out}: It's done. {player} is a {buyer} player.",
    "{out} confirms {player}'s medical at {buyer} is complete.",
    "{out}: {seller} cash in as {player} leaves for {buyer}.",
]

REJECT = [
    "{out}: {seller} turned down {buyer} for {player}.",
    "{out} — no deal. {seller} told {buyer} the squad is too thin to sell {player}.",
    "{out}: {buyer}'s bid for {player} was 'nowhere near'.",
    "{out} hears {seller} want a bigger number for {player}.",
]

INJURY = [
    "{out}: {player} faces {days} days out with a {kind}.",
    "{out} — blow for {club}: {player} picked up a {kind}{by}.",
    "{out}: {club} wait on scans after {player}'s {kind}.",
]

FANS = [
    "{out}: {club} supporters are restless after a flat run.",
    "{out} — noise around the {club} board; results have not matched the plan.",
    "{out}: {club} fans stayed behind to applaud a young side.",
    "{out}: Patience wears thin at {club} after another home blank.",
]

BOARD = [
    "{out}: {club} have sacked their coach, {coach}.",
    "{out} — {club} stand by {coach} for now.",
    "{out}: {club} close to a new deal for {coach}.",
]

RETIRE = [
    "{out}: {player} has called time on a long career.",
    "{out} — dressing-room farewell as {player} retires at {club}.",
]

TRAIN = [
    "{out}: {club} closed training after a knock in a drill.",
    "{out} — {club} work on set pieces ahead of the next match.",
    "{out}: {player} looked sharp in {club} shooting practice.",
]

PRIZE = [
    "{out}: {club} bank a league prize after finishing {place}.",
    "{out} — prize money lands at {club} ({place}).",
]

WINDOW = [
    "{out}: The window is a waiting game; few medicals this week.",
    "{out} — mid-table sides hunt a striker before deadline.",
    "{out}: Full-backs are the premium this window.",
    "{out} hears several deals will slip to the final 48 hours.",
]

LEAGUE = [
    "{out}: Title race talk around {club} after a strong month.",
    "{out} — {club} look over their shoulder at the bottom three.",
    "{out}: {league} clocks off for an international pause.",
]


def byline(rng: random.Random | None = None) -> str:
    rng = rng or random
    return rng.choice(OUTLETS)


def fill(topic: str, **kw) -> str:
    bank = {
        "rumour": RUMOUR,
        "signed": SIGNED,
        "reject": REJECT,
        "injury": INJURY,
        "fans": FANS,
        "board": BOARD,
        "retire": RETIRE,
        "train": TRAIN,
        "prize": PRIZE,
        "window": WINDOW,
        "league": LEAGUE,
    }.get(topic, WINDOW)
    kw.setdefault("hurt", kw.get("kind", "knock"))
    text = random.choice(bank).format(out=byline(), **kw)
    return text
