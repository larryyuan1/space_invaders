import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import save_manager as sm_module
from save_manager import SaveManager


class TestSaveManager(unittest.TestCase):

    def setUp(self):
        # Each test gets a fresh temp file (deleted so SaveManager starts clean)
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.tmp.close()
        os.unlink(self.tmp.name)
        self._patch = patch.object(sm_module, "SAVE_FILE", self.tmp.name)
        self._patch.start()
        self.sm = SaveManager()

    def tearDown(self):
        self._patch.stop()
        if os.path.exists(self.tmp.name):
            os.unlink(self.tmp.name)

    # ── tokens ────────────────────────────────────────────────────────────────

    def test_initial_tokens_zero(self):
        self.assertEqual(self.sm.tokens, 0)

    def test_add_tokens(self):
        self.sm.add_tokens(25)
        self.assertEqual(self.sm.tokens, 25)

    def test_spend_tokens_success(self):
        self.sm.add_tokens(20)
        ok = self.sm.spend_tokens(15)
        self.assertTrue(ok)
        self.assertEqual(self.sm.tokens, 5)

    def test_spend_tokens_exact(self):
        self.sm.add_tokens(10)
        ok = self.sm.spend_tokens(10)
        self.assertTrue(ok)
        self.assertEqual(self.sm.tokens, 0)

    def test_spend_tokens_insufficient(self):
        self.sm.add_tokens(5)
        ok = self.sm.spend_tokens(10)
        self.assertFalse(ok)
        self.assertEqual(self.sm.tokens, 5)   # unchanged

    # ── daily login ───────────────────────────────────────────────────────────

    def test_daily_login_awards_tokens(self):
        reward = self.sm.check_daily_login()
        self.assertEqual(reward, 10)
        self.assertEqual(self.sm.tokens, 10)

    def test_daily_login_only_once_per_day(self):
        self.sm.check_daily_login()
        reward2 = self.sm.check_daily_login()
        self.assertEqual(reward2, 0)
        self.assertEqual(self.sm.tokens, 10)

    def test_daily_login_different_day(self):
        # Simulate yesterday's login then check today
        self.sm.data["last_login"] = "2000-01-01"
        self.sm.save()
        reward = self.sm.check_daily_login()
        self.assertEqual(reward, 10)

    # ── upgrades ──────────────────────────────────────────────────────────────

    def test_upgrade_stat_success(self):
        self.sm.add_tokens(50)
        ok, cost, lvl, _ = self.sm.upgrade_stat("viper", "speed")
        self.assertTrue(ok)
        self.assertEqual(cost, 5)
        self.assertEqual(lvl, 1)
        self.assertEqual(self.sm.get_upgrades("viper")["speed"], 1)

    def test_upgrade_stat_insufficient_tokens(self):
        ok, cost, lvl, _ = self.sm.upgrade_stat("viper", "speed")
        self.assertFalse(ok)
        self.assertEqual(lvl, 0)
        self.assertEqual(self.sm.get_upgrades("viper")["speed"], 0)

    def test_upgrade_stat_at_max_level(self):
        self.sm.add_tokens(500)
        for _ in range(11):
            self.sm.upgrade_stat("falcon", "damage")
        ok, cost, lvl, _ = self.sm.upgrade_stat("falcon", "damage")
        self.assertFalse(ok)
        self.assertEqual(lvl, 11)

    def test_upgrade_costs_scale_correctly(self):
        """Lv 1-3 = 5, Lv 4-6 = 10, Lv 7-9 = 20, Lv 10-11 = 40."""
        self.sm.add_tokens(500)
        expected = [5, 5, 5, 10, 10, 10, 20, 20, 20, 40, 40]
        for i, exp_cost in enumerate(expected):
            _, cost, _, _ = self.sm.upgrade_stat("titan", "fire_rate")
            self.assertEqual(cost, exp_cost, f"Level {i + 1}: expected {exp_cost}, got {cost}")

    def test_upgrade_persists_to_disk(self):
        self.sm.add_tokens(50)
        self.sm.upgrade_stat("viper", "bullets")
        sm2 = SaveManager()
        self.assertEqual(sm2.get_upgrades("viper")["bullets"], 1)

    def test_milestone_bonus_level_5(self):
        self.sm.add_tokens(500)
        for _ in range(4):
            self.sm.upgrade_stat("titan", "speed")
        _, _, _, milestone = self.sm.upgrade_stat("titan", "speed")
        self.assertEqual(milestone, 15)

    def test_milestone_bonus_level_11(self):
        self.sm.add_tokens(500)
        for _ in range(10):
            self.sm.upgrade_stat("viper", "damage")
        _, _, _, milestone = self.sm.upgrade_stat("viper", "damage")
        self.assertEqual(milestone, 30)

    def test_milestone_not_awarded_twice(self):
        self.sm.add_tokens(500)
        for _ in range(5):
            self.sm.upgrade_stat("falcon", "speed")
        # Reload and check key is stored (can't hit lv5 again, but key must be present)
        key = "falcon_speed_5"
        self.assertIn(key, self.sm.data["milestones_given"])

    # ── leaderboard ───────────────────────────────────────────────────────────

    def test_leaderboard_sorted_descending(self):
        self.sm.add_tokens(200)
        self.sm.add_score("Alice", 5000, "viper")
        self.sm.add_score("Bob",   3000, "falcon")
        self.sm.add_score("Eve",   8000, "titan")
        lb = self.sm.get_leaderboard()
        self.assertEqual(lb[0]["name"], "Eve")
        self.assertEqual(lb[1]["name"], "Alice")
        self.assertEqual(lb[2]["name"], "Bob")

    def test_leaderboard_rank1_token_bonus(self):
        self.sm.add_tokens(200)
        tokens_before = self.sm.tokens
        bonus = self.sm.add_score("Player", 9999, "viper")
        self.assertEqual(bonus, 50)
        self.assertEqual(self.sm.tokens, tokens_before + 50)

    def test_leaderboard_rank2_token_bonus(self):
        self.sm.add_tokens(200)
        self.sm.add_score("First", 9999, "viper")
        bonus = self.sm.add_score("Second", 8000, "falcon")
        self.assertEqual(bonus, 30)

    def test_leaderboard_no_bonus_outside_top3(self):
        self.sm.add_tokens(200)
        for i in range(3):
            self.sm.add_score(f"P{i}", 9000 - i * 100, "viper")
        bonus = self.sm.add_score("Last", 100, "titan")
        self.assertEqual(bonus, 0)

    def test_leaderboard_capped_at_20(self):
        self.sm.add_tokens(1000)
        for i in range(25):
            self.sm.add_score(f"P{i}", i * 10, "viper")
        self.assertEqual(len(self.sm.get_leaderboard()), 20)

    def test_leaderboard_empty_initially(self):
        self.assertEqual(self.sm.get_leaderboard(), [])
