# Chibi Climber — 5 stages of grief

A pygame platformer about climbing through Denial, Anger, Bargaining,
Depression and Acceptance. Jump out past the top edge to rise to the next
stage; fall out the bottom and you drop back a stage. No floor past stage 1.

## How to run it

```bash
git clone <your-repo-url>
cd <repo-folder>
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate
pip install pygame
python ball_game.py
```

## What I made better (since class)

- Chibi climber: big head, tiny torso, arms/legs with a walk cycle (was a plain ball).
- 5 themed stages (Denial → Acceptance) with chained fly-through transitions.
- No floor past stage 1: falling out the bottom drops you a stage; R safely restarts.
- Wall latch (0.5s cling) + spring jump with glowing edge indicators.
- Victory screen: flashing red VICTORY, 150-piece confetti, auto-closes after 45s.
- Stage backgrounds shift per stage (my own def, below).
- Stage layouts documented as ASCII maps with a tuning guide; physics covered by tests.

## How it works (three defs)

- `move_and_collide(x, y, vx, vy, dt)` — moves the character's feet-anchored
  hitbox one axis at a time and resolves platform hits: land on top when
  falling, bonk when rising, shove sideways otherwise.
- `try_wall_latch(on_ground, latched, wall_dir, pressing_toward, ready)` —
  decides whether leaning into an edge wall mid-air starts a 0.5s cling
  (one latch per airtime, never on the ground).
- `stage_bg_color(idx)` — takes the stage number and returns that stage's
  background color, dark grey through to a warm dawn. Hand-written by me:
  I picked every RGB value and wired it into `main` via
  `screen.fill(stage_bg_color(level_idx))`.

  ## Recording
  https://drive.google.com/file/d/1NW3cdOSg6hFG_35Mmldz6XKkeuK-Lvw5/view?usp=sharing
