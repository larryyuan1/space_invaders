import json
import os
from datetime import date

from constants import UPGRADE_COSTS, TOKEN_DAILY, TOKEN_RANK, TOKEN_MILESTONE

SAVE_FILE = os.path.join(os.path.dirname(__file__), "save_data.json")

_DEFAULT_UPGRADES = {"speed": 0, "fire_rate": 0, "damage": 0, "bullets": 0}


def _fresh():
    return {
        "tokens": 0,
        "last_login": None,
        "ships": {
            sid: {"upgrades": _DEFAULT_UPGRADES.copy()}
            for sid in ("viper", "falcon", "titan")
        },
        "leaderboard": [],
        "milestones_given": {},   # "viper_speed_5": True  etc.
    }


class SaveManager:
    def __init__(self):
        self.data = self._load()

    # ── persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE) as f:
                    data = json.load(f)
                for sid in ("viper", "falcon", "titan"):
                    data["ships"].setdefault(sid, {"upgrades": _DEFAULT_UPGRADES.copy()})
                data.setdefault("milestones_given", {})
                return data
            except Exception:
                pass
        return _fresh()

    def save(self):
        with open(SAVE_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    # ── tokens ────────────────────────────────────────────────────────────────

    @property
    def tokens(self):
        return self.data["tokens"]

    def add_tokens(self, amount):
        self.data["tokens"] += amount
        self.save()

    def spend_tokens(self, amount):
        if self.data["tokens"] >= amount:
            self.data["tokens"] -= amount
            self.save()
            return True
        return False

    # ── daily login ───────────────────────────────────────────────────────────

    def check_daily_login(self):
        """Award daily tokens once per calendar day. Returns amount awarded."""
        today = str(date.today())
        if self.data.get("last_login") != today:
            self.data["last_login"] = today
            self.data["tokens"] += TOKEN_DAILY
            self.save()
            return TOKEN_DAILY
        return 0

    # ── upgrades ──────────────────────────────────────────────────────────────

    def get_upgrades(self, ship_id):
        return self.data["ships"][ship_id]["upgrades"]

    def upgrade_stat(self, ship_id, stat):
        """
        Attempt to upgrade stat for ship.
        Returns (success: bool, cost: int, new_level: int, milestone_tokens: int).
        """
        ups = self.data["ships"][ship_id]["upgrades"]
        cur = ups[stat]
        if cur >= 11:
            return False, 0, cur, 0
        cost = UPGRADE_COSTS[cur + 1]
        if not self.spend_tokens(cost):
            return False, cost, cur, 0
        ups[stat] = cur + 1
        new_lvl = ups[stat]

        # milestone bonus
        milestone_tokens = 0
        key = f"{ship_id}_{stat}_{new_lvl}"
        if new_lvl in TOKEN_MILESTONE and key not in self.data["milestones_given"]:
            bonus = TOKEN_MILESTONE[new_lvl]
            self.data["tokens"] += bonus
            self.data["milestones_given"][key] = True
            milestone_tokens = bonus

        self.save()
        return True, cost, new_lvl, milestone_tokens

    # ── leaderboard ───────────────────────────────────────────────────────────

    def add_score(self, name, score, ship_id):
        """Add score, sort, trim to top 20. Returns rank-based token bonus."""
        lb = self.data["leaderboard"]
        lb.append({"name": name, "score": score, "ship": ship_id})
        lb.sort(key=lambda x: x["score"], reverse=True)
        self.data["leaderboard"] = lb[:20]

        rank_bonus = 0
        for rank, entry in enumerate(self.data["leaderboard"][:3], 1):
            if entry["name"] == name and entry["score"] == score:
                rank_bonus = TOKEN_RANK.get(rank, 0)
                if rank_bonus:
                    self.data["tokens"] += rank_bonus
                break

        self.save()
        return rank_bonus

    def get_leaderboard(self):
        return self.data["leaderboard"]
