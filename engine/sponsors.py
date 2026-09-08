"""In-game shirt houses. Not official partnerships."""

CATALOG = [
    {"id": "cocacola", "name": "Coca-Cola", "kind": "drink", "per_home_win": 90_000, "season": 1_800_000, "task": "top5", "years": 3, "streak": 8_000, "award": "golden_boot", "award_pay": 300_000, "min_rank": "B"},
    {"id": "pepsi", "name": "Pepsi", "kind": "drink", "per_home_win": 75_000, "season": 1_500_000, "task": "top6", "years": 2, "streak": 6_000, "award": "young", "award_pay": 200_000, "min_rank": "C"},
    {"id": "samsung", "name": "Samsung", "kind": "electronics", "per_home_win": 85_000, "season": 2_000_000, "task": "top4", "years": 3, "streak": 9_000, "award": "playmaker", "award_pay": 280_000, "min_rank": "B"},
    {"id": "bmw", "name": "BMW", "kind": "auto", "per_home_win": 110_000, "season": 2_400_000, "task": "top3", "years": 3, "streak": 12_000, "award": "golden_boot", "award_pay": 400_000, "min_rank": "A"},
    {"id": "toyota", "name": "Toyota", "kind": "auto", "per_home_win": 70_000, "season": 1_300_000, "task": "top6", "years": 2, "streak": 6_000, "award": "club_poty", "award_pay": 180_000, "min_rank": "C"},
    {"id": "mtn", "name": "MTN", "kind": "telecom", "per_home_win": 55_000, "season": 1_100_000, "task": "top8", "years": 3, "streak": 5_000, "award": "young", "award_pay": 140_000, "min_rank": "D"},
    {"id": "qatar", "name": "Qatar Airways", "kind": "airline", "per_home_win": 120_000, "season": 2_600_000, "task": "top3", "years": 4, "streak": 14_000, "award": "golden_boot", "award_pay": 450_000, "min_rank": "A"},
    {"id": "sony", "name": "Sony", "kind": "electronics", "per_home_win": 65_000, "season": 1_400_000, "task": "top5", "years": 2, "streak": 7_000, "award": "playmaker", "award_pay": 220_000, "min_rank": "C"},
    {"id": "adidas", "name": "Adidas", "kind": "kit", "per_home_win": 80_000, "season": 1_700_000, "task": "top4", "years": 3, "streak": 8_000, "award": "club_poty", "award_pay": 260_000, "min_rank": "B"},
    {"id": "nike", "name": "Nike", "kind": "kit", "per_home_win": 95_000, "season": 2_100_000, "task": "top3", "years": 3, "streak": 10_000, "award": "young", "award_pay": 320_000, "min_rank": "A"},
    {"id": "emirates", "name": "Emirates", "kind": "airline", "per_home_win": 130_000, "season": 2_800_000, "task": "top3", "years": 4, "streak": 15_000, "award": "golden_boot", "award_pay": 500_000, "min_rank": "A"},
    {"id": "visa", "name": "Visa", "kind": "bank", "per_home_win": 60_000, "season": 1_600_000, "task": "top5", "years": 3, "streak": 7_000, "award": "playmaker", "award_pay": 200_000, "min_rank": "B"},
    {"id": "redbull", "name": "Red Bull", "kind": "drink", "per_home_win": 50_000, "season": 1_000_000, "task": "top8", "years": 2, "streak": 5_000, "award": "young", "award_pay": 150_000, "min_rank": "D"},
    {"id": "hyundai", "name": "Hyundai", "kind": "auto", "per_home_win": 58_000, "season": 1_150_000, "task": "top7", "years": 2, "streak": 5_000, "award": "club_poty", "award_pay": 160_000, "min_rank": "C"},
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
