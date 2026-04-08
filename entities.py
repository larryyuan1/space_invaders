import pygame
import random
import math
from constants import *


# ── Bullet ────────────────────────────────────────────────────────────────────

class Bullet:
    W = 4
    H = 12

    def __init__(self, x, y, dy, damage=1, color=YELLOW):
        self.x      = x
        self.y      = y
        self.dy     = dy        # negative = up (player), positive = down (enemy)
        self.damage = damage
        self.color  = color
        self.alive  = True

    def update(self):
        self.y += self.dy
        if self.y < -20 or self.y > SCREEN_HEIGHT + 20:
            self.alive = False

    def draw(self, surf):
        r = pygame.Rect(int(self.x) - self.W // 2, int(self.y) - self.H // 2, self.W, self.H)
        pygame.draw.rect(surf, self.color, r, border_radius=2)
        # soft glow
        glow = pygame.Surface((self.W + 6, self.H + 6), pygame.SRCALPHA)
        gc = (*self.color, 60)
        pygame.draw.rect(glow, gc, (0, 0, self.W + 6, self.H + 6), border_radius=3)
        surf.blit(glow, (r.left - 3, r.top - 3))

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W // 2, int(self.y) - self.H // 2, self.W, self.H)


# ── Explosion ─────────────────────────────────────────────────────────────────

class Explosion:
    LIFETIME = 28

    def __init__(self, x, y, color=ORANGE, size=20):
        self.x     = x
        self.y     = y
        self.color = color
        self.frame = 0
        self.alive = True
        self.particles = [
            {
                "x": float(x), "y": float(y),
                "dx": random.uniform(-3.5, 3.5),
                "dy": random.uniform(-3.5, 3.5),
                "r":  random.randint(2, 5),
            }
            for _ in range(14)
        ]

    def update(self):
        self.frame += 1
        for p in self.particles:
            p["x"] += p["dx"]
            p["y"] += p["dy"]
            p["dy"] += 0.15
        if self.frame >= self.LIFETIME:
            self.alive = False

    def draw(self, surf):
        alpha = max(0, 255 - int(255 * self.frame / self.LIFETIME))
        for p in self.particles:
            r = max(1, p["r"])
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
            surf.blit(s, (int(p["x"]) - r, int(p["y"]) - r))


# ── Ship drawing (shared between Player and preview renders) ──────────────────

def draw_ship(surf, ship_id, cx, cy, scale=1.0, color=None, outline=WHITE, line_w=1):
    """Draw any ship centered at (cx, cy) at the given scale."""
    base  = SHIPS[ship_id]
    col   = color if color else base["color"]
    w2    = int(base["width"]  * scale / 2)
    h2    = int(base["height"] * scale / 2)

    if ship_id == "viper":
        pts = [
            (cx,             cy - h2),
            (cx - w2,        cy + h2),
            (cx - w2 // 3,   cy),
            (cx + w2 // 3,   cy),
            (cx + w2,        cy + h2),
        ]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, outline, pts, line_w)
        # engine glow
        pygame.draw.circle(surf, (80, 255, 180), (cx, cy + h2 - 2), max(2, int(4 * scale)))

    elif ship_id == "falcon":
        pts = [
            (cx,               cy - h2),
            (cx - w2,          cy + h2),
            (cx - w2 // 2,     cy + h2 // 2),
            (cx,               cy + h2 // 3),
            (cx + w2 // 2,     cy + h2 // 2),
            (cx + w2,          cy + h2),
        ]
        pygame.draw.polygon(surf, col, pts)
        pygame.draw.polygon(surf, outline, pts, line_w)
        # cockpit
        pygame.draw.ellipse(surf, (200, 230, 255),
                            (cx - max(1, int(6 * scale)), cy - h2 // 2,
                             max(2, int(12 * scale)), h2 // 2))
        # engines
        er = max(2, int(4 * scale))
        pygame.draw.circle(surf, (120, 180, 255), (cx - w2 // 3, cy + h2 - 2), er)
        pygame.draw.circle(surf, (120, 180, 255), (cx + w2 // 3, cy + h2 - 2), er)

    else:  # titan
        # main body
        body = pygame.Rect(cx - w2 // 2, cy - h2, w2, int(h2 * 1.8))
        pygame.draw.rect(surf, col, body, border_radius=max(2, int(4 * scale)))
        # wings
        lw = [(cx - w2, cy + h2 // 2), (cx - w2 // 2, cy - h2 // 4), (cx - w2 // 2, cy + h2)]
        rw = [(cx + w2, cy + h2 // 2), (cx + w2 // 2, cy - h2 // 4), (cx + w2 // 2, cy + h2)]
        pygame.draw.polygon(surf, col, lw)
        pygame.draw.polygon(surf, col, rw)
        pygame.draw.polygon(surf, outline, lw, line_w)
        pygame.draw.polygon(surf, outline, rw, line_w)
        pygame.draw.rect(surf, outline, body, line_w, border_radius=max(2, int(4 * scale)))
        # cannon barrel
        bw = max(2, int(5 * scale))
        bh = max(4, int(10 * scale))
        pygame.draw.rect(surf, outline, (cx - bw // 2, cy - h2 - bh, bw, bh))
        # engines
        er = max(2, int(4 * scale))
        for ex in (-w2 // 3, 0, w2 // 3):
            pygame.draw.circle(surf, (255, 160, 80), (cx + ex, cy + h2 - 2), er)


# ── Player ────────────────────────────────────────────────────────────────────

class Player:
    BULLET_SPEED     = 12
    INVINCIBLE_FRAMES = 120   # 2 sec

    def __init__(self, ship_id, upgrades):
        self.ship_id = ship_id
        base = SHIPS[ship_id]
        ups  = upgrades

        self.speed = base["speed"] + ups["speed"] * UPGRADE_SPEED_BOOST
        self.fire_cooldown = max(
            FIRE_COOLDOWN_MIN,
            base["fire_cooldown"] - ups["fire_rate"] * UPGRADE_FIRE_REDUCTION
        )
        self.damage = base["damage"] + ups["damage"] * UPGRADE_DAMAGE_BOOST

        bul_lvl = ups["bullets"]
        self.bullet_count = 1
        for lvl, cnt in sorted(BULLET_COUNT_TABLE.items()):
            if bul_lvl >= lvl:
                self.bullet_count = cnt

        self.color  = base["color"]
        self.width  = base["width"]
        self.height = base["height"]

        self.x          = SCREEN_WIDTH // 2
        self.y          = PLAYER_Y
        self.lives      = PLAYER_LIVES
        self.score      = 0
        self.fire_timer = 0
        self.invincible = 0
        self.alive      = True

    # ── input & state ─────────────────────────────────────────────────────────

    def handle_input(self, keys, bullets):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        half = self.width // 2
        self.x = max(half, min(SCREEN_WIDTH - half, self.x))

        self.fire_timer = max(0, self.fire_timer - 1)
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.fire_timer == 0:
            self._shoot(bullets)
            self.fire_timer = self.fire_cooldown

    def _shoot(self, bullets):
        top = self.y - self.height // 2
        if self.bullet_count == 1:
            bullets.append(Bullet(self.x, top, -self.BULLET_SPEED, self.damage, YELLOW))
        else:
            spread = 10
            for i in range(self.bullet_count):
                ox = (i - (self.bullet_count - 1) / 2) * spread
                bullets.append(Bullet(self.x + ox, top, -self.BULLET_SPEED, self.damage, YELLOW))

    def update(self):
        if self.invincible > 0:
            self.invincible -= 1

    def hit(self, explosions):
        if self.invincible > 0:
            return
        self.lives -= 1
        self.invincible = self.INVINCIBLE_FRAMES
        explosions.append(Explosion(self.x, self.y, self.color))
        if self.lives <= 0:
            self.alive = False

    # ── drawing ───────────────────────────────────────────────────────────────

    def draw(self, surf):
        if self.invincible > 0 and (self.invincible // 8) % 2 == 0:
            return
        draw_ship(surf, self.ship_id, int(self.x), int(self.y))

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x) - self.width  // 2,
            int(self.y) - self.height // 2,
            self.width, self.height
        )


# ── Enemy ─────────────────────────────────────────────────────────────────────

_ENEMY_COLORS = [
    (255,  50,  50),   # type 0 – top row (30 pts)
    (255, 150,  50),   # type 1 – middle rows (20 pts)
    (150,  50, 255),   # type 2 – bottom rows (10 pts)
]

class Enemy:
    W = 38
    H = 26

    def __init__(self, row, col, x, y):
        self.row   = row
        self.col   = col
        self.x     = float(x)
        self.y     = float(y)
        self.etype = 0 if row == 0 else (1 if row <= 2 else 2)
        self.points = ENEMY_POINTS[self.etype]
        self.color  = _ENEMY_COLORS[self.etype]
        self.alive  = True
        self.anim   = 0   # 0 or 1

    def draw(self, surf):
        if not self.alive:
            return
        x, y = int(self.x), int(self.y)
        w2, h2 = self.W // 2, self.H // 2
        c = self.color
        a = self.anim

        if self.etype == 0:
            self._draw_squid(surf, x, y, w2, h2, c, a)
        elif self.etype == 1:
            self._draw_crab(surf, x, y, w2, h2, c, a)
        else:
            self._draw_octo(surf, x, y, w2, h2, c, a)

    # ── enemy sprite helpers ──────────────────────────────────────────────────

    @staticmethod
    def _draw_squid(surf, x, y, w2, h2, c, a):
        # body ellipse
        pygame.draw.ellipse(surf, c, (x - w2 + 4, y - h2, (w2 - 4) * 2, h2 * 2))
        # eyes
        for ex, col in [(-w2 // 3, WHITE), (w2 // 3, WHITE)]:
            pygame.draw.circle(surf, col, (x + ex, y - 2), 4)
            pygame.draw.circle(surf, BLACK, (x + ex, y - 2), 2)
        # antennae
        ao = (-6 if a == 0 else 6)
        pygame.draw.line(surf, c, (x - w2 // 2, y - h2), (x - w2 + ao, y - h2 - 7), 2)
        pygame.draw.line(surf, c, (x + w2 // 2, y - h2), (x + w2 - ao, y - h2 - 7), 2)
        # legs
        for lx in [-w2 + 2, -w2 // 2, 0, w2 // 2, w2 - 2]:
            lo = (-3 if a == 0 else 3)
            pygame.draw.line(surf, c, (x + lx, y + h2), (x + lx + lo, y + h2 + 6), 2)
        pygame.draw.ellipse(surf, WHITE, (x - w2 + 4, y - h2, (w2 - 4) * 2, h2 * 2), 1)

    @staticmethod
    def _draw_crab(surf, x, y, w2, h2, c, a):
        body = pygame.Rect(x - w2 + 5, y - h2 + 3, (w2 - 5) * 2, (h2 - 3) * 2)
        pygame.draw.rect(surf, c, body, border_radius=4)
        # claws
        if a == 0:
            cl = [(x - w2 + 5, y), (x - w2 - 2, y - 5), (x - w2 - 2, y + 5)]
            cr = [(x + w2 - 5, y), (x + w2 + 2, y - 5), (x + w2 + 2, y + 5)]
        else:
            cl = [(x - w2 + 5, y), (x - w2 - 2, y - 2), (x - w2,     y + 6)]
            cr = [(x + w2 - 5, y), (x + w2 + 2, y - 2), (x + w2,     y + 6)]
        pygame.draw.polygon(surf, c, cl)
        pygame.draw.polygon(surf, c, cr)
        # eyes
        for ex in [-w2 // 3, w2 // 3]:
            pygame.draw.circle(surf, WHITE, (x + ex, y - 2), 3)
            pygame.draw.circle(surf, BLACK, (x + ex, y - 2), 1)
        # legs
        for i, lx in enumerate([-w2 + 4, -w2 + 10, w2 - 10, w2 - 4]):
            lo = (3 if i >= 2 else -3) * (1 if a == 0 else -1)
            pygame.draw.line(surf, c, (x + lx, y + h2 - 3), (x + lx + lo, y + h2 + 6), 2)
        pygame.draw.rect(surf, WHITE, body, 1, border_radius=4)

    @staticmethod
    def _draw_octo(surf, x, y, w2, h2, c, a):
        # cap
        pygame.draw.ellipse(surf, c, (x - w2, y - h2, w2 * 2, h2 + 4))
        # body
        body = pygame.Rect(x - w2 // 2, y, w2, h2)
        pygame.draw.rect(surf, c, body)
        # tentacles
        for i, ox in enumerate([-w2, -w2 // 2, w2 // 2, w2]):
            end_y = y + h2 + (6 if (i + a) % 2 == 0 else 3)
            end_x = x + ox + (3 if a == 0 else -3)
            pygame.draw.line(surf, c, (x + ox // 2, y + h2), (end_x, end_y), 2)
        # eyes
        for ex in [-w2 // 3, w2 // 3]:
            pygame.draw.circle(surf, WHITE, (x + ex, y - h2 // 4), 3)
            pygame.draw.circle(surf, BLACK, (x + ex, y - h2 // 4), 1)
        pygame.draw.ellipse(surf, WHITE, (x - w2, y - h2, w2 * 2, h2 + 4), 1)

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x) - self.W // 2,
            int(self.y) - self.H // 2,
            self.W, self.H
        )


# ── Enemy Grid ────────────────────────────────────────────────────────────────

class EnemyGrid:
    def __init__(self):
        self.enemies    = []
        self.direction  = 1   # 1=right, -1=left
        self.move_timer = 0
        self.anim_frame = 0
        self.shoot_timer = 0
        self.total      = ENEMY_ROWS * ENEMY_COLS
        self._build()

    def _build(self):
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = ENEMY_START_X + col * ENEMY_COL_SPACING
                y = ENEMY_START_Y + row * ENEMY_ROW_SPACING
                self.enemies.append(Enemy(row, col, x, y))

    @property
    def alive(self):
        return [e for e in self.enemies if e.alive]

    @property
    def alive_count(self):
        return sum(1 for e in self.enemies if e.alive)

    def _move_interval(self):
        ratio = self.alive_count / self.total
        return max(ENEMY_MOVE_INTERVAL_MIN,
                   int(ENEMY_MOVE_INTERVAL_MAX * ratio))

    def update(self, enemy_bullets):
        living = self.alive
        if not living:
            return

        # ── movement ──────────────────────────────────────────────────────────
        self.move_timer += 1
        if self.move_timer >= self._move_interval():
            self.move_timer = 0
            self.anim_frame ^= 1
            for e in living:
                e.anim = self.anim_frame

            rightmost = max(e.x for e in living)
            leftmost  = min(e.x for e in living)
            step = ENEMY_STEP * self.direction

            would_right = rightmost + step + Enemy.W // 2
            would_left  = leftmost  + step - Enemy.W // 2

            if would_right >= SCREEN_WIDTH or would_left <= 0:
                for e in living:
                    e.y += ENEMY_DROP
                self.direction *= -1
            else:
                for e in living:
                    e.x += step

        # ── shooting ──────────────────────────────────────────────────────────
        self.shoot_timer += 1
        # shoot faster as grid thins
        shoot_interval = max(30,
            ENEMY_SHOOT_INTERVAL - (self.total - self.alive_count))
        if self.shoot_timer >= shoot_interval:
            self.shoot_timer = 0
            # bottom enemy per column
            col_map = {}
            for e in living:
                if e.col not in col_map or e.row > col_map[e.col].row:
                    col_map[e.col] = e
            shooter = random.choice(list(col_map.values()))
            enemy_bullets.append(
                Bullet(shooter.x, shooter.y + Enemy.H // 2, dy=6, damage=1, color=RED)
            )

    def draw(self, surf):
        for e in self.enemies:
            e.draw(surf)

    def reached_player_line(self):
        for e in self.alive:
            if e.y + Enemy.H // 2 >= PLAYER_Y - 15:
                return True
        return False


# ── Mystery Ship ─────────────────────────────────────────────────────────────

class MysteryShip:
    W = 60
    H = 26
    SPEED = 3

    def __init__(self):
        self.direction = random.choice([-1, 1])
        self.x = float(-self.W if self.direction == 1 else SCREEN_WIDTH + self.W)
        self.y = 65
        self.alive  = True
        self.points = MYSTERY_POINTS

    def update(self):
        self.x += self.SPEED * self.direction
        if self.x < -self.W - 30 or self.x > SCREEN_WIDTH + self.W + 30:
            self.alive = False

    def draw(self, surf):
        x, y = int(self.x), self.y
        w2, h2 = self.W // 2, self.H // 2
        pygame.draw.ellipse(surf, PURPLE,        (x - w2,      y,      self.W, h2))
        pygame.draw.ellipse(surf, (200, 100, 255),(x - w2 // 2, y - h2, w2,    h2 + 3))
        for lx in range(-w2 + 8, w2, 10):
            pygame.draw.circle(surf, YELLOW, (x + lx, y + h2 // 2), 2)
        pygame.draw.ellipse(surf, WHITE, (x - w2, y, self.W, h2), 1)

    @property
    def rect(self):
        return pygame.Rect(int(self.x) - self.W // 2, self.y - self.H // 2, self.W, self.H)


# ── Bunker ────────────────────────────────────────────────────────────────────

_BUNKER_PATTERN = [
    "  XXXXXXXX  ",
    " XXXXXXXXXX ",
    "XXXXXXXXXXXX",
    "XXXXXXXXXXXX",
    "XXXXXXXXXXXX",
    "XXX      XXX",
    "XX        XX",
]
_BLOCK = 6

class BunkerBlock:
    def __init__(self, x, y):
        self.x    = x
        self.y    = y
        self.hp   = 4
        self.alive = True

    def hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        g = min(255, int(60 + 50 * self.hp))
        pygame.draw.rect(surf, (0, g, 0), (self.x, self.y, _BLOCK, _BLOCK))


class Bunker:
    def __init__(self, center_x, top_y):
        self.blocks = []
        cols = len(_BUNKER_PATTERN[0])
        for r, row in enumerate(_BUNKER_PATTERN):
            for c, ch in enumerate(row):
                if ch == "X":
                    bx = center_x - (cols * _BLOCK) // 2 + c * _BLOCK
                    by = top_y + r * _BLOCK
                    self.blocks.append(BunkerBlock(bx, by))

    def check_hit(self, bullet):
        """Destroy first block hit; mark bullet dead. Returns True if hit."""
        br = bullet.rect
        for blk in self.blocks:
            if not blk.alive:
                continue
            if br.colliderect(pygame.Rect(blk.x, blk.y, _BLOCK, _BLOCK)):
                blk.hit()
                bullet.alive = False
                return True
        return False

    def draw(self, surf):
        for blk in self.blocks:
            blk.draw(surf)
