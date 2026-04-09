import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Minimal pygame init — no visible window needed
import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from constants import (
    SHIPS, SCREEN_HEIGHT, FIRE_COOLDOWN_MIN,
    ENEMY_ROWS, ENEMY_COLS,
)
from entities import Player, Bullet, Enemy, EnemyGrid


# ── helpers ───────────────────────────────────────────────────────────────────

def _ups(**kwargs):
    base = {"speed": 0, "fire_rate": 0, "damage": 0, "bullets": 0}
    base.update(kwargs)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# Player stat calculations
# ══════════════════════════════════════════════════════════════════════════════

class TestPlayerStats(unittest.TestCase):

    def test_viper_base_speed(self):
        p = Player("viper", _ups())
        self.assertAlmostEqual(p.speed, SHIPS["viper"]["speed"])

    def test_falcon_base_speed(self):
        p = Player("falcon", _ups())
        self.assertAlmostEqual(p.speed, SHIPS["falcon"]["speed"])

    def test_titan_base_speed(self):
        p = Player("titan", _ups())
        self.assertAlmostEqual(p.speed, SHIPS["titan"]["speed"])

    def test_speed_upgrade_applied(self):
        p = Player("viper", _ups(speed=3))
        self.assertAlmostEqual(p.speed, SHIPS["viper"]["speed"] + 3 * 0.4)

    def test_fire_cooldown_base(self):
        p = Player("falcon", _ups())
        self.assertEqual(p.fire_cooldown, SHIPS["falcon"]["fire_cooldown"])

    def test_fire_cooldown_reduced_by_upgrade(self):
        p = Player("falcon", _ups(fire_rate=5))
        expected = max(FIRE_COOLDOWN_MIN, SHIPS["falcon"]["fire_cooldown"] - 5 * 2)
        self.assertEqual(p.fire_cooldown, expected)

    def test_fire_cooldown_never_below_minimum(self):
        p = Player("viper", _ups(fire_rate=11))
        self.assertGreaterEqual(p.fire_cooldown, FIRE_COOLDOWN_MIN)

    def test_damage_base(self):
        p = Player("titan", _ups())
        self.assertEqual(p.damage, SHIPS["titan"]["damage"])

    def test_damage_upgrade_applied(self):
        p = Player("titan", _ups(damage=4))
        self.assertEqual(p.damage, SHIPS["titan"]["damage"] + 4)

    def test_bullet_count_default(self):
        p = Player("viper", _ups())
        self.assertEqual(p.bullet_count, 1)

    def test_bullet_count_at_upgrade_level_3(self):
        p = Player("falcon", _ups(bullets=3))
        self.assertEqual(p.bullet_count, 2)

    def test_bullet_count_at_upgrade_level_6(self):
        p = Player("falcon", _ups(bullets=6))
        self.assertEqual(p.bullet_count, 3)

    def test_bullet_count_at_upgrade_level_9(self):
        p = Player("falcon", _ups(bullets=9))
        self.assertEqual(p.bullet_count, 4)

    def test_bullet_count_at_upgrade_level_11(self):
        p = Player("falcon", _ups(bullets=11))
        self.assertEqual(p.bullet_count, 5)


# ══════════════════════════════════════════════════════════════════════════════
# Player state & rect
# ══════════════════════════════════════════════════════════════════════════════

class TestPlayerState(unittest.TestCase):

    def test_starts_with_3_lives(self):
        p = Player("viper", _ups())
        self.assertEqual(p.lives, 3)

    def test_starts_alive(self):
        p = Player("viper", _ups())
        self.assertTrue(p.alive)

    def test_hit_reduces_lives(self):
        p = Player("viper", _ups())
        p.hit([])
        self.assertEqual(p.lives, 2)

    def test_invincibility_prevents_immediate_second_hit(self):
        p = Player("viper", _ups())
        p.hit([])
        p.hit([])   # blocked by invincibility
        self.assertEqual(p.lives, 2)

    def test_three_hits_kills_player(self):
        p = Player("viper", _ups())
        p.hit([]);  p.invincible = 0
        p.hit([]);  p.invincible = 0
        p.hit([])
        self.assertFalse(p.alive)
        self.assertEqual(p.lives, 0)

    def test_rect_correct_width_height(self):
        p = Player("falcon", _ups())
        r = p.rect
        self.assertEqual(r.width,  SHIPS["falcon"]["width"])
        self.assertEqual(r.height, SHIPS["falcon"]["height"])

    def test_rect_centered_on_position(self):
        p = Player("viper", _ups())
        r = p.rect
        self.assertEqual(r.centerx, int(p.x))
        self.assertEqual(r.centery, int(p.y))


# ══════════════════════════════════════════════════════════════════════════════
# Bullet
# ══════════════════════════════════════════════════════════════════════════════

class TestBullet(unittest.TestCase):

    def test_player_bullet_moves_up(self):
        b = Bullet(100, 200, dy=-12)
        b.update()
        self.assertEqual(b.y, 188)

    def test_enemy_bullet_moves_down(self):
        b = Bullet(100, 200, dy=6)
        b.update()
        self.assertEqual(b.y, 206)

    def test_bullet_alive_mid_screen(self):
        b = Bullet(100, 300, dy=-12)
        b.update()
        self.assertTrue(b.alive)

    def test_bullet_dies_off_top(self):
        # needs to pass y < -20; start at -9 so after dy=-12 it's at -21
        b = Bullet(100, -9, dy=-12)
        b.update()
        self.assertFalse(b.alive)

    def test_bullet_dies_off_bottom(self):
        # needs to pass y > SCREEN_HEIGHT+20; start at +9 so after dy=12 it's at +21
        b = Bullet(100, SCREEN_HEIGHT + 9, dy=12)
        b.update()
        self.assertFalse(b.alive)

    def test_rect_centered_on_position(self):
        b = Bullet(200, 300, dy=-10)
        self.assertEqual(b.rect.centerx, 200)
        self.assertEqual(b.rect.centery, 300)

    def test_default_damage(self):
        b = Bullet(0, 0, dy=-10)
        self.assertEqual(b.damage, 1)

    def test_custom_damage(self):
        b = Bullet(0, 0, dy=-10, damage=4)
        self.assertEqual(b.damage, 4)


# ══════════════════════════════════════════════════════════════════════════════
# Enemy
# ══════════════════════════════════════════════════════════════════════════════

class TestEnemy(unittest.TestCase):

    def test_top_row_is_type0_worth_30(self):
        e = Enemy(0, 0, 100, 100)
        self.assertEqual(e.etype, 0)
        self.assertEqual(e.points, 30)

    def test_row1_is_type1_worth_20(self):
        e = Enemy(1, 0, 100, 100)
        self.assertEqual(e.etype, 1)
        self.assertEqual(e.points, 20)

    def test_row2_is_type1_worth_20(self):
        e = Enemy(2, 0, 100, 100)
        self.assertEqual(e.etype, 1)
        self.assertEqual(e.points, 20)

    def test_row3_is_type2_worth_10(self):
        e = Enemy(3, 0, 100, 100)
        self.assertEqual(e.etype, 2)
        self.assertEqual(e.points, 10)

    def test_bottom_row_is_type2_worth_10(self):
        e = Enemy(4, 0, 100, 100)
        self.assertEqual(e.etype, 2)
        self.assertEqual(e.points, 10)

    def test_rect_centered_on_position(self):
        e = Enemy(0, 0, 200, 300)
        self.assertEqual(e.rect.centerx, 200)
        self.assertEqual(e.rect.centery, 300)

    def test_starts_alive(self):
        e = Enemy(0, 0, 100, 100)
        self.assertTrue(e.alive)


# ══════════════════════════════════════════════════════════════════════════════
# EnemyGrid
# ══════════════════════════════════════════════════════════════════════════════

class TestEnemyGrid(unittest.TestCase):

    def test_grid_starts_full(self):
        g = EnemyGrid()
        self.assertEqual(g.alive_count, ENEMY_ROWS * ENEMY_COLS)

    def test_killing_enemy_reduces_count(self):
        g = EnemyGrid()
        g.enemies[0].alive = False
        self.assertEqual(g.alive_count, ENEMY_ROWS * ENEMY_COLS - 1)

    def test_all_enemies_killed(self):
        g = EnemyGrid()
        for e in g.enemies:
            e.alive = False
        self.assertEqual(g.alive_count, 0)
        self.assertEqual(g.alive, [])

    def test_grid_total_enemies(self):
        g = EnemyGrid()
        self.assertEqual(len(g.enemies), ENEMY_ROWS * ENEMY_COLS)

    def test_top_row_enemies_are_type0(self):
        g = EnemyGrid()
        top_row = [e for e in g.enemies if e.row == 0]
        self.assertTrue(all(e.etype == 0 for e in top_row))

    def test_bottom_rows_are_type2(self):
        g = EnemyGrid()
        bottom = [e for e in g.enemies if e.row >= 3]
        self.assertTrue(all(e.etype == 2 for e in bottom))


if __name__ == "__main__":
    unittest.main()
