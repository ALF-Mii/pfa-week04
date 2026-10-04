"""Chibi climber: 5 stages, exit past the top edge (pygame)."""
import math
import random

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

# Victory: 45s celebration, then the window closes itself.
WIN_DURATION_MS = 45000
CONFETTI_N = 150
CONFETTI_COLORS = [(255, 80, 80), (255, 200, 60), (120, 220, 120),
                   (120, 180, 255), (220, 130, 255), (255, 255, 255)]

# Wall latch + spring: hold into a screen edge mid-air to cling for up
# to 0.5s, then SPACE springs off — mostly upward, shoved away from the
# wall. Into-wall steering is ignored during the shove so the arc always
# leaves the wall. One latch per airtime. Glowing edges = ready.
WALL_W = 10
LATCH_TIME = 0.5
WALL_PUSH_SPEED = 350.0
WALL_PUSH_TIME = 0.22
WALL_READY = (120, 220, 255)
WALL_SPENT = (60, 70, 90)

# 5 hand-tuned climbs. Rules per layout: vertical steps <= ~100px
# (jump reaches 160), horizontal gaps small, top platform near y~95,
# second-highest at y>=170 so it can't trigger the exit by itself.
# 5 stages of grief, laid out as one chained climb. Each stage's base
# sits under the previous stage's exit (fly in at the same x), with:
# top platform near y~95 (only it can exit), second-highest at y>=165,
# vertical steps <=120px (jump reaches 160), and a weave to suit the mood.
# ---------------------------------------------------------------------------
# STAGE GEOMETRY — how to tweak the climb.
#
# Screen: 800x600, ground line y=540 (stage 1 only). Each entry is a tuple:
#     platform: (x, y, w, h) = TOP-LEFT corner, width, thickness
#     block:    (x, y, w, h) = solid wall, jumped around / latched past
# Character: 36 wide, 90 tall. Physics limits to respect:
#     rise per jump .... max 160px, comfy <= 110 (Depression pushes ~120)
#     horizontal reach . ~300px per jump at full run speed
#     top platform ..... top edge near y=90  (only it can exit past y=0)
#     second-highest ... top edge at y>=165 (can't exit by itself)
#     chain rule ....... each base platform sits under the previous
#                        stage's exit, so the fly-through always has
#                        something to catch (see "overlap" test).
# ASCII maps below are 1 char = 10x20px: '#' = platform, 'X' = block.
# ---------------------------------------------------------------------------
LEVELS = [
    # -- Stage 1: Denial ---------------------------------------------------
    # Safe and wide; everything is fine. Route: base -> mid -> top.
    #  80|         ##################
    # 160|                                 ##################
    # 240|                                                        ##################
    # 340|                                 ####################
    # 440|      ####################
    {"name": "Denial",
     "platforms": [(60, 450, 200, 24), (330, 350, 200, 24),
                   (560, 250, 180, 24), (330, 170, 180, 24),
                   (90, 90, 180, 24)],
     "blocks": []},
    # -- Stage 2: Anger ----------------------------------------------------
    # Jagged zigzag; one X tooth juts under the mid jump, hop around it.
    # 100|            ###############
    # 160|                                   ###############
    # 240|                                                          ##############
    # 360|                                   ###############
    # 400|                              XXXX (to y540)
    # 440|        ####################  XXXX
    {"name": "Anger",
     "platforms": [(80, 450, 200, 24), (350, 350, 150, 24),
                   (580, 250, 140, 24), (350, 165, 150, 24),
                   (120, 95, 150, 24)],
     "blocks": [(300, 400, 36, 140)]},
    # -- Stage 3: Bargaining -----------------------------------------------
    # Weave back and forth; the central XXXX doubles as a stepping stone.
    # 100|                                                ###############
    # 180|                         ###############
    # 260|                                                    ###############
    # 320|                                    XXXX (to y450)
    # 380|                        ########### XXXX
    # 440|          ###################
    {"name": "Bargaining",
     "platforms": [(100, 450, 190, 24), (240, 385, 110, 24),
                   (520, 270, 150, 24), (250, 180, 150, 24),
                   (480, 95, 150, 24)],
     "blocks": [(360, 330, 40, 120)]},
    # -- Stage 4: Depression -----------------------------------------------
    # Four lonely platforms, near-limit rises, long falls between.
    # 100|                      #############
    # 200|                                                  #############
    # 320|                    #############
    # 440|                                                ###################
    {"name": "Depression",
     "platforms": [(480, 450, 190, 24), (200, 330, 130, 24),
                   (500, 210, 130, 24), (220, 95, 130, 24)],
     "blocks": []},
    # -- Stage 5: Acceptance -----------------------------------------------
    # Calm even staircase, alternating sides all the way up.
    #  80|                    ###############
    # 160|                                             ################
    # 240|                    ################
    # 340|                                             ################
    # 440|                    #################
    {"name": "Acceptance",
     "platforms": [(200, 450, 170, 24), (450, 350, 160, 24),
                   (200, 250, 160, 24), (450, 170, 160, 24),
                   (200, 90, 150, 24)],
     "blocks": []},
    # -- Stage 6: Victory --------------------------------------------------
    # The dance floor. Fly in from Acceptance, celebrate 45s while the game
    # keeps running underneath, then the window closes. Falling off drops
    # you back to Acceptance (climb back up to restart the 45s).
    # 440|                         ####################
    {"name": "Victory",
     "platforms": [(250, 450, 200, 24)],
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


def has_floor(idx):
    """Only the first stage has a floor; later stages are void below."""
    return idx == 0


def stage_spawn(idx):
    """Safe start point for a stage: the ground, or its lowest platform."""
    if idx == 0:
        return SPAWN
    lowest = max(LEVELS[idx]["platforms"], key=lambda p: p[1])
    return (lowest[0] + lowest[2] / 2, lowest[1])


def enter_from_above(x):
    """Re-entry when falling back a stage: drop in from the top edge."""
    return (max(CHAR_W / 2, min(WIDTH - CHAR_W / 2, x)), 30)


def enter_from_below(x):
    """Re-entry when jumping up a stage: fly in from the bottom edge.

    Caller keeps the rising vy, so momentum carries straight through.
    """
    return (max(CHAR_W / 2, min(WIDTH - CHAR_W / 2, x)), HEIGHT + 30)


def wall_state(x):
    """Which screen-edge wall is touched: -1 (left), +1 (right), 0 (none)."""
    if x <= CHAR_W / 2:
        return -1
    if x >= WIDTH - CHAR_W / 2:
        return 1
    return 0


def try_wall_latch(on_ground, latched, wall_dir, pressing_toward, ready):
    """Start clinging to the wall. One latch per airtime, never grounded."""
    return (not on_ground and not latched and wall_dir != 0
            and pressing_toward and ready)


def apply_push(vx_key, bonus, push_dir):
    """Merge key steering with the wall-spring shove.

    Into-wall steering is dropped during the shove so the arc always
    leaves the wall; with-the-push steering still adds on top.
    """
    if bonus != 0.0 and vx_key * push_dir < 0:
        return bonus
    return vx_key + bonus


def bounce_push(push_t, push_dir, dt):
    """Wall-spring shove: (vx_bonus, new_push_t). Mostly-up arc helper."""
    if push_t > 0:
        return push_dir * WALL_PUSH_SPEED, max(0.0, push_t - dt)
    return 0.0, push_t


def draw_walls(screen, bounce_ready, tick, latched=False):
    """Edge indicators: bright pulsing bars + chevrons when armed."""
    if latched:
        col = (255, 255, 255)
    elif bounce_ready:
        k = 0.5 + 0.5 * math.sin(tick * 0.008)
        col = tuple(min(255, c + int(45 * k)) for c in WALL_READY)
    else:
        col = WALL_SPENT
    pygame.draw.rect(screen, col, (0, 0, WALL_W, HEIGHT))
    pygame.draw.rect(screen, col, (WIDTH - WALL_W, 0, WALL_W, HEIGHT))
    if bounce_ready:
        for cy in range(80, HEIGHT, 120):
            pygame.draw.polygon(screen, col,
                                [(2, cy - 12), (2, cy + 12), (WALL_W + 6, cy)])
            pygame.draw.polygon(screen, col,
                                [(WIDTH - 2, cy - 12), (WIDTH - 2, cy + 12),
                                 (WIDTH - WALL_W - 6, cy)])


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


def spawn_confetti(top=False):
    """One confetti piece. top=True respawns it just above the screen."""
    return {
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(-20, -5) if top else random.uniform(0, HEIGHT),
        "vy": random.uniform(120, 320),
        "sway": random.uniform(30, 90),
        "phase": random.uniform(0, 6.28),
        "t": random.uniform(0, 100),
        "w": random.randint(4, 8),
        "h": random.randint(6, 12),
        "color": random.choice(CONFETTI_COLORS),
    }


def step_confetti(parts, dt):
    """Fall + sway the pieces; recycle fallen ones back to the top."""
    for p in parts:
        p["t"] += dt
        p["y"] += p["vy"] * dt
        p["x"] += math.sin(p["t"] * 3 + p["phase"]) * p["sway"] * dt
        if p["x"] < -20:
            p["x"] = WIDTH + 10
        elif p["x"] > WIDTH + 20:
            p["x"] = -10
        if p["y"] > HEIGHT + 15:
            p.update(spawn_confetti(top=True))
    return parts


def draw_confetti(screen, parts):
    for p in parts:
        pygame.draw.rect(screen, p["color"],
                         (int(p["x"]), int(p["y"]), p["w"], p["h"]))


def win_time_left_ms(start_ms, now_ms, duration_ms=WIN_DURATION_MS):
    """Ms left on the victory screen, floored at 0 (window closes at 0)."""
    return max(0, duration_ms - (now_ms - start_ms))


def stage_bg_color(idx):
    """Background color per grief stage, dark to dawn."""
    return [
        (30, 30, 30),    # Denial: flat grey
        (60, 25, 25),    # Anger: dark red
        (35, 25, 60),    # Bargaining: restless purple
        (12, 15, 30),    # Depression: near-black blue
        (55, 45, 50),    # Acceptance: warm dawn
    ][idx % 5]


def draw_character(screen, x, y, facing, swing, cling=0):
    """Draw the kid anchored at feet (x, y). swing in [-1, 1] walk cycle.

    cling: -1/0/+1, arms reach up toward the latched wall while set.
    """
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

    # arms (swing opposite to same-side leg; reach up while clinging)
    for side in (-1, 1):
        if cling != 0:
            hand = (x + cling * 18 + side * 4, shoulder_y - 22)
        else:
            sway = int(math.sin(swing) * 6) * side
            hand = (x + side * 20 - sway, shoulder_y + 16)
        pygame.draw.line(screen, SKIN,
                         (x + side * (TORSO_W / 2 - 2), shoulder_y),
                         hand, 7)

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
    win_font = pygame.font.SysFont(None, 120)

    level_idx = 0
    x, y = load_level(0)
    x, y = stage_spawn(0)
    vx = 0.0
    vy = 0.0
    on_ground = True
    phase = 0.0
    amp = 0.0
    facing = 1
    push_t = 0.0
    push_dir = 0
    latch_ready = True
    latched = False
    latch_t = 0.0
    latch_dir = 0
    celebrating = False
    win_start = 0
    confetti = []

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        vx = 0.0
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        if left:
            vx = -MOVE_SPEED
            facing = -1
        if right:
            vx = MOVE_SPEED
            facing = 1
        jump_pressed = (keys[pygame.K_SPACE] or keys[pygame.K_w]
                        or keys[pygame.K_UP])
        bonus, push_t = bounce_push(push_t, push_dir, dt)
        vx = apply_push(vx, bonus, push_dir)
        if jump_pressed and on_ground and not latched:
            vy = JUMP_VELOCITY
            on_ground = False
        if keys[pygame.K_r]:
            (x, y) = stage_spawn(level_idx)
            vy = 0.0
            on_ground = True
            latch_ready = True
            latched = False
            push_t = 0.0

        target = 1.0 if (vx != 0 and on_ground) else 0.0
        amp += (target - amp) * min(1.0, dt * 10)
        phase += abs(vx) * dt * 0.045

        if not latched:
            vy += GRAVITY * dt
            x, y, vy, landed = move_and_collide(x, y, vx, vy, dt)
            on_ground = landed

            if has_floor(level_idx) and y >= GROUND_Y:
                y = GROUND_Y
                vy = 0.0
                on_ground = True

        # exit past the top edge -> fly into the next stage from below
        # with position and upward momentum kept; land it yourself.
        # Entering the Victory stage starts the 45s celebration.
        if y < EXIT_Y:
            if level_idx + 1 < len(LEVELS):
                level_idx += 1
                load_level(level_idx)
                (x, y) = enter_from_below(x)
                on_ground = False
                if level_idx == len(LEVELS) - 1:
                    celebrating = True
                    win_start = pygame.time.get_ticks()
                    confetti = [spawn_confetti()
                                for _ in range(CONFETTI_N)]
            else:  # unreachable by physics; bounce back down safely
                y = EXIT_Y + 50
                vy = abs(vy)
            latch_ready = True
            latched = False
            push_t = 0.0

        # no floor past stage 1: fall out the bottom -> previous stage
        # (leaving Victory cancels the celebration timer)
        if level_idx > 0 and y - CHAR_H > HEIGHT:
            level_idx -= 1
            load_level(level_idx)
            (x, y) = enter_from_above(x)
            vy = 0.0
            on_ground = False
            celebrating = False
            latch_ready = True
            latched = False
            push_t = 0.0

        x = max(CHAR_W / 2, min(WIDTH - CHAR_W / 2, x))

        # wall latch: hold into an edge mid-air to cling, SPACE to spring
        # off (mostly up, shoved away). Runs out after LATCH_TIME or let-go.
        touching = wall_state(x)
        pressing = (touching == -1 and left) or (touching == 1 and right)
        if try_wall_latch(on_ground, latched, touching, pressing,
                          latch_ready):
            latched, latch_t, latch_dir = True, LATCH_TIME, touching
            vy = 0.0
            facing = touching
        if latched:
            latch_t -= dt
            vy = 0.0
            if jump_pressed:
                vy = JUMP_VELOCITY
                push_dir = -latch_dir
                push_t = WALL_PUSH_TIME
                latched = False
                latch_ready = False
                facing = -latch_dir
            elif latch_t <= 0 or not pressing:
                latched = False
                latch_ready = False
        if on_ground:
            latch_ready = True
            latched = False
            push_t = 0.0

        screen.fill(stage_bg_color(level_idx))
        draw_walls(screen, latch_ready, pygame.time.get_ticks(), latched)
        if has_floor(level_idx):
            pygame.draw.line(screen, (100, 100, 100),
                             (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        for o in OBSTACLES:
            pygame.draw.rect(screen, (70, 130, 180), o)
        draw_character(screen, x, y, facing, phase if amp > 0.05 else 0.0,
                       latch_dir if latched else 0)
        lvl = LEVELS[level_idx]
        tag = hud.render("Stage %d/%d - %s"
                         % (level_idx + 1, len(LEVELS), lvl["name"]),
                         True, (200, 200, 200))
        screen.blit(tag, (12, 10))
        bounce_hint = hud.render("Hold into a wall to latch - SPACE springs off",
                                 True, (140, 210, 240))
        screen.blit(bounce_hint, (12, 40))
        if not has_floor(level_idx):
            hint = hud.render("No floor - falling drops a stage!",
                              True, (230, 170, 120))
            screen.blit(hint, (12, 70))
        if celebrating:
            now = pygame.time.get_ticks()
            if win_time_left_ms(win_start, now) <= 0:
                running = False
            step_confetti(confetti, dt)
            draw_confetti(screen, confetti)
            if (now // 400) % 2 == 0:  # flashing red, ~1.25 Hz
                msg = win_font.render("VICTORY", True, (255, 45, 45))
                screen.blit(msg,
                            msg.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 20)))
            left_s = win_time_left_ms(win_start, now) // 1000
            timer = hud.render("Closing in %ds..." % left_s, True,
                               (235, 235, 235))
            screen.blit(timer, timer.get_rect(center=(WIDTH / 2,
                                                       HEIGHT / 2 + 60)))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
