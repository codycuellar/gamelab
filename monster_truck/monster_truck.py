import math
import sys
import pygame
import pymunk

from monster_truck.config import *
from monster_truck.truck import Truck
from monster_truck.util import Camera
from monster_truck.level import load_level_geometry

pygame.init()


def rebuild_world(
    level_config: LevelConfig, truck_config: TruckConfig, polylines, start_pos
):
    """
    Creates a fresh space and populates it using PRE-LOADED geometry.
    This is extremely fast compared to re-scanning the image.
    """
    space = pymunk.Space()
    space.gravity = level_config.gravity

    # 1. Add segments to the new space from our cached polylines
    for polyline in polylines:
        for p1, p2 in zip(polyline, polyline[1:]):
            seg = pymunk.Segment(space.static_body, p1, p2, 0.2)
            seg.friction = level_config.ground_friction
            space.add(seg)

    # 2. Re-init the truck in the new space
    truck = Truck(truck_config, space, start_pos)

    return space, truck


def run_game():
    dt = 1.0 / FPS

    # Load configurations
    level_config = load_level_config(DEFAULT_LEVEL)
    truck_config = load_truck_config(DEFAULT_TRUCK)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    # --- ONE TIME HEAVY LIFTING ---
    # We create a dummy space just to extract the geometry once
    temp_space = pymunk.Space()
    terrain_polylines, truck_start_pos = load_level_geometry(level_config, temp_space)

    # --- INITIAL PHYSICS SETUP ---
    space, truck = rebuild_world(
        level_config, truck_config, terrain_polylines, truck_start_pos
    )

    camera = Camera((SCREEN_W, SCREEN_H), screen_scale=PX_PER_METER)
    font = pygame.font.SysFont("Arial", 20, bold=True)

    # HUD Tracking
    metric_timer = 0.0
    display_fps = 0.0
    update_interval = 0.25
    display_speed = 0.0
    display_rpm_f = 0.0
    display_rpm_r = 0.0

    running = True
    while running:
        # 1. EVENT HANDLING (Use events for one-shot actions like Reset)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    # Instant reset using cached geometry
                    space, truck = rebuild_world(
                        level_config, truck_config, terrain_polylines, truck_start_pos
                    )
                if e.key == pygame.K_q:
                    running = False

        # 2. INPUT & PHYSICS
        keys = pygame.key.get_pressed()
        camera.base_pos = truck.chassis_body.position

        input_direction = 0
        if keys[pygame.K_RIGHT]:
            input_direction = -1
        elif keys[pygame.K_LEFT]:
            input_direction = 1

        is_braking = keys[pygame.K_SPACE]

        truck.motor_front.update_target(input_direction, is_braking)
        truck.motor_rear.update_target(input_direction, is_braking)
        truck.motor_front.step(dt)
        truck.motor_rear.step(dt)

        # 3. METRICS UPDATE
        metric_timer += dt
        if metric_timer >= update_interval:
            display_speed = truck.chassis_body.velocity.length
            rad_to_rpm = 60 / (2 * math.pi)
            display_rpm_f = -truck.wheel_f_body.angular_velocity * rad_to_rpm
            display_rpm_r = -truck.wheel_r_body.angular_velocity * rad_to_rpm
            display_fps = clock.get_fps()
            metric_timer = 0.0

        # 4. DRAWING
        screen.fill((174, 211, 250))

        # Draw Terrain (from our cached polylines)
        color = (173, 144, 127)
        for polyline in terrain_polylines:
            if len(polyline) >= 2:
                points_px = [camera.to_screen_coords(pt) for pt in polyline]
                pygame.draw.lines(screen, color, False, points_px, 3)

        truck.draw(screen, camera)

        # Draw HUD
        metrics = [
            f"FPS: {int(display_fps)}",
            f"Speed: {display_speed:.1f} m/s",
            f"Front RPM: {int(display_rpm_f)}",
            f"Rear RPM: {int(display_rpm_r)}",
        ]
        for i, text in enumerate(metrics):
            shadow = font.render(text, True, (255, 255, 255))
            surf = font.render(text, True, (0, 0, 0))
            screen.blit(shadow, (22, 22 + i * 25))
            screen.blit(surf, (20, 20 + i * 25))

        pygame.display.flip()
        space.step(dt)
        clock.tick(FPS)


if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()
