"""Movable ball with jump + obstacles (pygame)."""
import pygame

WIDTH, HEIGHT = 800, 600
FPS = 60

BALL_RADIUS = 25
MOVE_SPEED = 400        # px/sec
GRAVITY = 2000.0        # px/sec^2
JUMP_VELOCITY = -800.0  # px/sec (negative = up)
GROUND_Y = HEIGHT - 60

SPAWN = (WIDTH / 2, GROUND_Y - BALL_RADIUS)

# Solid platforms / blocks (x, y, w, h). Ball lands on top, bonks
# underneath, and is blocked from the sides.
OBSTACLES = [
    pygame.Rect(120, 440, 140, 24),
    pygame.Rect(340, 350, 140, 24),
    pygame.Rect(560, 440, 140, 24),
    pygame.Rect(340, 180, 140, 24),
    pygame.Rect(620, 250, 40, 170),  # tall block
]


def circle_rect_overlap(cx, cy, r, rect):
    nx = max(rect.left, min(cx, rect.right))
    ny = max(rect.top, min(cy, rect.bottom))
    dx, dy = cx - nx, cy - ny
    return dx * dx + dy * dy < r * r


def move_and_collide(x, y, vx, vy, dt):
    """Move the ball and resolve against OBSTACLES.

    Returns (x, y, vy, on_ground). Floor/walls handled by caller.
    """
    r = BALL_RADIUS

    # X axis first so walls feel solid while airborne.
    x += vx * dt
    for o in OBSTACLES:
        if circle_rect_overlap(x, y, r, o):
            if vx > 0:
                x = o.left - r
            elif vx < 0:
                x = o.right + r
            elif x < o.centerx:
                x = o.left - r
            else:
                x = o.right + r

    # Y axis: land on top when falling, bonk when rising.
    prev_bottom = y + r
    y += vy * dt
    on_ground = False
    for o in OBSTACLES:
        if circle_rect_overlap(x, y, r, o):
            if vy >= 0 and prev_bottom <= o.top + 8:
                y = o.top - r
                vy = 0.0
                on_ground = True
            elif vy < 0:
                y = o.bottom + r
                vy = 0.0
            elif x < o.centerx:
                x = o.left - r
            else:
                x = o.right + r

    return x, y, vy, on_ground


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ball Move + Jump")
    clock = pygame.time.Clock()

    x, y = SPAWN
    vx = 0.0
    vy = 0.0
    on_ground = True

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        vx = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            vx = -MOVE_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            vx = MOVE_SPEED
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]
                or keys[pygame.K_UP]) and on_ground:
            vy = JUMP_VELOCITY
            on_ground = False
        if keys[pygame.K_r]:
            (x, y) = SPAWN
            vy = 0.0

        vy += GRAVITY * dt
        x, y, vy, landed = move_and_collide(x, y, vx, vy, dt)
        on_ground = landed

        # floor
        floor = GROUND_Y - BALL_RADIUS
        if y >= floor:
            y = floor
            vy = 0.0
            on_ground = True

        # walls
        x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, x))

        screen.fill((30, 30, 30))
        pygame.draw.line(screen, (100, 100, 100),
                         (0, GROUND_Y), (WIDTH, GROUND_Y), 3)
        for o in OBSTACLES:
            pygame.draw.rect(screen, (70, 130, 180), o)
        pygame.draw.circle(screen, (220, 80, 60),
                           (int(x), int(y)), BALL_RADIUS)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
