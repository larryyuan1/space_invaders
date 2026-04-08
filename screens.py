import pygame
import sys
import math
import random

from constants import *
from entities  import Player, EnemyGrid, Bullet, Explosion, MysteryShip, Bunker, draw_ship
from ui        import Button, TextInput


# ── Background stars ──────────────────────────────────────────────────────────

def _make_stars(n=150):
    stars = []
    for _ in range(n):
        b = random.randint(60, 200)
        stars.append([
            random.randint(0, SCREEN_WIDTH),
            random.randint(0, SCREEN_HEIGHT),
            (b, b, b),
            random.choice([1, 1, 1, 2]),
        ])
    return stars

def _scroll_stars(stars):
    for s in stars:
        s[1] += 0.3
        if s[1] > SCREEN_HEIGHT:
            s[1] = 0
            s[0] = random.randint(0, SCREEN_WIDTH)

def _draw_stars(surf, stars):
    for s in stars:
        pygame.draw.circle(surf, s[2], (int(s[0]), int(s[1])), s[3])


# ── Stat bar helper ───────────────────────────────────────────────────────────

def _stat_bar(surf, font, x, y, label, value, max_val, color, bar_w=140):
    lbl = font.render(label, True, GRAY)
    surf.blit(lbl, (x, y))
    bg = pygame.Rect(x, y + 20, bar_w, 10)
    pygame.draw.rect(surf, DARK_GRAY, bg, border_radius=4)
    fill = max(0, int(bar_w * value / max_val))
    if fill:
        pygame.draw.rect(surf, color, pygame.Rect(x, y + 20, fill, 10), border_radius=4)
    pygame.draw.rect(surf, GRAY, bg, 1, border_radius=4)


# ══════════════════════════════════════════════════════════════════════════════
# Main Menu
# ══════════════════════════════════════════════════════════════════════════════

class MainMenuScreen:
    def __init__(self, save_manager, daily_reward=0):
        self.save        = save_manager
        self.daily_reward = daily_reward
        self.stars       = _make_stars()
        self.notify_timer = 200 if daily_reward else 0
        self.tick        = 0

        self._f_title = pygame.font.SysFont("monospace", 52, bold=True)
        self._f_sub   = pygame.font.SysFont("monospace", 20)
        self._f_tok   = pygame.font.SysFont("monospace", 20, bold=True)
        self._f_notif = pygame.font.SysFont("monospace", 22, bold=True)

        cx = SCREEN_WIDTH // 2
        self.btn_play  = Button(cx, 310, 230, 52, "PLAY")
        self.btn_lb    = Button(cx, 380, 230, 52, "LEADERBOARD",   PURPLE, (200, 100, 255))
        self.btn_upg   = Button(cx, 450, 230, 52, "UPGRADE SHIPS", ORANGE, YELLOW)
        self.btn_quit  = Button(cx, 520, 230, 52, "QUIT",          GRAY,   (160, 160, 160))

    def handle_event(self, event):
        if self.btn_play.handle_event(event):
            return ("ship_select", None)
        if self.btn_lb.handle_event(event):
            return ("leaderboard", None)
        if self.btn_upg.handle_event(event):
            return ("upgrade", None)
        if self.btn_quit.handle_event(event):
            pygame.quit(); sys.exit()
        return None

    def update(self, dt):
        _scroll_stars(self.stars)
        self.tick += 1
        if self.notify_timer > 0:
            self.notify_timer -= 1

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)

        # animated title color
        pulse = abs(math.sin(self.tick * 0.025)) * 30
        col   = (int(80 + pulse), int(180 + pulse // 2), 255)
        title = self._f_title.render("NEON  RAIDERS", True, col)
        surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 155)))

        sub = self._f_sub.render("Survive. Destroy. Conquer.", True, GRAY)
        surf.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 220)))

        tok = self._f_tok.render(f"Tokens: {self.save.tokens}", True, YELLOW)
        surf.blit(tok, (20, 18))

        self.btn_play.draw(surf)
        self.btn_lb.draw(surf)
        self.btn_upg.draw(surf)
        self.btn_quit.draw(surf)

        # keyboard hint
        hint = self._f_sub.render("ARROWS / WASD = Move     SPACE / W / UP = Shoot", True, DARK_GRAY)
        surf.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 660)))

        if self.notify_timer > 0:
            alpha = min(255, self.notify_timer * 4)
            msg = self._f_notif.render(
                f"+{self.daily_reward} tokens — Daily Login Bonus!", True, NEON_GREEN)
            msg.set_alpha(alpha)
            surf.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 600)))


# ══════════════════════════════════════════════════════════════════════════════
# Ship Select
# ══════════════════════════════════════════════════════════════════════════════

class ShipSelectScreen:
    def __init__(self, save_manager):
        self.save      = save_manager
        self.stars     = _make_stars()
        self.selected  = "falcon"
        self.hover_idx = None
        self.tick      = 0

        self._f_title = pygame.font.SysFont("monospace", 36, bold=True)
        self._f_name  = pygame.font.SysFont("monospace", 22, bold=True)
        self._f_desc  = pygame.font.SysFont("monospace", 15)
        self._f_stat  = pygame.font.SysFont("monospace", 14)
        self._f_keys  = pygame.font.SysFont("monospace", 16)

        cx = SCREEN_WIDTH // 2
        self.btn_play = Button(cx,  640, 230, 50, "LAUNCH!", GREEN, NEON_GREEN)
        self.btn_back = Button(110,  38, 160, 40, "< BACK",  GRAY,  WHITE)

        # card rects centered on screen
        card_w, card_h = 220, 340
        total_w = 3 * card_w + 2 * 20
        sx = (SCREEN_WIDTH - total_w) // 2
        self.cards = [
            pygame.Rect(sx + i * (card_w + 20), 180, card_w, card_h)
            for i in range(3)
        ]

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            return ("main_menu", None)
        if self.btn_play.handle_event(event):
            return ("game", self.selected)

        if event.type == pygame.MOUSEMOTION:
            self.hover_idx = None
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    self.hover_idx = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(self.cards):
                if r.collidepoint(event.pos):
                    self.selected = SHIP_ORDER[i]

        return None

    def update(self, dt):
        _scroll_stars(self.stars)
        self.tick += 1

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)

        title = self._f_title.render("SELECT YOUR SHIP", True, WHITE)
        surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 80)))

        for i, (sid, card) in enumerate(zip(SHIP_ORDER, self.cards)):
            base = SHIPS[sid]
            ups  = self.save.get_upgrades(sid)
            sel  = sid == self.selected
            hov  = self.hover_idx == i

            # card bg
            bg_col = (25, 55, 95) if sel else (22, 28, 45)
            bc_col = base["color"] if sel else (WHITE if hov else GRAY)
            pygame.draw.rect(surf, bg_col, card, border_radius=12)
            pygame.draw.rect(surf, bc_col, card, 2, border_radius=12)

            cx = card.centerx
            # ship preview with subtle bob
            bob = int(math.sin(self.tick * 0.05 + i) * 4)
            draw_ship(surf, sid, cx, card.top + 105 + bob, scale=2.2)

            # name
            name = self._f_name.render(base["name"], True, base["color"])
            surf.blit(name, name.get_rect(center=(cx, card.top + 195)))

            # description
            desc = self._f_desc.render(base["description"], True, GRAY)
            surf.blit(desc, desc.get_rect(center=(cx, card.top + 220)))

            # stat bars
            bx = card.left + 20
            speed_val = base["speed"]  + ups["speed"]  * UPGRADE_SPEED_BOOST
            dmg_val   = base["damage"] + ups["damage"] * UPGRADE_DAMAGE_BOOST
            fr_raw    = base["fire_cooldown"] - ups["fire_rate"] * UPGRADE_FIRE_REDUCTION
            fr_val    = max(FIRE_COOLDOWN_MIN, fr_raw)
            fr_disp   = 60 - fr_val   # higher = faster

            _stat_bar(surf, self._f_stat, bx, card.top + 243, f"SPD {speed_val:.1f}", speed_val, 12.0, CYAN,    bar_w=180)
            _stat_bar(surf, self._f_stat, bx, card.top + 278, f"DMG {dmg_val}",       dmg_val,   16,   RED,     bar_w=180)
            _stat_bar(surf, self._f_stat, bx, card.top + 313, "ATK RATE",             fr_disp,   58,   ORANGE,  bar_w=180)

        self.btn_play.draw(surf)
        self.btn_back.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Game
# ══════════════════════════════════════════════════════════════════════════════

class GameScreen:
    def __init__(self, ship_id, save_manager):
        self.save   = save_manager
        self.player = Player(ship_id, save_manager.get_upgrades(ship_id))
        self.grid   = EnemyGrid()

        self.player_bullets = []
        self.enemy_bullets  = []
        self.explosions     = []

        self.mystery      = None
        self.mystery_timer = MYSTERY_INTERVAL

        spacing = SCREEN_WIDTH // (BUNKER_COUNT + 1)
        self.bunkers = [Bunker(spacing * (i + 1), BUNKER_Y) for i in range(BUNKER_COUNT)]

        self.stars = _make_stars()

        self.time_left_ms = GAME_DURATION * 1000
        self.time_left    = GAME_DURATION
        self.paused       = False
        self.result       = None

        self._popup_timer = 0
        self._popup_text  = ""
        self._popup_x     = 0.0
        self._popup_y     = 0.0
        self._popup_color = YELLOW

        self._f_hud   = pygame.font.SysFont("monospace", 21, bold=True)
        self._f_small = pygame.font.SysFont("monospace", 16)
        self._f_big   = pygame.font.SysFont("monospace", 48, bold=True)
        self._f_popup = pygame.font.SysFont("monospace", 18, bold=True)

        cx = SCREEN_WIDTH // 2
        self.btn_resume = Button(cx, 350, 200, 50, "RESUME")
        self.btn_quit_g = Button(cx, 420, 200, 50, "QUIT", RED, (255, 80, 80))

    # ── events ────────────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.paused = not self.paused

        if self.paused:
            if self.btn_resume.handle_event(event):
                self.paused = False
            if self.btn_quit_g.handle_event(event):
                return ("main_menu", None)

        return None

    # ── update ────────────────────────────────────────────────────────────────

    def update(self, dt):
        if self.paused or self.result:
            return None

        _scroll_stars(self.stars)

        # timer
        self.time_left_ms -= dt
        self.time_left = max(0, int(self.time_left_ms / 1000))
        if self.time_left_ms <= 0 and self.grid.alive_count > 0:
            self.result = "lose_time"

        # player
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, self.player_bullets)
        self.player.update()

        # enemies
        self.grid.update(self.enemy_bullets)
        if self.grid.reached_player_line():
            self.result = "lose_invaded"

        # mystery ship
        self.mystery_timer -= 1
        if self.mystery_timer <= 0:
            self.mystery = MysteryShip()
            self.mystery_timer = MYSTERY_INTERVAL
        if self.mystery:
            self.mystery.update()
            if not self.mystery.alive:
                self.mystery = None

        # update bullets
        for b in self.player_bullets:  b.update()
        for b in self.enemy_bullets:   b.update()
        self.player_bullets = [b for b in self.player_bullets if b.alive]
        self.enemy_bullets  = [b for b in self.enemy_bullets  if b.alive]

        # explosions
        for ex in self.explosions:  ex.update()
        self.explosions = [ex for ex in self.explosions if ex.alive]

        # popup float up
        if self._popup_timer > 0:
            self._popup_timer -= 1
            self._popup_y     -= 0.6

        # ── collisions ────────────────────────────────────────────────────────

        for bullet in self.player_bullets:
            if not bullet.alive:
                continue

            # mystery ship
            if self.mystery and bullet.rect.colliderect(self.mystery.rect):
                self.player.score += self.mystery.points
                self._popup(f"+{self.mystery.points}", self.mystery.x, self.mystery.y, PURPLE)
                self.explosions.append(Explosion(self.mystery.x, self.mystery.y, PURPLE, 30))
                self.mystery = None
                bullet.alive = False
                continue

            # enemies
            hit_enemy = False
            for enemy in self.grid.alive:
                if bullet.rect.colliderect(enemy.rect):
                    enemy.alive = False
                    self.player.score += enemy.points
                    self._popup(f"+{enemy.points}", enemy.x, enemy.y, enemy.color)
                    self.explosions.append(Explosion(enemy.x, enemy.y, enemy.color))
                    bullet.alive = False
                    hit_enemy = True
                    break

            # bunkers (player bullets destroy blocks)
            if bullet.alive:
                for bunker in self.bunkers:
                    if bunker.check_hit(bullet):
                        break

        for bullet in self.enemy_bullets:
            if not bullet.alive:
                continue
            # bunkers first
            blocked = False
            for bunker in self.bunkers:
                if bunker.check_hit(bullet):
                    blocked = True
                    break
            if blocked:
                continue
            # player
            if bullet.rect.colliderect(self.player.rect):
                self.player.hit(self.explosions)
                bullet.alive = False
                if not self.player.alive:
                    self.result = "lose_dead"

        # win
        if self.grid.alive_count == 0:
            self.result = "win"

        if self.result:
            return ("result", {
                "result":  self.result,
                "score":   self.player.score,
                "ship_id": self.player.ship_id,
            })

        return None

    def _popup(self, text, x, y, color=YELLOW):
        self._popup_text  = text
        self._popup_x     = x
        self._popup_y     = float(y)
        self._popup_color = color
        self._popup_timer = 60

    # ── draw ──────────────────────────────────────────────────────────────────

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)

        for bunker in self.bunkers:  bunker.draw(surf)
        self.grid.draw(surf)
        for b in self.player_bullets:  b.draw(surf)
        for b in self.enemy_bullets:   b.draw(surf)
        if self.mystery:               self.mystery.draw(surf)
        for ex in self.explosions:     ex.draw(surf)
        self.player.draw(surf)

        if self._popup_timer > 0:
            alpha = min(255, self._popup_timer * 5)
            ptxt  = self._f_popup.render(self._popup_text, True, self._popup_color)
            ptxt.set_alpha(alpha)
            surf.blit(ptxt, ptxt.get_rect(center=(int(self._popup_x), int(self._popup_y))))

        self._draw_hud(surf)

        if self.paused:
            self._draw_pause(surf)

    def _draw_hud(self, surf):
        pygame.draw.rect(surf, (8, 8, 18), (0, 0, SCREEN_WIDTH, 50))
        pygame.draw.line(surf, GRAY, (0, 50), (SCREEN_WIDTH, 50))

        # score
        sc = self._f_hud.render(f"SCORE  {self.player.score:06d}", True, YELLOW)
        surf.blit(sc, (18, 14))

        # timer
        m, s = divmod(self.time_left, 60)
        t_col = RED if self.time_left <= 30 else WHITE
        tc = self._f_hud.render(f"{m:02d}:{s:02d}", True, t_col)
        surf.blit(tc, tc.get_rect(center=(SCREEN_WIDTH // 2, 25)))

        # lives (ship icons)
        for i in range(self.player.lives):
            lx = SCREEN_WIDTH - 22 - i * 22
            draw_ship(surf, self.player.ship_id, lx, 28, scale=0.55)

        # enemy count
        rem = self._f_small.render(f"ENEMIES: {self.grid.alive_count}", True, RED)
        surf.blit(rem, (SCREEN_WIDTH - 140, 55))

        # ESC hint
        esc = self._f_small.render("ESC=Pause", True, DARK_GRAY)
        surf.blit(esc, (SCREEN_WIDTH // 2 + 80, 60))

    def _draw_pause(self, surf):
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        surf.blit(ov, (0, 0))
        pt = self._f_big.render("PAUSED", True, WHITE)
        surf.blit(pt, pt.get_rect(center=(SCREEN_WIDTH // 2, 280)))
        self.btn_resume.draw(surf)
        self.btn_quit_g.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Result Screen
# ══════════════════════════════════════════════════════════════════════════════

class ResultScreen:
    def __init__(self, result_data, save_manager):
        self.save     = save_manager
        self.result   = result_data["result"]
        self.score    = result_data["score"]
        self.ship_id  = result_data["ship_id"]
        self.is_win   = self.result == "win"
        self.submitted = False
        self.rank_bonus = 0
        self.stars    = _make_stars()
        self.tick     = 0

        self._f_big   = pygame.font.SysFont("monospace", 52, bold=True)
        self._f_med   = pygame.font.SysFont("monospace", 26, bold=True)
        self._f_small = pygame.font.SysFont("monospace", 18)

        cx = SCREEN_WIDTH // 2
        self.name_input = TextInput(cx, 415, 300, 46, placeholder="Your name (max 12)...")
        self.btn_submit = Button(cx, 475, 220, 46, "SUBMIT SCORE", GREEN, NEON_GREEN)
        self.btn_menu = Button(cx, 565, 200, 46, "MAIN MENU", GRAY, WHITE)
        self.btn_play_again = Button(cx, 615, 200, 46, "PLAY AGAIN", BLUE, CYAN)

    def handle_event(self, event):
        if not self.submitted:
            action = self.name_input.handle_event(event)
            if self.btn_submit.handle_event(event) or action == "submit":
                name = self.name_input.text.strip() or "PLAYER"
                self.rank_bonus = self.save.add_score(name, self.score, self.ship_id)
                self.submitted  = True
        if self.btn_menu.handle_event(event):
            return ("main_menu", None)
        if self.btn_play_again.handle_event(event):
            return ("ship_select", None)
        return None

    def update(self, dt):
        _scroll_stars(self.stars)
        self.tick += 1

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)
        cx = SCREEN_WIDTH // 2

        if self.is_win:
            pulse = abs(math.sin(self.tick * 0.04)) * 25
            col   = (int(80 + pulse), 255, int(80 + pulse))
            headline = self._f_big.render("VICTORY!", True, col)
        else:
            headline = self._f_big.render("GAME OVER", True, RED)
        surf.blit(headline, headline.get_rect(center=(cx, 175)))

        reasons = {
            "win":          "All invaders destroyed!",
            "lose_dead":    "Your ship was destroyed.",
            "lose_time":    "Time ran out!",
            "lose_invaded": "The invaders reached Earth!",
        }
        reason_txt = self._f_small.render(reasons.get(self.result, ""), True, GRAY)
        surf.blit(reason_txt, reason_txt.get_rect(center=(cx, 248)))

        score_txt = self._f_med.render(f"SCORE   {self.score:06d}", True, YELLOW)
        surf.blit(score_txt, score_txt.get_rect(center=(cx, 300)))

        if not self.submitted:
            lbl = self._f_small.render("Enter your name for the leaderboard:", True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=(cx, 378)))
            self.name_input.draw(surf)
            self.btn_submit.draw(surf)
        else:
            ok = self._f_small.render("Score submitted!", True, NEON_GREEN)
            surf.blit(ok, ok.get_rect(center=(cx, 468)))
            if self.rank_bonus:
                bon = self._f_small.render(
                    f"+{self.rank_bonus} tokens for your leaderboard rank!", True, YELLOW)
                surf.blit(bon, bon.get_rect(center=(cx, 500)))

        self.btn_menu.draw(surf)
        self.btn_play_again.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Leaderboard
# ══════════════════════════════════════════════════════════════════════════════

class LeaderboardScreen:
    def __init__(self, save_manager):
        self.save  = save_manager
        self.stars = _make_stars()

        self._f_title = pygame.font.SysFont("monospace", 36, bold=True)
        self._f_hdr   = pygame.font.SysFont("monospace", 16)
        self._f_entry = pygame.font.SysFont("monospace", 21)

        self.btn_back = Button(110, 38, 160, 40, "< BACK", GRAY, WHITE)

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            return ("main_menu", None)
        return None

    def update(self, dt):
        _scroll_stars(self.stars)

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)

        title = self._f_title.render("LEADERBOARD", True, YELLOW)
        surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 78)))

        COL = [90, 165, 365, 530]
        hy  = 135
        for hdr, cx in zip(["RANK", "NAME", "SCORE", "SHIP"], COL):
            h = self._f_hdr.render(hdr, True, GRAY)
            surf.blit(h, (cx, hy))
        pygame.draw.line(surf, GRAY, (70, hy + 22), (SCREEN_WIDTH - 70, hy + 22))

        rank_colors = {1: YELLOW, 2: (200, 200, 200), 3: (205, 127, 50)}
        entries = self.save.get_leaderboard()[:12]

        for i, entry in enumerate(entries):
            rank = i + 1
            ey   = hy + 40 + i * 40
            col  = rank_colors.get(rank, WHITE)

            if rank <= 3:
                hl = pygame.Surface((SCREEN_WIDTH - 140, 32), pygame.SRCALPHA)
                hl.fill((40, 40, 70, 120))
                surf.blit(hl, (70, ey - 4))

            ship_data = SHIPS.get(entry.get("ship", ""), {})
            ship_col  = ship_data.get("color", WHITE)
            ship_name = ship_data.get("name", "?")

            for txt, cx in [
                (f"#{rank}",                   COL[0]),
                (entry["name"][:12],           COL[1]),
                (f"{entry['score']:06d}",      COL[2]),
                (ship_name,                    COL[3]),
            ]:
                c   = ship_col if cx == COL[3] else col
                lbl = self._f_entry.render(txt, True, c)
                surf.blit(lbl, (cx, ey))

        if not entries:
            msg = self._f_entry.render("No scores yet — play to get on the board!", True, GRAY)
            surf.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, 300)))

        self.btn_back.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
# Upgrade Screen
# ══════════════════════════════════════════════════════════════════════════════

_STATS = [
    ("speed",     "Speed",      CYAN),
    ("fire_rate", "Fire Rate",  ORANGE),
    ("damage",    "Damage",     RED),
    ("bullets",   "Multi-Shot", NEON_GREEN),
]

class UpgradeScreen:
    def __init__(self, save_manager):
        self.save      = save_manager
        self.stars     = _make_stars()
        self.selected  = "viper"
        self.tick      = 0
        self.message   = ""
        self.msg_timer = 0
        self.msg_color = NEON_GREEN

        self._f_title = pygame.font.SysFont("monospace", 32, bold=True)
        self._f_med   = pygame.font.SysFont("monospace", 19, bold=True)
        self._f_small = pygame.font.SysFont("monospace", 15)
        self._f_tok   = pygame.font.SysFont("monospace", 20, bold=True)

        self.btn_back = Button(110, 38, 160, 40, "< BACK", GRAY, WHITE)

        # ship tab buttons
        self.ship_tabs = [
            Button(200 + i * 200, 108, 160, 40, SHIPS[sid]["name"], DARK_GRAY, (40, 40, 80))
            for i, sid in enumerate(SHIP_ORDER)
        ]

        # upgrade buttons (one per stat)
        self.upg_btns = [
            Button(SCREEN_WIDTH - 80, 0, 130, 36, "UPGRADE", BLUE, CYAN)
            for _ in _STATS
        ]

    def handle_event(self, event):
        if self.btn_back.handle_event(event):
            return ("main_menu", None)

        for i, btn in enumerate(self.ship_tabs):
            if btn.handle_event(event):
                self.selected = SHIP_ORDER[i]

        ups = self.save.get_upgrades(self.selected)
        for i, (stat, label, _) in enumerate(_STATS):
            if self.upg_btns[i].handle_event(event):
                cur = ups[stat]
                if cur >= 11:
                    self._msg(f"{label} is already MAX!", GRAY)
                else:
                    cost = UPGRADE_COSTS[cur + 1]
                    ok, paid, new_lvl, milestone = self.save.upgrade_stat(self.selected, stat)
                    if ok:
                        msg = f"{label} → Lv.{new_lvl}  (-{paid} tokens)"
                        if milestone:
                            msg += f"  +{milestone} MILESTONE BONUS!"
                        self._msg(msg, NEON_GREEN)
                    else:
                        self._msg(f"Need {cost} tokens!", RED)

        return None

    def _msg(self, text, color=NEON_GREEN):
        self.message   = text
        self.msg_timer = 150
        self.msg_color = color

    def update(self, dt):
        _scroll_stars(self.stars)
        self.tick += 1
        if self.msg_timer > 0:
            self.msg_timer -= 1

    def draw(self, surf):
        surf.fill(DIM)
        _draw_stars(surf, self.stars)

        title = self._f_title.render("UPGRADE SHIPS", True, YELLOW)
        surf.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 55)))

        tok = self._f_tok.render(f"Tokens: {self.save.tokens}", True, YELLOW)
        surf.blit(tok, (SCREEN_WIDTH - 210, 18))

        # ship tabs
        for i, (btn, sid) in enumerate(zip(self.ship_tabs, SHIP_ORDER)):
            active = sid == self.selected
            btn.color       = (30, 60, 100)   if active else DARK_GRAY
            btn.hover_color = (40, 80, 130)   if active else (40, 40, 80)
            btn.draw(surf)

        # ship panel
        base   = SHIPS[self.selected]
        ups    = self.save.get_upgrades(self.selected)
        px, py = 70, 148

        # ship preview bob
        bob = int(math.sin(self.tick * 0.06) * 4)
        draw_ship(surf, self.selected, px + 70, py + 65 + bob, scale=1.8)
        ship_lbl = self._f_med.render(base["name"], True, base["color"])
        surf.blit(ship_lbl, (px, py + 130))

        # separator
        pygame.draw.line(surf, GRAY, (px, py + 155), (SCREEN_WIDTH - 60, py + 155))

        STAT_BASE_Y = py + 170
        STAT_GAP    = 105

        for i, (stat, label, color) in enumerate(_STATS):
            sy      = STAT_BASE_Y + i * STAT_GAP
            cur_lvl = ups[stat]

            # label + level
            lbl = self._f_med.render(label, True, color)
            surf.blit(lbl, (px, sy))
            lvl = self._f_med.render(f"Lv. {cur_lvl} / 11", True, WHITE)
            surf.blit(lvl, (px + 220, sy))

            # progress pips (11 pips)
            PIP_W, PIP_H, PIP_GAP = 34, 12, 4
            for pip in range(11):
                px2 = px + pip * (PIP_W + PIP_GAP)
                pr  = pygame.Rect(px2, sy + 30, PIP_W, PIP_H)
                pygame.draw.rect(surf, color if pip < cur_lvl else DARK_GRAY, pr, border_radius=3)
                pygame.draw.rect(surf, GRAY, pr, 1, border_radius=3)

            # next cost / max
            if cur_lvl < 11:
                cost = UPGRADE_COSTS[cur_lvl + 1]
                ct = self._f_small.render(f"Next upgrade: {cost} tokens", True, YELLOW)
                surf.blit(ct, (px, sy + 50))
            else:
                mx = self._f_small.render("MAX LEVEL", True, NEON_GREEN)
                surf.blit(mx, (px, sy + 50))

            # upgrade button — reposition each frame
            btn = self.upg_btns[i]
            btn.rect.centery = sy + 20
            if cur_lvl >= 11:
                btn.color       = DARK_GRAY
                btn.hover_color = DARK_GRAY
                btn.text        = "MAX"
            else:
                btn.color       = BLUE
                btn.hover_color = CYAN
                btn.text        = "UPGRADE"
            btn.draw(surf)

        # bottom message
        if self.msg_timer > 0:
            alpha = min(255, self.msg_timer * 4)
            msg = self._f_med.render(self.message, True, self.msg_color)
            msg.set_alpha(alpha)
            surf.blit(msg, msg.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)))

        self.btn_back.draw(surf)
