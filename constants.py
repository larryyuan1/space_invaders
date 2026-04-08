# ── Screen ────────────────────────────────────────────────────────────────────
SCREEN_WIDTH  = 900
SCREEN_HEIGHT = 700
FPS           = 60
TITLE         = "Neon Raiders"

# ── Colors ────────────────────────────────────────────────────────────────────
BLACK     = (0,   0,   0)
WHITE     = (255, 255, 255)
GRAY      = (100, 100, 100)
DARK_GRAY = (30,  30,  40)
DIM       = (10,  10,  20)

GREEN      = (0,   220,  70)
RED        = (220,  50,  50)
BLUE       = (50,  150, 255)
YELLOW     = (255, 220,   0)
CYAN       = (0,   220, 255)
ORANGE     = (255, 140,   0)
PURPLE     = (180,  50, 255)
NEON_GREEN = (57,  255,  20)
NEON_PINK  = (255,  50, 150)

# ── Game ──────────────────────────────────────────────────────────────────────
GAME_DURATION     = 300   # seconds (5 min)
PLAYER_LIVES      = 3
PLAYER_Y          = SCREEN_HEIGHT - 65
FIRE_COOLDOWN_MIN = 5     # frames

# ── Ships ─────────────────────────────────────────────────────────────────────
SHIPS = {
    "viper": {
        "name":         "Viper",
        "color":        (0, 255, 120),
        "speed":        7.0,
        "fire_cooldown": 15,   # frames between shots
        "damage":       1,
        "bullet_count": 1,
        "width":        32,
        "height":       24,
        "description":  "Fast & agile. Low damage.",
    },
    "falcon": {
        "name":         "Falcon",
        "color":        (80, 160, 255),
        "speed":        5.0,
        "fire_cooldown": 25,
        "damage":       2,
        "bullet_count": 1,
        "width":        44,
        "height":       32,
        "description":  "Balanced all-rounder.",
    },
    "titan": {
        "name":         "Titan",
        "color":        (255, 120, 50),
        "speed":        3.0,
        "fire_cooldown": 40,
        "damage":       4,
        "bullet_count": 1,
        "width":        58,
        "height":       42,
        "description":  "Slow & devastating.",
    },
}

SHIP_ORDER = ["viper", "falcon", "titan"]

# ── Upgrades ──────────────────────────────────────────────────────────────────
# index = target level (1-11); index 0 unused
UPGRADE_COSTS = [0, 5, 5, 5, 10, 10, 10, 20, 20, 20, 40, 40]

UPGRADE_SPEED_BOOST      = 0.4    # per level
UPGRADE_FIRE_REDUCTION   = 2      # frames shaved per level
UPGRADE_DAMAGE_BOOST     = 1      # per level
# bullets upgrade level → how many bullets fired
BULLET_COUNT_TABLE = {0: 1, 3: 2, 6: 3, 9: 4, 11: 5}

# ── Token rewards ─────────────────────────────────────────────────────────────
TOKEN_DAILY   = 10
TOKEN_RANK    = {1: 50, 2: 30, 3: 20}
TOKEN_MILESTONE = {5: 15, 11: 30}   # tokens when any single upgrade stat hits these levels

# ── Enemy grid ────────────────────────────────────────────────────────────────
ENEMY_ROWS   = 5
ENEMY_COLS   = 11
ENEMY_START_X = 100   # center-x of first enemy
ENEMY_START_Y = 115   # center-y of first enemy
ENEMY_COL_SPACING = 65
ENEMY_ROW_SPACING = 50
ENEMY_DROP    = 18    # pixels dropped when reversing direction
ENEMY_STEP    = 8     # pixels per horizontal move tick

ENEMY_MOVE_INTERVAL_MAX = 48   # frames between move ticks (full grid)
ENEMY_MOVE_INTERVAL_MIN = 5    # frames between move ticks (last few enemies)
ENEMY_SHOOT_INTERVAL    = 95   # frames between enemy shots (decreases as grid thins)

ENEMY_POINTS = {0: 30, 1: 20, 2: 10}   # type → score

# ── Mystery ship ──────────────────────────────────────────────────────────────
MYSTERY_POINTS   = 150
MYSTERY_INTERVAL = 1800   # frames (~30 sec)

# ── Bunkers ───────────────────────────────────────────────────────────────────
BUNKER_COUNT = 4
BUNKER_Y     = SCREEN_HEIGHT - 148
