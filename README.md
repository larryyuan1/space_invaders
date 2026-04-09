# Neon Raiders

A Space Invaders-style arcade game built with Python and pygame. Pick a ship, destroy waves of alien invaders, climb the leaderboard, and spend tokens upgrading your fleet.

## Features

- 3 playable ships with distinct stats — Viper, Falcon, Titan
- Classic 5×11 enemy grid that speeds up as you thin the ranks
- 3 enemy types worth different points
- Mystery UFO for bonus points
- 4 destructible bunkers
- 5-minute survival rounds
- Token economy: daily login rewards, leaderboard bonuses, upgrade milestones
- Per-ship upgrade system — Speed, Fire Rate, Damage, Multi-Shot (max level 11)
- Persistent leaderboard and upgrade progress saved locally

## Requirements

- Python 3.8+
- pygame

## Installation

```bash
git clone git@github.com:larryyuan1/space_invaders.git
cd space_invaders
pip install pygame
python3 main.py
```

## Controls

| Key | Action |
|-----|--------|
| `← →` / `A D` | Move left / right |
| `Space` / `W` / `↑` | Shoot |
| `ESC` | Pause |

## Ships

| Ship | Speed | Fire Rate | Damage | Size |
|------|-------|-----------|--------|------|
| Viper | Fast | High | Low | Small |
| Falcon | Medium | Medium | Medium | Medium |
| Titan | Slow | Low | High | Large |

## How to Win

Kill all enemies before the 5-minute timer runs out — without letting them reach you or getting shot down.

## Tokens & Upgrades

**Earn tokens by:**
- Daily login (+10)
- Top 3 leaderboard finish (+50 / +30 / +20)
- Reaching upgrade milestones (level 5 = +15, level 11 = +30)

**Spend tokens to upgrade 4 stats per ship (max level 11 each):**

| Levels | Cost per upgrade |
|--------|-----------------|
| 1 – 3 | 5 tokens |
| 4 – 6 | 10 tokens |
| 7 – 9 | 20 tokens |
| 10 – 11 | 40 tokens |

Full max on one stat costs 185 tokens.

## Project Structure

```
main.py          Entry point and game loop
constants.py     All game constants and ship definitions
save_manager.py  Save/load: tokens, upgrades, leaderboard (save_data.json)
entities.py      Player, enemies, bullets, bunkers, mystery ship
screens.py       All screens: menu, ship select, game, result, leaderboard, upgrades
ui.py            Button and TextInput widgets
tests/           Unit tests for save logic and game entities
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```
