"""Local + hosted accounts, rooms, friends. Stdlib only."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACC = ROOT / "saves" / "accounts.json"


def _empty() -> dict:
    return {"users": {}, "tokens": {}, "rooms": {}, "friends": {}}


def load() -> dict:
    if ACC.is_file():
        try:
            return json.loads(ACC.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return _empty()


def save(db: dict) -> None:
    ACC.parent.mkdir(parents=True, exist_ok=True)
    tmp = ACC.with_suffix(".tmp")
    tmp.write_text(json.dumps(db, indent=2), encoding="utf-8")
    tmp.replace(ACC)


def _hash(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 80_000).hex()


def register(name: str, password: str = "") -> str | None:
    name = name.strip().lower()
    if len(name) < 3:
        return "Name 3+ letters."
    db = load()
    if name in db["users"]:
        return None
    db["users"][name] = {"name": name}
    db["friends"].setdefault(name, [])
    save(db)
    return None


def login(name: str, password: str = "") -> str | None:
    name = name.strip().lower()
    if len(name) < 3:
        return None
    db = load()
    db["users"].setdefault(name, {"name": name})
    db["friends"].setdefault(name, [])
    tok = secrets.token_hex(16)
    db["tokens"][tok] = name
    save(db)
    return tok


def user_of(token: str | None) -> str | None:
    if not token:
        return None
    return load()["tokens"].get(token)


def logout(token: str) -> None:
    db = load()
    db["tokens"].pop(token, None)
    save(db)


def add_friend(me: str, other: str) -> str:
    other = other.strip().lower()
    db = load()
    if other not in db["users"]:
        return "No player with that name."
    if other == me:
        return "That is you."
    db["friends"].setdefault(me, [])
    if other not in db["friends"][me]:
        db["friends"][me].append(other)
    db["friends"].setdefault(other, [])
    if me not in db["friends"][other]:
        db["friends"][other].append(me)
    save(db)
    return f"Added {other}."


def friends_of(me: str) -> list:
    return load()["friends"].get(me, [])


def new_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))


def create_room(host: str, needed: int = 2) -> str:
    db = load()
    code = new_code()
    db["rooms"][code] = {
        "host": host,
        "needed": max(2, min(4, needed)),
        "members": [host],
        "ready": {},
    }
    save(db)
    return code


def join_room(code: str, name: str) -> str | None:
    code = code.strip().upper()
    db = load()
    room = db["rooms"].get(code)
    if not room:
        return "No room with that code."
    if name not in room["members"]:
        if len(room["members"]) >= int(room.get("needed", 2)):
            return "Room is full."
        room["members"].append(name)
    save(db)
    return None


def room(code: str | None) -> dict | None:
    if not code:
        return None
    return load()["rooms"].get(code.strip().upper())


def leave_room(code: str, name: str) -> None:
    db = load()
    room = db["rooms"].get(code)
    if not room:
        return
    room["members"] = [m for m in room["members"] if m != name]
    room.get("ready", {}).pop(name, None)
    if not room["members"]:
        db["rooms"].pop(code, None)
    save(db)


def set_room_ready(code: str, name: str, on: bool) -> tuple[int, int]:
    db = load()
    room = db["rooms"].get(code)
    if not room:
        return 0, 2
    room.setdefault("ready", {})[name] = bool(on)
    save(db)
    n = sum(1 for v in room["ready"].values() if v)
    return n, int(room.get("needed", 2))


def port() -> int:
    return int(os.environ.get("PORT", "8765"))
