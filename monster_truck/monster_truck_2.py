import math
import pygame
import pymunk
import pymunk.pygame_util

FPS = 60.0

# ---------- Screen / Scale ----------
PIX_PER_METER = 30.0  # how many pixels equal 1 meter
SCREEN_W = 2048  # ~34m
SCREEN_H = 1200  # ~20m

# ---------- Truck Setup ----------
TRUCK_LENGTH = 4.7  # meters
TRUCK_HEIGHT = 2.2  # meters
TRUCK_SIZE = (TRUCK_LENGTH, TRUCK_HEIGHT)
TRUCK_MASS = 4500  # kg (rough mass for a big truck)
TRUCK_TOP_SPEED = 18.0
TRUCK_ACCELERATION = 4.0

# ---------- Wheel Setup ----------
WHEEL_RADIUS = 0.9  # meters (radius)
WHEEL_REAR_OFFSET = (-TRUCK_LENGTH / 3.0, -TRUCK_HEIGHT / 1.4)
WHEEL_FRONT_OFFSET = (TRUCK_LENGTH / 3.0, -TRUCK_HEIGHT / 1.4)
WHEEL_MASS = 700.0  # kg per wheel (rough)
WHEEL_FRICTION = 1
MAX_WHEEL_SPEED = 18.0
WHEEL_TORQUE = 50000

pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock = pygame.time.Clock()


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
    chassis_s.friction = 1.0
    chassis_s.filter = pymunk.ShapeFilter(group=filter_group)
    space.add(chassis_b, chassis_s)

    wheel_r_b.position = position + pymunk.Vec2d(*WHEEL_REAR_OFFSET)
    wheel_f_b.position = position + pymunk.Vec2d(*WHEEL_FRONT_OFFSET)
    chassis_b.position = pymunk.Vec2d(*position)

    space.add(
        pymunk.PivotJoint(wheel_r_b, chassis_b, wheel_r_b.position),
        pymunk.PivotJoint(wheel_f_b, chassis_b, wheel_f_b.position),
    )

    # Return everything needed for driving
    return chassis_b, wheel_r_b, wheel_f_b


def add_jump(
    space: pymunk.Space,
    start_x: float,
    width: float,
    amplitude: float,
    cutoff: float = 1.0,
    steps: int = 16,
):
    """
    Adds a jump (cosine ramp) to the static floor.

    Parameters:
    - start_x: x-coordinate where the jump starts
    - width: horizontal length of the jump
    - amplitude: vertical rise (meters)
    - cutoff: fraction of full jump (0.0-1.0), 1.0 = full height
    - steps: number of segments for smoothness
    """
    static = space.static_body
    points: list[tuple[float, float]] = []

    # generate points along the cosine curve
    for i in range(steps + 1):
        t = i / steps  # normalized 0 → 1
        if t > cutoff:
            t = cutoff
        x = start_x + t * width
        y = 1 + amplitude * (1 - math.cos(t * math.pi / 2))  # starts at floor y=1
        points.append((x, y))

    segs = []
    # create segments between consecutive points
    for i in range(len(points) - 1):
        segs.append(pymunk.Segment(static, points[i], points[i + 1], 0.2))

    return segs


def build_ground(space: pymunk.Space):
    static = space.static_body

    # flat floor first
    floor_segments: list[pymunk.Segment] = []
    floor_segments.append(pymunk.Segment(static, (0, 1), (100, 1), 0.2))

    # example: add a small jump starting at x=5, 3m wide, 2m high
    segs = add_jump(space, start_x=20, width=3, amplitude=2, cutoff=1.0)
    for seg in segs:
        floor_segments.append(seg)

    # example: partial jump (stop before full height) starting at x=10
    segs = add_jump(space, start_x=50, width=2, amplitude=1.5, cutoff=0.7)
    for seg in segs:
        floor_segments.append(seg)

    for seg in floor_segments:
        seg.friction = 1.0
        space.add(seg)


def run_game(screen, screen_h):
    space = pymunk.Space()
    space.gravity = (0, -9.81)  # meters / s^2 (world uses meters)

    draw_options = pymunk.pygame_util.DrawOptions(screen)
    # scale x by PIX_PER_METER, scale y by -PIX_PER_METER (flip), translate Y by screen height
    draw_options.transform = pymunk.Transform(
        PIX_PER_METER, 0, 0, -PIX_PER_METER, 0, screen_h
    )

    truck_starting_position = (7.0, 5.5)  # x=5m, y=3.5m above ground
    chassis, wheel_r, wheel_f = make_truck(space, truck_starting_position)

    build_ground(space)

    dt = 1.0 / FPS

    # ---------- Main loop ----------
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

        keys = pygame.key.get_pressed()
        # calculate desired torque
        desired_torque = (
            -WHEEL_TORQUE
            if keys[pygame.K_RIGHT]
            else WHEEL_TORQUE if keys[pygame.K_LEFT] else 0.0
        )

        # --- 2. Check the linear speed limit of the chassis body ---
        truck_body_velocity_magnitude = chassis.velocity.length

        # Check if the truck is already at or above its top speed AND
        # the input is trying to increase the speed.
        if (
            (truck_body_velocity_magnitude > TRUCK_TOP_SPEED)
            and (truck_body_velocity_magnitude > 0 and desired_torque > 0)
            or (truck_body_velocity_magnitude > 0 and desired_torque < 0)
        ):  # Check reversing too, if necessary

            # If moving forward faster than limit, and trying to go faster, cut power.
            # Note: You may want to relax this slightly to allow for very fast wheel spin
            # during a jump or wheelie, which is typical for a monster truck.
            if desired_torque > 0:
                desired_torque = 0.0
            # Add reverse checks if your TRUCK_TOP_SPEED is the same for reverse.

        # --- 3. Apply the FULL desired torque equally to both wheels ---
        # A locked diff means both wheels receive the same torque.
        wheel_r.torque += desired_torque
        wheel_f.torque += desired_torque

        space.step(dt)

        screen.fill((30, 30, 40))
        space.debug_draw(draw_options)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    run_game(screen, SCREEN_H)
    pygame.quit()
