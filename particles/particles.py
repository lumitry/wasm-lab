import asyncio
import math
import random
from dataclasses import dataclass

import pygame

WIDTH = 1280
HEIGHT = 720
BACKGROUND = (10, 12, 20)
TEXT = (235, 240, 255)

PARTICLE_COUNT = 5000
PARTICLE_RADIUS = 4
MAX_START_SPEED = 240
FPS = 120


@dataclass(slots=True)
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    radius: float
    color: tuple[int, int, int]


def random_color() -> tuple[int, int, int]:
    palette = (
        (255, 110, 110),
        (255, 186, 73),
        (255, 235, 120),
        (120, 230, 180),
        (110, 190, 255),
        (185, 130, 255),
    )
    return random.choice(palette)


def make_particles(count: int, width: int, height: int) -> list[Particle]:
    particles: list[Particle] = []
    cols = max(1, int(math.sqrt(count * width / height)))
    rows = max(1, math.ceil(count / cols))
    spacing_x = width / (cols + 1)
    spacing_y = height / (rows + 1)

    for index in range(count):
        col = index % cols
        row = index // cols

        x = (col + 1) * spacing_x + random.uniform(-1.5, 1.5) * PARTICLE_RADIUS
        y = (row + 1) * spacing_y + random.uniform(-1.5, 1.5) * PARTICLE_RADIUS

        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, MAX_START_SPEED)
        particles.append(
            Particle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                radius=PARTICLE_RADIUS,
                color=random_color(),
            )
        )

    return particles


def bounce_off_walls(particle: Particle, width: int, height: int) -> None:
    if particle.x - particle.radius < 0:
        particle.x = particle.radius
        particle.vx *= -1
    elif particle.x + particle.radius > width:
        particle.x = width - particle.radius
        particle.vx *= -1

    if particle.y - particle.radius < 0:
        particle.y = particle.radius
        particle.vy *= -1
    elif particle.y + particle.radius > height:
        particle.y = height - particle.radius
        particle.vy *= -1


def resolve_particle_collision(a: Particle, b: Particle) -> None:
    dx = b.x - a.x
    dy = b.y - a.y
    min_dist = a.radius + b.radius
    dist_sq = dx * dx + dy * dy

    if dist_sq == 0:
        angle = random.uniform(0, math.tau)
        dx = math.cos(angle) * 0.01
        dy = math.sin(angle) * 0.01
        dist_sq = dx * dx + dy * dy

    if dist_sq >= min_dist * min_dist:
        return

    dist = math.sqrt(dist_sq)
    nx = dx / dist
    ny = dy / dist

    overlap = min_dist - dist
    correction = overlap * 0.5
    a.x -= nx * correction
    a.y -= ny * correction
    b.x += nx * correction
    b.y += ny * correction

    rel_vx = a.vx - b.vx
    rel_vy = a.vy - b.vy
    approach_speed = rel_vx * nx + rel_vy * ny

    # Only resolve the velocity if the particles are moving into each other.
    if approach_speed > 0:
        a.vx -= approach_speed * nx
        a.vy -= approach_speed * ny
        b.vx += approach_speed * nx
        b.vy += approach_speed * ny


def update_particles(
    particles: list[Particle], dt: float, width: int, height: int
) -> None:
    cell_size = PARTICLE_RADIUS * 2
    grid: dict[tuple[int, int], list[int]] = {}

    for index, particle in enumerate(particles):
        particle.x += particle.vx * dt
        particle.y += particle.vy * dt
        bounce_off_walls(particle, width, height)

        cell = (int(particle.x // cell_size), int(particle.y // cell_size))
        grid.setdefault(cell, []).append(index)

    for index, particle in enumerate(particles):
        base_cell_x = int(particle.x // cell_size)
        base_cell_y = int(particle.y // cell_size)

        for offset_x in (-1, 0, 1):
            for offset_y in (-1, 0, 1):
                neighbor_cell = (base_cell_x + offset_x, base_cell_y + offset_y)
                for other_index in grid.get(neighbor_cell, ()):
                    if other_index <= index:
                        continue
                    resolve_particle_collision(particle, particles[other_index])


def draw_particles(screen: pygame.Surface, particles: list[Particle]) -> None:
    for particle in particles:
        pygame.draw.circle(
            screen,
            particle.color,
            (int(particle.x), int(particle.y)),
            int(particle.radius),
        )


def stir_particles(
    particles: list[Particle], mouse_pos: tuple[int, int], strength: float = 480
) -> None:
    mx, my = mouse_pos
    for particle in particles:
        dx = particle.x - mx
        dy = particle.y - my
        dist_sq = dx * dx + dy * dy
        if 1 < dist_sq < 140 * 140:
            dist = math.sqrt(dist_sq)
            push = strength / dist
            particle.vx += (dx / dist) * push
            particle.vy += (dy / dist) * push


async def main() -> None:
    pygame.init()
    pygame.display.set_caption("Bouncy Particle Collisions")

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    particles = make_particles(PARTICLE_COUNT, WIDTH, HEIGHT)

    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.033)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    width, height = screen.get_size()
                    particles = make_particles(PARTICLE_COUNT, width, height)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                stir_particles(particles, event.pos, strength=720)

        if pygame.mouse.get_pressed()[0]:
            stir_particles(particles, pygame.mouse.get_pos(), strength=28)

        width, height = screen.get_size()
        update_particles(particles, dt, width, height)

        screen.fill(BACKGROUND)
        draw_particles(screen, particles)

        label = font.render(
            (
                f"{len(particles)} particles  |  "
                f"FPS: {clock.get_fps():5.1f}  |  "
                "click/drag to stir  |  R to reset"
            ),
            True,
            TEXT,
        )
        screen.blit(label, (16, 16))

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())