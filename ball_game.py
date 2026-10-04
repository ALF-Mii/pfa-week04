"""Chibi climber: 5 stages, exit past the top edge (pygame)."""
import math

import pygame

WIDTH, HEIGHT = 800, 600
FPS = 60

MOVE_SPEED = 400        # px/sec
GRAVITY = 2000.0        # px/sec^2
JUMP_VELOCITY = -800.0  # px/sec (negative = up)
GROUND_Y = HEIGHT - 60
JUMP_HEIGHT = JUMP_VELOCITY ** 2 / (2 * GRAVITY)  # ~160px max rise

# Proportions: oversized head, tiny torso -> small-child look.
HEAD_R = 24
TORSO_W, TORSO_H = 26, 20
LEG_LEN = 22
CHAR_W, CHAR_H = 36, HEAD_R * 2 + TORSO_H + LEG_LEN  # 36 x 90

SPAWN = (WIDTH / 2, GROUND_Y)

SKIN = (255, 210, 170)
SHIRT = (90, 150, 220)
PANTS = (60, 60, 75)
DARK = (40, 35, 35)

# Exit past the top edge: feet above y=0. Every level keeps its
# second-highest platform low enough that only the top one can exit.
EXIT_Y = 0

# 5 hand-tuned climbs. Rules per layout: vertical steps <= ~100px
# (jump reaches 160), horizontal gaps small, top platform near y~95,
# second-highest at y>=170 so it can't trigger the exit by itself.
LEVELS = [
    {"name": "First Steps",
     "platforms": [(60, 450, 200, 24), (330, 350, 200, 24),
                   (560, 250, 180, 24), (330, 170, 180, 24),
                   (90, 90, 180, 24)],
     "blocks": []},
    {"name": "Zigzag",
     "platforms": [(560, 455, 150, 24), (370, 360, 150, 24),
                   (150, 265, 150, 24), (370, 175, 150, 24),
                   (580, 95, 150, 24)],
     "blocks": []},
    {"name": "The Wall",
     "platforms": [(60, 450, 140, 24), (240, 350, 140, 24),
                   (60, 250, 140, 24), (250, 210, 140, 24),
                   (450, 170, 140, 24), (600, 95, 130, 24)],
     "blocks": [(380, 300, 40, 240)]},
    {"name": "Skinny",
     "platforms": [(80, 445, 120, 24), (300, 345, 120, 24),
                   (520, 250, 120, 24), (300, 175, 120, 24),
                   (90, 95, 120, 24)],
     "blocks": [(500, 400, 36, 140)]},
    {"name": "Summit",
     "platforms": [(620, 450, 110, 24), (430, 350, 110, 24),
                   (240, 260, 110, 24), (430, 180, 110, 24),
                   (620, 95, 110, 24)],
     "blocks": []},
]

# Active solid geometry; rebuilt by load_level().
OBSTACLES = []


def load_level(idx):
    """Load LEVELS[idx] into OBSTACLES. Returns spawn (x, y)."""
    global OBSTACLES
    lvl = LEVELS[idx]
    OBSTACLES = ([pygame.Rect(*p) for p in lvl["platforms"]]
                 + [pygame.Rect(*b) for b in lvl["blocks"]])
    return SPAWN


def top_two_platforms(idx):
    """(highest_top, second_highest_top) for exit-margin checks."""
    tops = sorted(p[1] for p in LEVELS[idx]["platforms"])
    return tops[0], tops[1]


def char_rect(x, y):
    """Collision box for feet-anchored position (x, y)."""
    return pygame.Rect(x - CHAR_W / 2, y - CHAR_H, CHAR_W, CHAR_H)


def move_and_collide(x, y, vx, vy, dt):
    """Move the character and resolve against OBSTACLES.

    (x, y) is the feet position. Returns (x, y, vy, on_ground).
    Floor/walls handled by caller.
    """
    x += vx * dt
    r = char_rect(x, y)
    for o in OBSTACLES:
        if r.colliderect(o):
            if vx > 0:
                x = o.left - CHAR_W / 2
            elif vx < 0:
                x = o.right + CHAR_W / 2
            elif x < o.centerx:
                x = o.left - CHAR_W / 2
            else:
                x = o.right + CHAR_W / 2
            r = char_rect(x, y)

    prev_bottom, prev_top = y, y - CHAR_H
    y += vy * dt
    on_ground = False
    r = char_rect(x, y)
    for o in OBSTACLES:
        if r.colliderect(o):
            if vy >= 0 and prev_bottom <= o.top + 8:
                y = o.top
                vy = 0.0
                on_ground = True
            elif vy < 0 and prev_top >= o.bottom - 8:
                y = o.bottom + CHAR_H
                vy = 0.0
            elif x < o.centerx:
                x = o.left - CHAR_W / 2
            else:
                x = o.right + CHAR_W / 2
            r = char_rect(x, y)

    return x, y, vy, on_ground


def jump_apex(x, y_start):
    """Feet height at jump apex from a standstill jump (for tests)."""
    y, vy, top = y_start, JUMP_VELOCITY, y_start
    for _ in range(300):
        vy += GRAVITY / 60
        x, y, vy, _ = move_and_collide(x, y, 0.0, vy, 1 / 60)
        top = min(top, y)
        if vy >= 0:
            break
    return top


def draw_character(screen, x, y, facing, swing):
    """Draw the kid anchored at feet (x, y). swing in [-1, 1] walk cycle."""
    hip_y = y - LEG_LEN
    shoulder_y = hip_y - TORSO_H + 4
    head_cy = shoulder_y - HEAD_R + 4

    # legs + shoes
    for dx in (-7, 7):
        sway = int(math.sin(swing) * 7 * (1 if dx > 0 else -1))
        foot = (x + dx + sway, y - 2)
        pygame.draw.line(screen, PANTS, (x + dx, hip_y), foot, 9)
        pygame.draw.circle(screen, DARK, foot, 5)

    # torso
    pygame.draw.rect(screen, SHIRT,
                     (x - TORSO_W / 2, hip_y - TORSO_H, TORSO_W, TORSO_H),
                     border_radius=6)

    # arms (swing opposite to same-side leg)
    for side in (-1, 1):
        sway = int(math.sin(swing) * 6) * side
        pygame.draw.line(screen, SKIN,
                         (x + side * (TORSO_W / 2 - 2), shoulder_y),
                         (x + side * 20 - sway, shoulder_y + 16), 7)

    # big head
    pygame.draw.circle(screen, SKIN, (int(x), int(head_cy)), HEAD_R)

    # face looks toward movement
    look = 2 * facing
    for ex in (-8, 8):
        pygame.draw.circle(screen, DARK,
                           (int(x + ex + look), int(head_cy - 3)), 4)
    pygame.draw.arc(screen, (150, 70, 70),
                    (x - 10 + look, head_cy + 2, 20, 12),
                    0.4, math.pi - 0.4, 2)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chibi Climber — 5 Stages")
    clock = pygame.time.Clock()
    hud = pygame.font.SysFont(None, 32)
    big = pygame.font.SysFont(None, 72)

    level_idx = 0
    x, y = load_level(0)
    vx = 0.0
    vy = 0.0
    on_ground = True
    phase = 0.0
    amp = 0.0
    facing = 1
    won = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if won:
            if keys[pygame.K_r]:
                level_idx = 0
                x, y = load_level(0)
                vy = 0.0
                won = False
            screen.fill((20, 40, 30))
            msg = big.render("YOU MADE IT!", True, (140, 230, 150))
            sub = hud.render("Climbed all 5 stages - press R to play again",
                             True, (200, 200, 200))
            screen.blit(msg, msg.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20)))
            screen.blit(sub, sub.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 40)))
            pygame.display.flip()
            continue

        vx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx = -MOVE_SPEED
            facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = MOVE_SPEED
            facing = 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]
                or keys[pygame.K_UP]) and on_ground:
            vy = JUMP_VELOCITY
            on_ground = False
        if keys[pygame.K_r]:
            (x, y) = SPAWN
            vy = 0.0

        target = 1.0 if (vx != 0 and on_ground) else 0.0
        amp += (target - amp) * min(1.0, dt * 10)
        phase += abs(vx) * dt * 0.045

        vy += GRAVITY * dt
        x, y, vy, landed = move_and_collide(x, y, vx, vy, dt)
        on_ground = landed

        if y >= GROUND_Y:
            y = GROUND_Y
            vy = 0.0
            on_ground = True

        # exit past the top edge -> next stage
        if y < EXIT_Y:
            level_idx += 1
            if level_idx >= len(LEVELS):
                won = True
            else:
                x, y = load_level(level_idx)
                vy = 0.0
                on_ground = False

        x = max(CHAR_W / 2, min(WIDTH - CHAR_W / 2, x))

        screen.fill((30, 30, 30))
        pygame.draw.line(screen, (100, 100, 100),
                         (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        for o in OBSTACLES:
            pygame.draw.rect(screen, (70, 130, 180), o)
        draw_character(screen, x, y, facing, phase if amp > 0.05 else 0.0)
        lvl = LEVELS[level_idx]
        tag = hud.render("Stage %d/5 - %s" % (level_idx + 1, lvl["name"]),
                         True, (200, 200, 200))
        screen.blit(tag, (12, 10))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
