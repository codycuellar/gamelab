import math
import sys
import pygame
import pymunk

from monster_truck.config import *
from monster_truck.truck import Truck
from monster_truck.rendering_utils import Camera
from monster_truck.level_utils import load_level_geometry_from_svg, level_units_to_world

pygame.init()


def rebuild_world(
    level_config: LevelConfig,
    truck_config: TruckConfig,
):
    """
    Creates a fresh space and populates it using PRE-LOADED geometry.
    This is extremely fast compared to re-scanning the image.
    """
    space = pymunk.Space()
    space.gravity = level_config.gravity
    terrain_points = load_level_geometry_from_svg(
        space,
        level_config.svg_path,
        level_config.units_per_meter,
        level_config.samples_per_meter,
        level_config.ground_friction,
    )

    truck = Truck(
        truck_config,
        space,
        level_units_to_world(level_config.start_position, level_config.units_per_meter),
    )
    return space, terrain_points, truck


def run_game():
    # Load configurations
    current_level_config = load_level_config()
    current_truck_config = load_truck_config()

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    camera = Camera((SCREEN_W, SCREEN_H), screen_scale=PX_PER_METER)
    font = pygame.font.SysFont("Arial", 20, bold=True)

    space, terrain_points, truck = rebuild_world(
        current_level_config, current_truck_config
    )

    # HUD Tracking
    metric_timer = 0.0
    display_fps = 0.0
    update_interval = 0.25
    display_speed = 0.0
    display_rpm_f = 0.0
    display_rpm_r = 0.0

    # draw_options = pymunk.pygame_util.DrawOptions(screen)
    # draw_options.transform = pymunk.Transform(10, 0, 0, -10, 0, SCREEN_H)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        space.step(dt)

        # 1. EVENT HANDLING (Use events for one-shot actions like Reset)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    # Instant reset using cached geometry
                    space, terrain_points, truck = rebuild_world(
                        current_level_config, current_truck_config
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

        truck.motor.update_target(input_direction, keys[pygame.K_SPACE])
        truck.motor.step()

        # 3. METRICS UPDATE
        metric_timer += dt
        if metric_timer >= update_interval:
            display_speed = truck.chassis_body.velocity.length
            rad_to_rpm = 60 / (2 * math.pi)
            display_rpm_f = -truck.wheel_front_body.angular_velocity * rad_to_rpm
            display_rpm_r = -truck.wheel_rear_body.angular_velocity * rad_to_rpm
            display_fps = clock.get_fps()
            metric_timer = 0.0

        # 4. DRAWING
        screen.fill((174, 211, 250))

        # Draw Terrain (from our cached polylines)
        color = (173, 144, 127)
        if len(terrain_points) >= 2:
            points_px = [camera.to_screen_coords(pt) for pt in terrain_points]
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

        # space.debug_draw(draw_options)
        pygame.display.flip()


if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()
