import math
import sys
import pygame
import pymunk

from monster_truck.config import *
from monster_truck.truck import Truck
from monster_truck.rendering_utils import Camera
from monster_truck.level_utils import load_level_geometry_from_svg, level_units_to_world

pygame.init()


def init_world(
    level_config: LevelConfig, truck_config: TruckConfig, start_position: pymunk.Vec2d
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

    truck = Truck(truck_config, space, start_position)
    return space, terrain_points, truck


def print_time(t: float):
    minutes = int(t // 60)
    seconds = int(t % 60)
    return f"{minutes}:{seconds:02d}"


def run_game():
    # Load configurations
    current_level_config = load_level_config()
    current_truck_config = load_truck_config()
    f_coord = current_level_config.finish_line
    finish_line = level_units_to_world(
        pymunk.Vec2d(f_coord, f_coord), current_level_config.units_per_meter
    ).x

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    camera = Camera((SCREEN_W, SCREEN_H), screen_scale=PX_PER_METER)

    menu_font = pygame.font.SysFont("Arial", 20, bold=True)
    menu_bg_color = (220, 247, 247)
    menu_font_color = (125, 97, 95)

    space, terrain_points, truck = init_world(
        current_level_config,
        current_truck_config,
        level_units_to_world(
            current_level_config.start_position, current_level_config.units_per_meter
        ),
    )

    # HUD Tracking
    metric_timer = 0.0
    display_fps = 0.0
    update_interval = 0.25
    display_speed = 0.0
    display_rpm_f = 0.0
    display_rpm_r = 0.0

    level_time = 0
    game_start = True
    game_over = False

    menu_font = pygame.font.SysFont("Impact", 25)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        space.step(dt)

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False

        if game_start:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        game_start = False

            screen.fill(menu_bg_color)
            text = menu_font.render(
                f"Press spacebar to start the game!",
                True,
                menu_font_color,
            )
            text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            screen.blit(text, text_rect)
            pygame.display.flip()
            continue

        if game_over:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        game_over = False
                        level_time = 0
                        space, terrain_points, truck = init_world(
                            current_level_config,
                            current_truck_config,
                            level_units_to_world(
                                current_level_config.start_position,
                                current_level_config.units_per_meter,
                            ),
                        )

            screen.fill(menu_bg_color)
            text = menu_font.render(
                f"Level Complete! Your time: {print_time(level_time)}",
                True,
                menu_font_color,
            )
            text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            screen.blit(text, text_rect)

            text = menu_font.render(
                f"Press spacebar to try again!", True, menu_font_color
            )
            text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30))
            screen.blit(text, text_rect)
            pygame.display.flip()
            continue

        level_time += dt

        # 1. EVENT HANDLING (Use events for one-shot actions like Reset)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    # Instant reset using cached geometry
                    space, terrain_points, truck = init_world(
                        current_level_config,
                        current_truck_config,
                        truck.chassis_body.position + pymunk.Vec2d(0, 2),
                    )

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

        for body in [truck.chassis_body, truck.wheel_rear_body, truck.wheel_front_body]:
            for shape in body.shapes:
                bb = shape.bb
                if bb.left <= finish_line <= bb.right:
                    game_over = True

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
            shadow = menu_font.render(text, True, (255, 255, 255))
            surf = menu_font.render(text, True, (0, 0, 0))
            screen.blit(shadow, (22, 22 + i * 25))
            screen.blit(surf, (20, 20 + i * 25))

        # space.debug_draw(draw_options)
        pygame.display.flip()


if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()
