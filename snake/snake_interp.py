import pygame
import math
import random

pygame.init()

INITIAL_REFRESH_RATE = 1 / 10

grid_dim = (60, 60)
gss = 20

screen_dim = (grid_dim[0] * gss, grid_dim[1] * gss)
screen = pygame.display.set_mode(screen_dim)
pygame.display.set_caption("Snake tail")
clock = pygame.time.Clock()
running = True
dt = 0


class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other: "Vector"):
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector"):
        return Vector(self.x - other.x, self.y - other.y)

    def __eq__(self, other: "Vector"):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"Vector({self.x}, {self.y})"

    @property
    def data(self):
        return [self.x, self.y]

    def to_screen(self):
        return Vector(self.x, -self.y)

    def rotate_image(self, image: pygame.Surface):
        angle = math.degrees(math.atan2(self.y, self.x)) - 90
        return pygame.transform.rotate(image, angle)


def coord_in_array(coord: Vector):
    return coord.x + coord.y * grid_dim[1]


def new_snake():
    head = [grid_dim[0] // 2, grid_dim[1] // 2]
    return [Vector(head[0], head[1] + i) for i in range(5)]


def new_rat():
    return Vector(
        random.randint(0, grid_dim[0] - 1), random.randint(0, grid_dim[1] - 1)
    )


def load_image(file_name):
    image = pygame.image.load(file_name)
    image.convert_alpha()
    return pygame.transform.scale(image, (gss, gss))


def get_corner_screen_rotation_angle(prev: Vector, next: Vector):
    prev = prev.to_screen()
    next = next.to_screen()

    if (prev == Vector(1, 0) and next == Vector(0, -1)) or (
        prev == Vector(0, -1) and next == Vector(1, 0)
    ):
        return 90  # right → up
    if (prev == Vector(0, -1) and next == Vector(-1, 0)) or (
        prev == Vector(-1, 0) and next == Vector(0, -1)
    ):
        return 180  # up → left
    if (prev == Vector(-1, 0) and next == Vector(0, 1)) or (
        prev == Vector(0, 1) and next == Vector(-1, 0)
    ):
        return 270  # left → down
    else:
        return 0  # down → right


snake_head_img = load_image("assets/snake_head.png")
snake_body_img = load_image("assets/snake_body.png")
snake_angl_img = load_image("assets/snake_corner.png")
snake_tail_img = load_image("assets/snake_tail.png")
rat_img = load_image("assets/rat.png")

snake_position_list = new_snake()
snake_length = len(snake_position_list)
direction = Vector(0, -1)

refresh_rate = INITIAL_REFRESH_RATE
refresh = 0
print_t = 0

# For smooth animation: track previous positions for interpolation
previous_snake_positions = snake_position_list.copy()

font = pygame.font.SysFont("Arial", 25)

rat_position = new_rat()

rats = 0

game_over = False
game_start = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if game_start:
        screen.fill(pygame.Color(150, 220, 180))
        text = font.render(
            f"Press any arrow key to start the game!",
            True,
            "black",
        )
        screen.blit(text, (screen_dim[0] / 4, screen_dim[1] / 2))
        pygame.display.flip()

        keys = pygame.key.get_pressed()
        if (
            keys[pygame.K_UP]
            or keys[pygame.K_DOWN]
            or keys[pygame.K_LEFT]
            or keys[pygame.K_RIGHT]
        ):
            game_start = False
            # Initialize previous positions when game starts
            previous_snake_positions = snake_position_list.copy()

        continue

    if game_over:
        screen.fill(pygame.Color(220, 100, 100))
        text = font.render(
            f"YOU LOSE! Rats win! Total Score: {rats}",
            True,
            "black",
        )
        screen.blit(text, (screen_dim[0] / 8, screen_dim[1] / 8))
        text = font.render(f" Press 'Return' to try again.", True, "black")
        screen.blit(text, (screen_dim[0] / 8, screen_dim[1] / 6))
        pygame.display.flip()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            game_over = False
            rats = 0
            snake_position_list = new_snake()
            snake_length = len(snake_position_list)
            direction = Vector(0, -1)
            refresh_rate = INITIAL_REFRESH_RATE
            previous_snake_positions = snake_position_list.copy()

        continue

    screen.fill(pygame.Color(150, 220, 180))

    # Calculate interpolation progress (0.0 to 1.0) for smooth animation
    interpolation_progress = refresh / refresh_rate if refresh_rate > 0 else 0.0
    interpolation_progress = min(1.0, max(0.0, interpolation_progress))

    # draw the snake with interpolated positions
    for i, segment in enumerate(snake_position_list):
        # Get previous and current grid positions
        prev_pos = previous_snake_positions[i] if i < len(previous_snake_positions) else segment
        curr_pos = segment

        # Interpolate between previous and current grid positions
        interp_x = prev_pos.x + (curr_pos.x - prev_pos.x) * interpolation_progress
        interp_y = prev_pos.y + (curr_pos.y - prev_pos.y) * interpolation_progress

        # Convert to screen coordinates
        screen_x = interp_x * gss
        screen_y = interp_y * gss
        snake_segment_rect = pygame.Rect(screen_x, screen_y, gss, gss)

        if i == 0:  # This is the head
            screen.blit(
                direction.to_screen().rotate_image(snake_head_img), snake_segment_rect
            )
        elif i < len(snake_position_list) - 1:  # in the body
            # Use grid positions to determine corner state (stable during interpolation)
            # Calculate direction vectors: from previous to current, and from current to next
            prev_grid = segment - snake_position_list[i - 1]  # direction coming FROM previous
            next_grid = snake_position_list[i + 1] - segment  # direction going TO next

            # Convert to screen space for rendering direction
            prev_screen = prev_grid.to_screen()

            if prev_grid.x == next_grid.x or prev_grid.y == next_grid.y:  # straight segment
                screen.blit(prev_screen.rotate_image(snake_body_img), snake_segment_rect)
            else:  # corner piece
                angle = get_corner_screen_rotation_angle(prev_grid, next_grid)
                screen.blit(
                    pygame.transform.rotate(snake_angl_img, angle), snake_segment_rect
                )
        else:  # this is the tail
            # Use grid position for direction calculation
            delta = (snake_position_list[i - 1] - segment).to_screen()
            screen.blit(delta.rotate_image(snake_tail_img), snake_segment_rect)

    # drawing rat
    screen.blit(
        rat_img, pygame.Rect(rat_position.x * gss, rat_position.y * gss, gss, gss)
    )

    keys = pygame.key.get_pressed()
    new_direction = direction
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        new_direction = Vector(0, -1)
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        new_direction = Vector(0, 1)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        new_direction = Vector(-1, 0)
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        new_direction = Vector(1, 0)

    # don't allow moving back into self.
    if snake_position_list[0] + new_direction != snake_position_list[1]:
        direction = new_direction

    # Got the apple!
    if snake_position_list[0] == rat_position:
        rat_position = new_rat()
        snake_length += 3
        rats += 1
        refresh_rate /= 1.1

    # Show the snake updates at an interval independent of FPS
    if refresh >= refresh_rate:
        refresh = 0
        # Save current positions as previous for interpolation
        previous_snake_positions = snake_position_list.copy()
        snake_position_list.insert(0, snake_position_list[0] + direction)
        if len(snake_position_list) >= snake_length:
            snake_position_list.pop()

    # Game over situations
    for segment in snake_position_list:
        if (
            # ate yourself
            snake_position_list[0] + direction == segment
            # out of bounds
            or snake_position_list[0].x < 0
            or snake_position_list[0].x >= grid_dim[0]
            or snake_position_list[0].y < 0
            or snake_position_list[0].y >= grid_dim[1]
        ):
            game_over = True

    pygame.display.flip()

    dt = clock.tick(60) / 1000
    refresh += dt
    print_t += dt
