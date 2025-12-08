import math
import pygame
import pymunk
import pymunk.pygame_util

FPS = 60.0

GRAVITY = (0, -6.81)  # meters / s^2 (world uses -9.81 m/s^2)

# ---------- Screen / Scale ----------
PIX_PER_METER = 30.0  # how many pixels equal 1 meter
SCREEN_W = 2048  # ~34m
SCREEN_H = 1200  # ~20m

# ---------- Truck Setup ----------
TRUCK_LENGTH = 4.7  # meters
TRUCK_HEIGHT = 2.0  # meters
TRUCK_SIZE = (TRUCK_LENGTH, TRUCK_HEIGHT)
TRUCK_MASS = 1500  # kg (rough mass for a big truck)
TRUCK_FRICTION = 0.32
TRUCK_TOP_SPEED = 26.0
TRUCK_ACCEL_RATE = TRUCK_TOP_SPEED / 2.5
TRUCK_DECEL_RATE = TRUCK_TOP_SPEED / 10
TRUCK_BRAKE_RATE = TRUCK_TOP_SPEED / 1.5

# ---------- Wheel Setup ----------
WHEEL_RADIUS = 0.9  # meters (radius)
WHEEL_REAR_OFFSET = (-TRUCK_LENGTH / 3.0, -TRUCK_HEIGHT / 1.4)
WHEEL_FRONT_OFFSET = (TRUCK_LENGTH / 3.0, -TRUCK_HEIGHT / 1.4)
WHEEL_MASS = 500.0  # kg per wheel (rough)
WHEEL_FRICTION = 0.72
MAX_WHEEL_SPEED = TRUCK_TOP_SPEED
WHEEL_TORQUE = 90000

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()


def to_screen_coords(pos, screen_h, pix_per_meter):
    """Converts a Pymunk (x, y) position to a Pygame (x_px, y_px) position."""
    x_px = int(pos.x * pix_per_meter)
    # Apply the flip and offset
    y_px = int(screen_h - (pos.y * pix_per_meter))
    return x_px, y_px


class MotorController:
    def __init__(self, motor):
        self.motor = motor
        self.current_rate = 0.0
        self.target_rate = 0.0

    def update_target(self, input_direction: int):
        """Sets the target rate based on input (1=Right/Forward, -1=Left/Reverse, 0=None)."""
        if input_direction == 1:
            self.target_rate = (
                -TRUCK_TOP_SPEED
            )  # Assuming Right is Forward/CW (negative rate)
        elif input_direction == -1:
            self.target_rate = (
                TRUCK_TOP_SPEED  # Assuming Left is Reverse/CCW (positive rate)
            )
        else:
            self.target_rate = 0.0

    def step(self, dt, is_braking: bool):
        """Smoothly moves the motor rate towards the target rate, respecting braking."""

        # If the spacebar is held, the target rate is ZERO, regardless of other input
        if is_braking:
            self.target_rate = 0.0

        delta = self.target_rate - self.current_rate

        if abs(delta) < 1e-6:
            self.current_rate = self.target_rate
            return

        # Determine the rate based on the action required:
        if is_braking:
            # 🚨 Case 1: Active Spacebar Braking
            # Highest rate to stop quickly
            rate = TRUCK_BRAKE_RATE

        elif self.current_rate * self.target_rate < 0:
            # 🛑 Case 2: Active Reversing/Hard Braking (Switching direction via arrow keys)
            rate = TRUCK_BRAKE_RATE

        elif self.target_rate == 0.0 and abs(self.current_rate) > 0:
            # 💨 Case 3: Coasting (No arrow key input, moving towards 0)
            rate = TRUCK_DECEL_RATE

        else:
            # 🚀 Case 4: Acceleration/Holding Speed
            rate = TRUCK_ACCEL_RATE

        # Apply the step change
        step_change = rate * dt

        if delta > 0:
            self.current_rate += min(delta, step_change)
        else:
            self.current_rate += max(delta, -step_change)

        self.motor.rate = self.current_rate


def make_truck(space: pymunk.Space, position: tuple[float, float]):
    filter_group = 100

    wheel_moment = pymunk.moment_for_circle(WHEEL_MASS, 0, WHEEL_RADIUS)

    wheel_r_b = pymunk.Body(WHEEL_MASS, wheel_moment)
    wheel_r_s = pymunk.Circle(wheel_r_b, WHEEL_RADIUS)
    wheel_r_s.friction = WHEEL_FRICTION
    wheel_r_s.filter = pymunk.ShapeFilter(group=filter_group)
    space.add(wheel_r_b, wheel_r_s)

    wheel_f_b = pymunk.Body(WHEEL_MASS, wheel_moment)
    wheel_f_s = pymunk.Circle(wheel_f_b, WHEEL_RADIUS)
    wheel_f_s.friction = WHEEL_FRICTION
    wheel_f_s.filter = pymunk.ShapeFilter(group=filter_group)
    space.add(wheel_f_b, wheel_f_s)

    truck_moment = pymunk.moment_for_box(TRUCK_MASS, TRUCK_SIZE)

    chassis_b = pymunk.Body(TRUCK_MASS, truck_moment)
    chassis_s = pymunk.Poly.create_box(chassis_b, TRUCK_SIZE)
    chassis_s.friction = TRUCK_FRICTION
    chassis_s.filter = pymunk.ShapeFilter(group=filter_group)
    space.add(chassis_b, chassis_s)

    wheel_r_b.position = position + pymunk.Vec2d(*WHEEL_REAR_OFFSET)
    wheel_f_b.position = position + pymunk.Vec2d(*WHEEL_FRONT_OFFSET)
    chassis_b.position = pymunk.Vec2d(*position)

    space.add(
        pymunk.PivotJoint(wheel_r_b, chassis_b, wheel_r_b.position),
        pymunk.PivotJoint(wheel_f_b, chassis_b, wheel_f_b.position),
    )

    # Create the SimpleMotor for the rear wheel
    motor_r = pymunk.SimpleMotor(wheel_r_b, chassis_b, 0.0)
    motor_r.max_force = WHEEL_TORQUE
    space.add(motor_r)

    # Create the SimpleMotor for the front wheel (if 4x4)
    motor_f = pymunk.SimpleMotor(wheel_f_b, chassis_b, 0.0)
    motor_f.max_force = WHEEL_TORQUE
    space.add(motor_f)

    # Return everything needed for driving
    return chassis_b, wheel_r_b, wheel_f_b, motor_r, motor_f


def add_jump(
    space: pymunk.Space,
    start_x: float,
    width: float,
    amplitude: float,
    cutoff: float = 1.0,
    steps: int = 32,  # Increased steps for better fidelity
):
    """
    Adds a jump using a smooth, progressive sin^2 curve (haversine form)
    to the static floor. The curve starts and ends with a zero slope.

    Parameters:
    - space: The pymunk.Space to add the segments to.
    - start_x: x-coordinate where the jump begins.
    - width: horizontal length of the jump (full run-up/ramp).
    - amplitude: vertical rise (maximum height of the jump).
    - cutoff: fraction of the full jump curve to use (0.0-1.0).
    - steps: number of segments for smoothness.
    """
    static = space.static_body
    points: list[tuple[float, float]] = []

    # Ensure the steps are adequate for a smooth curve
    steps = max(2, steps)

    # Generate points along the smooth curve
    for i in range(steps + 1):
        t_total = i / steps  # normalized position along the segment (0 to 1)

        # Apply the cutoff, ensuring the curve doesn't go beyond the desired fraction
        t = min(t_total, cutoff)

        x = start_x + t * width

        # Smooth Curve: 0.5 * (1 - cos(pi * t))
        # This function ranges from 0 (at t=0) to 1 (at t=1) smoothly.
        y = 1 + amplitude * 0.5 * (1 - math.cos(t * math.pi))

        points.append((x, y))

    segs = []
    # Create segments between consecutive points and add them to the space
    for i in range(len(points) - 1):
        seg = pymunk.Segment(static, points[i], points[i + 1], 0.2)
        # Set friction—adjust this value (1.0 is standard friction)
        seg.friction = 1.0
        segs.append(seg)

    return segs


def build_ground(space: pymunk.Space):
    static = space.static_body

    # flat floor first
    floor_segments: list[pymunk.Segment] = []
    floor_segments.append(pymunk.Segment(static, (0, 1), (250, 1), 0.2))

    # example: add a small jump starting at x=5, 3m wide, 2m high
    segs = add_jump(space, start_x=40, width=20, amplitude=10, cutoff=1.0)
    for seg in segs:
        floor_segments.append(seg)

    # example: partial jump (stop before full height) starting at x=10
    segs = add_jump(space, start_x=120, width=12, amplitude=5, cutoff=0.7)
    for seg in segs:
        floor_segments.append(seg)

    for seg in floor_segments:
        seg.friction = 1.0
        space.add(seg)

    return floor_segments


def run_game(screen: pygame.Surface, screen_h: int):
    space = pymunk.Space()
    space.gravity = GRAVITY

    draw_options = pymunk.pygame_util.DrawOptions(screen)
    # scale x by PIX_PER_METER, scale y by -PIX_PER_METER (flip), translate Y by screen height
    draw_options.transform = pymunk.Transform(
        PIX_PER_METER, 0, 0, -PIX_PER_METER, 0, screen_h
    )

    truck_starting_position = (7.0, 5.5)  # x=5m, y=3.5m above ground
    chassis_b, wheel_r_b, wheel_f_b, motor_r, motor_f = make_truck(
        space, truck_starting_position
    )
    controller_r = MotorController(motor_r)
    controller_f = MotorController(motor_f)

    ground_segs = build_ground(space)

    dt = 1.0 / FPS

    chassis_img = pygame.image.load("assets/truck_1_body.png").convert_alpha()
    width_px = int(TRUCK_LENGTH * PIX_PER_METER)
    height_px = int(TRUCK_HEIGHT * PIX_PER_METER)
    chassis_sprite = pygame.transform.scale(chassis_img, (width_px, height_px))

    wheel_size_px = int(WHEEL_RADIUS * 2 * PIX_PER_METER)
    wheel_img = pygame.image.load("assets/truck_1_wheel.png").convert_alpha()
    # The width and height must be equal for a circular wheel
    wheel_sprite = pygame.transform.scale(wheel_img, (wheel_size_px, wheel_size_px))

    # Get the initial dimensions for rotation calculation
    sprite_rect = chassis_sprite.get_rect()

    # ---------- Main loop ----------
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

        keys = pygame.key.get_pressed()
        input_direction = 0
        if keys[pygame.K_RIGHT]:
            input_direction = 1  # Forward
        elif keys[pygame.K_LEFT]:
            input_direction = -1  # Reverse

        is_braking = keys[pygame.K_SPACE]  # New check for spacebar

        # 2. Update the target speed based on arrow key input
        # Note: update_target MUST happen before step, even with braking!
        controller_r.update_target(input_direction)
        controller_f.update_target(input_direction)

        # 3. Step the motor speed towards the target over time
        # Pass the braking flag to the step method
        controller_r.step(dt, is_braking)
        controller_f.step(dt, is_braking)

        space.step(dt)

        screen.fill((174, 211, 250))
        # space.debug_draw(draw_options)

        for segment in ground_segs:
            # Pymunk segments store their endpoints as Vec2d objects in segment.a and segment.b

            # 1. Get the endpoints (Pymunk world coordinates)
            # Note: You must apply the body's position offset if the segment is attached to a dynamic body.
            # Since your jump segments are attached to the static_body, we can use segment.a/b directly.
            start_pos_m = segment.a
            end_pos_m = segment.b

            # 2. Convert Pymunk coordinates to Pygame screen coordinates
            start_pos_px = to_screen_coords(start_pos_m, screen_h, PIX_PER_METER)
            end_pos_px = to_screen_coords(end_pos_m, screen_h, PIX_PER_METER)

            # 3. Draw the line on the Pygame screen
            pygame.draw.line(screen, (173, 144, 127), start_pos_px, end_pos_px, 5)

        # Draw the body
        angle_rad = chassis_b.angle
        position_m = chassis_b.position
        angle_degrees = math.degrees(angle_rad)
        rendered_angle = angle_degrees
        rotated_image = pygame.transform.rotate(chassis_sprite, rendered_angle)
        rotated_rect = rotated_image.get_rect()
        center_x_px, center_y_px = to_screen_coords(position_m, SCREEN_H, PIX_PER_METER)
        rotated_rect.center = (center_x_px, center_y_px)
        screen.blit(rotated_image, rotated_rect)

        angle_rad = wheel_r_b.angle
        position_m = wheel_r_b.position
        angle_degrees = math.degrees(angle_rad)
        rendered_angle = -angle_degrees  # <-- FIX 2: Negate angle for visual correction
        rotated_image = pygame.transform.rotate(wheel_sprite, rendered_angle)
        rotated_rect = rotated_image.get_rect()
        center_x_px, center_y_px = to_screen_coords(position_m, SCREEN_H, PIX_PER_METER)
        rotated_rect.center = (center_x_px, center_y_px)
        screen.blit(rotated_image, rotated_rect)

        # Draw the front wheel
        angle_rad = wheel_f_b.angle
        position_m = wheel_f_b.position
        angle_degrees = math.degrees(angle_rad)
        rendered_angle = -angle_degrees  # <-- FIX 2: Negate angle for visual correction
        rotated_image = pygame.transform.rotate(wheel_sprite, rendered_angle)
        rotated_rect = rotated_image.get_rect()
        center_x_px, center_y_px = to_screen_coords(position_m, SCREEN_H, PIX_PER_METER)
        rotated_rect.center = (center_x_px, center_y_px)
        screen.blit(rotated_image, rotated_rect)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    run_game(screen, SCREEN_H)
    pygame.quit()
