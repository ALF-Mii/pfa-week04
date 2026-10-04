"""Movable ball with jump (pygame)."""
import pygame

WIDTH, HEIGHT = 800, 600
FPS = 60

BALL_RADIUS = 25
MOVE_SPEED = 400        # px/sec
GRAVITY = 2000.0        # px/sec^2
JUMP_VELOCITY = -800.0  # px/sec (negative = up)
GROUND_Y = HEIGHT - 60  # ball center rest height = GROUND_Y - RADIUS


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Ball Move + Jump")
    clock = pygame.time.Clock()

    x = WIDTH / 2
    y = GROUND_Y - BALL_RADIUS
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

        vy += GRAVITY * dt
        x += vx * dt
        y += vy * dt

        # floor collision
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
        pygame.draw.circle(screen, (220, 80, 60),
                           (int(x), int(y)), BALL_RADIUS)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
