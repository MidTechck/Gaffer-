"""Original sponsor houses. Not real trademarks."""

CATALOG = [
    {"id": "fizzola", "name": "Fizzola", "kind": "drink", "per_home_win": 80_000, "season": 1_200_000, "task": "top5", "years": 2, "streak": 5_000, "award": "golden_boot", "award_pay": 250_000, "min_rank": "B"},
    {"id": "nexa", "name": "Nexa Mobile", "kind": "telecom", "per_home_win": 60_000, "season": 1_400_000, "task": "top4", "years": 3, "streak": 8_000, "award": "playmaker", "award_pay": 200_000, "min_rank": "C"},
    {"id": "hanova", "name": "Hanova", "kind": "electronics", "per_home_win": 55_000, "season": 1_600_000, "task": "top6", "years": 2, "streak": 6_000, "award": "young", "award_pay": 180_000, "min_rank": "C"},
    {"id": "gulfhouse", "name": "Gulf House Air", "kind": "airline", "per_home_win": 100_000, "season": 2_000_000, "task": "top3", "years": 3, "streak": 12_000, "award": "golden_boot", "award_pay": 400_000, "min_rank": "A"},
    {"id": "pulseplay", "name": "Pulse Play", "kind": "games", "per_home_win": 45_000, "season": 900_000, "task": "top8", "years": 2, "streak": 5_000, "award": "young", "award_pay": 120_000, "min_rank": "E"},
    {"id": "hexconsole", "name": "Hex Console", "kind": "games", "per_home_win": 48_000, "season": 950_000, "task": "top7", "years": 2, "streak": 5_000, "award": "playmaker", "award_pay": 130_000, "min_rank": "D"},
    {"id": "ironbank", "name": "Ironbank", "kind": "bank", "per_home_win": 40_000, "season": 1_800_000, "task": "top5", "years": 4, "streak": 7_000, "award": "club_poty", "award_pay": 220_000, "min_rank": "B"},
    {"id": "redstripe_tyres", "name": "Redstripe Tyres", "kind": "auto", "per_home_win": 35_000, "season": 700_000, "task": "top10", "years": 2, "streak": 5_000, "award": "club_poty", "award_pay": 90_000, "min_rank": "E"},
    {"id": "copperwire", "name": "Copper Wire Co", "kind": "energy", "per_home_win": 28_000, "season": 650_000, "task": "top8", "years": 2, "streak": 4_000, "award": "club_poty", "award_pay": 80_000, "min_rank": "E"},
    {"id": "savannah", "name": "Savannah Air", "kind": "airline", "per_home_win": 50_000, "season": 1_100_000, "task": "top6", "years": 3, "streak": 6_000, "award": "young", "award_pay": 140_000, "min_rank": "C"},
    {"id": "baobab", "name": "Baobab Bank", "kind": "bank", "per_home_win": 32_000, "season": 800_000, "task": "top7", "years": 3, "streak": 5_000, "award": "playmaker", "award_pay": 100_000, "min_rank": "D"},
    {"id": "nilelight", "name": "Nile Light", "kind": "energy", "per_home_win": 38_000, "season": 900_000, "task": "top5", "years": 2, "streak": 5_000, "award": "golden_boot", "award_pay": 160_000, "min_rank": "C"},
    {"id": "kalahari", "name": "Kalahari Motors", "kind": "auto", "per_home_win": 30_000, "season": 720_000, "task": "top10", "years": 2, "streak": 4_000, "award": "club_poty", "award_pay": 70_000, "min_rank": "E"},
]

RANK_ORDER = ["E", "D", "C", "B", "A", "A+", "S"]


def rank_ok(have: str, need: str) -> bool:
    try:
        return RANK_ORDER.index(have) >= RANK_ORDER.index(need)
    except ValueError:
        return False


def get(sid: str) -> dict:
    return next(s for s in CATALOG if s["id"] == sid)


def task_ok(task: str, place: int) -> bool:
    need = {"top3": 3, "top4": 4, "top5": 5, "top6": 6, "top7": 7, "top8": 8, "top10": 10}
    return place <= need.get(task, 20)
