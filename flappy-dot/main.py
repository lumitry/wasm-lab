# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///

import asyncio
import math
import random
from dataclasses import dataclass, field

import pygame

# Display tuning.
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 1920
LOGICAL_WIDTH = 480
LOGICAL_HEIGHT = 720
FPS_CAP = 120
MAX_DT = 1.0 / 30.0
WINDOW_TITLE = "Flappy Dot"

# Gameplay tuning.
SCROLL_SPEED = 210.0
PIPE_SPACING = 220.0
PIPE_COUNT = 5
PIPE_WIDTH = 84
PIPE_GAP = 210.0
PIPE_CAP_HEIGHT = 24
PIPE_MARGIN_TOP = 80
PIPE_MARGIN_BOTTOM = 132
PIPE_START_OFFSET = 220

BIRD_START_X = 150.0
BIRD_START_Y = LOGICAL_HEIGHT * 0.45
BIRD_SIZE = 18
BIRD_GRAVITY = 1500.0
BIRD_FLAP_VELOCITY = -460.0
BIRD_MAX_RISE_SPEED = -560.0
BIRD_MAX_FALL_SPEED = 760.0
BIRD_BOB_AMOUNT = 10.0
BIRD_BOB_SPEED = 3.2
BIRD_TRAIL_POINTS = 8
BIRD_COLLISION_SHRINK = 3

GROUND_HEIGHT = 96
GROUND_STRIPE_WIDTH = 48
GROUND_SCROLL_FACTOR = 1.25

BACKGROUND_DOT_COUNT = 10
BACKGROUND_DOT_MIN_SIZE = 10
BACKGROUND_DOT_MAX_SIZE = 34
BACKGROUND_DOT_MIN_SPEED = 0.08
BACKGROUND_DOT_MAX_SPEED = 0.30

FLASH_DURATION = 0.15
RESTART_LOCKOUT = 0.35

# Visual tuning.
SKY_TOP = (99, 196, 255)
SKY_BOTTOM = (220, 244, 255)
SUN_COLOR = (255, 238, 161)
CLOUD_COLOR = (255, 255, 255)
PIPE_COLOR = (57, 179, 110)
PIPE_SHADOW = (28, 112, 69)
PIPE_HIGHLIGHT = (143, 235, 177)
GROUND_COLOR = (214, 191, 96)
GROUND_DIRT = (164, 117, 72)
GROUND_STRIPE = (242, 221, 132)
TEXT_COLOR = (33, 45, 66)
TEXT_SHADOW = (255, 255, 255)
BIRD_COLOR = (255, 190, 59)
BIRD_SHADOW = (219, 113, 32)
BIRD_EYE = (255, 255, 255)
BIRD_PUPIL = (22, 22, 34)
TRAIL_COLOR = (255, 255, 255)
FLASH_COLOR = (255, 255, 255)


@dataclass(slots=True)
class Pipe:
    x: float
    gap_y: float
    scored: bool = False


@dataclass(slots=True)
class BackgroundDot:
    x: float
    y: float
    radius: float
    speed_factor: float
    color: tuple[int, int, int]


@dataclass(slots=True)
class Bird:
    x: float
    y: float
    vy: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def blend(color_a: tuple[int, int, int], color_b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return (
        int(color_a[0] + (color_b[0] - color_a[0]) * t),
        int(color_a[1] + (color_b[1] - color_a[1]) * t),
        int(color_a[2] + (color_b[2] - color_a[2]) * t),
    )


def circle_hits_rect(cx: float, cy: float, radius: float, rect: pygame.Rect) -> bool:
    closest_x = clamp(cx, rect.left, rect.right)
    closest_y = clamp(cy, rect.top, rect.bottom)
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy < radius * radius


def make_background_dot(width: int, height: int, x: float | None = None) -> BackgroundDot:
    playable_height = height - GROUND_HEIGHT - 40
    radius = random.uniform(BACKGROUND_DOT_MIN_SIZE, BACKGROUND_DOT_MAX_SIZE)
    tint = random.uniform(0.0, 1.0)
    return BackgroundDot(
        x=x if x is not None else random.uniform(0, width),
        y=random.uniform(70, playable_height),
        radius=radius,
        speed_factor=random.uniform(BACKGROUND_DOT_MIN_SPEED, BACKGROUND_DOT_MAX_SPEED),
        color=blend(CLOUD_COLOR, SKY_BOTTOM, tint * 0.45),
    )


def make_background_dots(count: int, width: int, height: int) -> list[BackgroundDot]:
    return [make_background_dot(width, height) for _ in range(count)]


class Game:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.play_top = 0
        self.play_bottom = height - GROUND_HEIGHT
        self.time = 0.0
        self.distance = 0.0
        self.best_score = 0
        self.flash_timer = 0.0
        self.restart_timer = 0.0
        self.background_dots = make_background_dots(BACKGROUND_DOT_COUNT, width, height)
        self.base_bird_y = BIRD_START_Y
        self.bird = Bird(BIRD_START_X, BIRD_START_Y)
        self.pipes: list[Pipe] = []
        self.score = 0
        self.state = "ready"
        self.reset(keep_best=True)

    def reset(self, keep_best: bool = True) -> None:
        if not keep_best:
            self.best_score = 0

        self.time = 0.0
        self.distance = 0.0
        self.flash_timer = 0.0
        self.restart_timer = 0.0
        self.score = 0
        self.state = "ready"
        self.base_bird_y = BIRD_START_Y
        self.bird = Bird(BIRD_START_X, BIRD_START_Y)
        self.pipes = []

        first_pipe_x = self.width + PIPE_START_OFFSET
        for index in range(PIPE_COUNT):
            self.pipes.append(self.make_pipe(first_pipe_x + index * PIPE_SPACING))

    def make_pipe(self, x: float) -> Pipe:
        half_gap = PIPE_GAP * 0.5
        gap_min = PIPE_MARGIN_TOP + half_gap
        gap_max = self.play_bottom - PIPE_MARGIN_BOTTOM - half_gap
        return Pipe(x=x, gap_y=random.uniform(gap_min, gap_max))

    def queue_flap(self) -> None:
        if self.state == "crashed":
            if self.restart_timer <= 0.0:
                self.reset(keep_best=True)
            return

        if self.state == "ready":
            self.state = "playing"

        self.bird.vy = max(BIRD_MAX_RISE_SPEED, BIRD_FLAP_VELOCITY)
        self.record_trail(force=True)

    def crash(self) -> None:
        if self.state == "crashed":
            return

        self.state = "crashed"
        self.flash_timer = FLASH_DURATION
        self.restart_timer = RESTART_LOCKOUT
        self.best_score = max(self.best_score, self.score)

    def update(self, dt: float) -> None:
        self.time += dt
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.restart_timer = max(0.0, self.restart_timer - dt)
        self.update_background(dt)

        if self.state == "ready":
            self.bird.y = self.base_bird_y + math.sin(self.time * BIRD_BOB_SPEED) * BIRD_BOB_AMOUNT
            self.bird.vy = 0.0
            self.record_trail()
            return

        if self.state == "playing":
            self.distance += SCROLL_SPEED * dt
            for pipe in self.pipes:
                pipe.x -= SCROLL_SPEED * dt
                if not pipe.scored and pipe.x + PIPE_WIDTH < self.bird.x:
                    pipe.scored = True
                    self.score += 1

            while self.pipes and self.pipes[0].x + PIPE_WIDTH < 0:
                self.pipes.pop(0)

            while len(self.pipes) < PIPE_COUNT:
                next_x = self.width + PIPE_START_OFFSET
                if self.pipes:
                    next_x = self.pipes[-1].x + PIPE_SPACING
                self.pipes.append(self.make_pipe(next_x))

        self.bird.vy = min(self.bird.vy + BIRD_GRAVITY * dt, BIRD_MAX_FALL_SPEED)
        self.bird.y += self.bird.vy * dt
        self.record_trail()

        bird_radius = BIRD_SIZE - BIRD_COLLISION_SHRINK
        if self.bird.y - bird_radius <= self.play_top:
            self.bird.y = self.play_top + bird_radius
            self.crash()

        if self.bird.y + bird_radius >= self.play_bottom:
            self.bird.y = self.play_bottom - bird_radius
            self.crash()

        if self.state == "playing":
            self.check_pipe_collisions(bird_radius)

    def update_background(self, dt: float) -> None:
        for dot in self.background_dots:
            dot.x -= SCROLL_SPEED * dot.speed_factor * dt
            if dot.x + dot.radius < -10:
                replacement = make_background_dot(self.width, self.height, self.width + dot.radius + random.uniform(20, 120))
                dot.x = replacement.x
                dot.y = replacement.y
                dot.radius = replacement.radius
                dot.speed_factor = replacement.speed_factor
                dot.color = replacement.color

    def check_pipe_collisions(self, bird_radius: float) -> None:
        for pipe in self.pipes:
            gap_top = int(pipe.gap_y - PIPE_GAP * 0.5)
            gap_bottom = int(pipe.gap_y + PIPE_GAP * 0.5)
            top_rect = pygame.Rect(int(pipe.x), 0, PIPE_WIDTH, gap_top)
            bottom_rect = pygame.Rect(int(pipe.x), gap_bottom, PIPE_WIDTH, self.play_bottom - gap_bottom)

            if circle_hits_rect(self.bird.x, self.bird.y, bird_radius, top_rect):
                self.crash()
                return

            if circle_hits_rect(self.bird.x, self.bird.y, bird_radius, bottom_rect):
                self.crash()
                return

    def record_trail(self, force: bool = False) -> None:
        current = (self.bird.x, self.bird.y)
        if not self.bird.trail:
            self.bird.trail.append(current)
            return

        last_x, last_y = self.bird.trail[-1]
        if force or abs(last_x - current[0]) + abs(last_y - current[1]) >= 4.0:
            self.bird.trail.append(current)

        if len(self.bird.trail) > BIRD_TRAIL_POINTS:
            self.bird.trail = self.bird.trail[-BIRD_TRAIL_POINTS:]


def draw_background(surface: pygame.Surface, game: Game) -> None:
    surface.fill(SKY_TOP)
    pygame.draw.circle(surface, SUN_COLOR, (game.width - 90, 90), 52)
    pygame.draw.circle(surface, blend(SUN_COLOR, SKY_BOTTOM, 0.35), (game.width - 105, 105), 62, 8)

    for dot in game.background_dots:
        pygame.draw.circle(surface, dot.color, (int(dot.x), int(dot.y)), int(dot.radius))
        pygame.draw.circle(
            surface,
            blend(dot.color, SKY_TOP, 0.55),
            (int(dot.x - dot.radius * 0.35), int(dot.y - dot.radius * 0.2)),
            max(2, int(dot.radius * 0.45)),
        )

    hill_y = game.play_bottom - 48
    pygame.draw.circle(surface, (126, 202, 118), (90, hill_y), 108)
    pygame.draw.circle(surface, (108, 192, 112), (245, hill_y + 18), 132)
    pygame.draw.circle(surface, (126, 202, 118), (430, hill_y), 104)


def draw_pipe(surface: pygame.Surface, pipe: Pipe, play_bottom: int) -> None:
    gap_top = int(pipe.gap_y - PIPE_GAP * 0.5)
    gap_bottom = int(pipe.gap_y + PIPE_GAP * 0.5)
    x = int(pipe.x)

    top_rect = pygame.Rect(x, 0, PIPE_WIDTH, gap_top)
    bottom_rect = pygame.Rect(x, gap_bottom, PIPE_WIDTH, play_bottom - gap_bottom)
    top_cap = pygame.Rect(x - 5, gap_top - PIPE_CAP_HEIGHT, PIPE_WIDTH + 10, PIPE_CAP_HEIGHT)
    bottom_cap = pygame.Rect(x - 5, gap_bottom, PIPE_WIDTH + 10, PIPE_CAP_HEIGHT)

    for rect in (top_rect, bottom_rect, top_cap, bottom_cap):
        pygame.draw.rect(surface, PIPE_COLOR, rect, border_radius=10)
        pygame.draw.rect(surface, PIPE_SHADOW, rect, width=4, border_radius=10)

    highlight_width = max(6, int(PIPE_WIDTH * 0.18))
    for rect in (top_rect, bottom_rect):
        highlight = pygame.Rect(rect.left + 10, rect.top + 6, highlight_width, max(0, rect.height - 12))
        if highlight.height > 0:
            pygame.draw.rect(surface, PIPE_HIGHLIGHT, highlight, border_radius=5)


def draw_ground(surface: pygame.Surface, game: Game) -> None:
    ground_rect = pygame.Rect(0, game.play_bottom, game.width, GROUND_HEIGHT)
    pygame.draw.rect(surface, GROUND_COLOR, ground_rect)
    pygame.draw.rect(surface, GROUND_DIRT, (0, game.play_bottom + 18, game.width, GROUND_HEIGHT - 18))
    pygame.draw.rect(surface, PIPE_HIGHLIGHT, (0, game.play_bottom, game.width, 10))

    offset = int(game.distance * GROUND_SCROLL_FACTOR) % GROUND_STRIPE_WIDTH
    stripe_x = -offset
    while stripe_x < game.width + GROUND_STRIPE_WIDTH:
        pygame.draw.rect(
            surface,
            GROUND_STRIPE,
            (stripe_x, game.play_bottom + 10, GROUND_STRIPE_WIDTH // 2, 22),
        )
        stripe_x += GROUND_STRIPE_WIDTH


def draw_bird(surface: pygame.Surface, game: Game) -> None:
    if game.bird.trail:
        for index, (trail_x, trail_y) in enumerate(game.bird.trail):
            t = (index + 1) / len(game.bird.trail)
            radius = max(2, int(BIRD_SIZE * 0.25 + t * BIRD_SIZE * 0.35))
            color = blend(TRAIL_COLOR, SKY_TOP, t * 0.85)
            pygame.draw.circle(surface, color, (int(trail_x), int(trail_y)), radius)

    body_center = (int(game.bird.x), int(game.bird.y))
    wing_phase = math.sin(game.time * 16.0 if game.state == "playing" else game.time * 5.0)
    wing_offset = int(wing_phase * 4)

    pygame.draw.circle(surface, BIRD_SHADOW, (body_center[0] + 2, body_center[1] + 3), BIRD_SIZE)
    pygame.draw.circle(surface, BIRD_COLOR, body_center, BIRD_SIZE)
    pygame.draw.circle(surface, blend(BIRD_COLOR, (255, 255, 255), 0.45), (body_center[0] - 5, body_center[1] - 5), BIRD_SIZE // 2)
    pygame.draw.ellipse(
        surface,
        BIRD_SHADOW,
        pygame.Rect(body_center[0] - 9, body_center[1] - 2 + wing_offset, 16, 10),
    )
    pygame.draw.circle(surface, BIRD_EYE, (body_center[0] + 5, body_center[1] - 4), 5)
    pygame.draw.circle(surface, BIRD_PUPIL, (body_center[0] + 7, body_center[1] - 4), 2)
    pygame.draw.polygon(
        surface,
        (255, 120, 79),
        [
            (body_center[0] + BIRD_SIZE - 1, body_center[1] - 1),
            (body_center[0] + BIRD_SIZE + 10, body_center[1] + 2),
            (body_center[0] + BIRD_SIZE - 2, body_center[1] + 5),
        ],
    )


def draw_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    position: tuple[int, int],
    center: bool = False,
) -> None:
    shadow = font.render(text, True, TEXT_SHADOW)
    label = font.render(text, True, color)
    rect = label.get_rect(center=position) if center else label.get_rect(topleft=position)
    shadow_rect = rect.move(2, 2)
    surface.blit(shadow, shadow_rect)
    surface.blit(label, rect)


def draw_hud(surface: pygame.Surface, game: Game, fonts: dict[str, pygame.font.Font]) -> None:
    draw_text(surface, fonts["score"], str(game.score), TEXT_COLOR, (game.width // 2, 70), center=True)
    draw_text(surface, fonts["small"], f"best {game.best_score}", TEXT_COLOR, (18, 18))
    draw_text(surface, fonts["tiny"], f"{clockwise_fps_hint()}", TEXT_COLOR, (18, 46))

    if game.state == "ready":
        draw_text(surface, fonts["title"], "FLAPPY DOT", TEXT_COLOR, (game.width // 2, 190), center=True)
        draw_text(surface, fonts["small"], "space / click / tap to flap", TEXT_COLOR, (game.width // 2, 245), center=True)
        # draw_text(surface, fonts["tiny"], "tweak the globals at the top of main.py", TEXT_COLOR, (game.width // 2, 275), center=True)
    elif game.state == "crashed":
        draw_text(surface, fonts["title"], "BONK", TEXT_COLOR, (game.width // 2, 200), center=True)
        draw_text(surface, fonts["small"], "space / click / tap to restart", TEXT_COLOR, (game.width // 2, 250), center=True)
        draw_text(surface, fonts["tiny"], f"score {game.score}   best {game.best_score}", TEXT_COLOR, (game.width // 2, 280), center=True)


def clockwise_fps_hint() -> str:
    return "R restarts instantly"


def draw_scene(
    window: pygame.Surface,
    canvas: pygame.Surface,
    game: Game,
    fonts: dict[str, pygame.font.Font],
) -> None:
    draw_background(canvas, game)

    for pipe in game.pipes:
        draw_pipe(canvas, pipe, game.play_bottom)

    draw_ground(canvas, game)
    draw_bird(canvas, game)
    draw_hud(canvas, game, fonts)

    if game.flash_timer > 0.0:
        overlay = pygame.Surface((game.width, game.height), pygame.SRCALPHA)
        alpha = int(190 * (game.flash_timer / FLASH_DURATION))
        overlay.fill((*FLASH_COLOR, alpha))
        canvas.blit(overlay, (0, 0))

    if window.get_size() == canvas.get_size():
        window.blit(canvas, (0, 0))
        return

    scaled = pygame.transform.scale(canvas, window.get_size())
    window.blit(scaled, (0, 0))


def create_fonts() -> dict[str, pygame.font.Font]:
    return {
        "title": pygame.font.Font(None, 54),
        "score": pygame.font.Font(None, 72),
        "small": pygame.font.Font(None, 32),
        "tiny": pygame.font.Font(None, 24),
    }


def is_flap_input(event: pygame.event.Event) -> bool:
    if event.type == pygame.KEYDOWN:
        return event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w)
    return event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN)


async def main() -> None:
    pygame.init()
    pygame.display.set_caption(WINDOW_TITLE)

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    canvas = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
    clock = pygame.time.Clock()
    fonts = create_fonts()
    game = Game(LOGICAL_WIDTH, LOGICAL_HEIGHT)

    running = True
    while running:
        dt = min(clock.tick(FPS_CAP) / 1000.0, MAX_DT)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                game.reset(keep_best=True)
            elif is_flap_input(event):
                game.queue_flap()

        game.update(dt)
        draw_scene(window, canvas, game, fonts)
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
