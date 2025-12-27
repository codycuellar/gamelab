import math
import sys

import pygame
import pymunk

from monster_truck.config import *
from monster_truck.truck import Truck
from monster_truck.rendering_utils import Camera, print_time
from monster_truck.level_utils import load_level_geometry_from_svg, level_units_to_world
from monster_truck.menus import MENU_STATE, main_menu, game_over


pygame.init()


class HUD:
    def __init__(self):
        self.update_interval = 0.25
        self.timer = 0.0
        self.display_fps = 0.0
        self.display_speed = 0.0
        self.display_rpm_f = 0.0
        self.display_rpm_r = 0.0

    def step(self, dt: float, truck: Truck, fps):
        self.timer += dt

        if self.timer >= self.update_interval:
            self.display_speed = truck.chassis_body.velocity.length
            rad_to_rpm = 60 / (2 * math.pi)
            self.display_rpm_f = -truck.wheel_front_body.angular_velocity * rad_to_rpm
            self.display_rpm_r = -truck.wheel_rear_body.angular_velocity * rad_to_rpm
            self.display_fps = fps
            self.timer = 0.0


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


def run_game():
    # Load configurations
    current_level_config = load_level_config()
    current_truck_config = load_truck_config()

    default_start_position = level_units_to_world(
        current_level_config.start_position, current_level_config.units_per_meter
    )
    f_coord = current_level_config.finish_line
    finish_line = level_units_to_world(
        pymunk.Vec2d(f_coord, f_coord), current_level_config.units_per_meter
    ).x

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    camera = Camera((SCREEN_W, SCREEN_H), screen_scale=PX_PER_METER)

    menu_font = pygame.font.SysFont("Arial", 20, bold=True)

    space, terrain_points, truck = init_world(
        current_level_config,
        current_truck_config,
        default_start_position,
    )

    hud = HUD()

    level_time = 0
    menu_font = pygame.font.SysFont("Impact", 25)

    state = MENU_STATE.MAIN_MENU
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        space.step(dt)

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                running = False
                continue

        if state is MENU_STATE.MAIN_MENU:
            state = main_menu(screen, events, menu_font)
            continue
        elif state is MENU_STATE.GAME_OVER:
            state = game_over(screen, events, menu_font, level_time)
            continue
        elif state is MENU_STATE.QUIT:
            running = False
            continue
        elif state is MENU_STATE.START_GAME:
            space, terrain_points, truck = init_world(
                current_level_config,
                current_truck_config,
                default_start_position,
            )
            level_time = 0
            state = MENU_STATE.RUN_GAME

        # =====================================================================
        # RUN THE ACTUAL GAME
        # =====================================================================

        # 1. EVENT HANDLING (Use events for one-shot actions like Reset)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    state = MENU_STATE.MAIN_MENU
                if e.key == pygame.K_RETURN:
                    space, terrain_points, truck = init_world(
                        current_level_config,
                        current_truck_config,
                        truck.chassis_body.position + pymunk.Vec2d(0, 2),
                    )
                    level_time += 10

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

        # DRAWING
        screen.fill((174, 211, 250))
        color = (173, 144, 127)
        if len(terrain_points) >= 2:
            points_px = [camera.to_screen_coords(pt) for pt in terrain_points]
            pygame.draw.lines(screen, color, False, points_px, 3)
        truck.draw(screen, camera)

        # Draw HUD
        hud.step(dt, truck, clock.get_fps())
        metrics = [
            f"Time: {print_time(level_time)}",
            f"FPS: {int(hud.display_fps)}",
            f"Speed: {hud.display_speed:.1f} m/s",
            f"Front RPM: {int(hud.display_rpm_f)}",
            f"Rear RPM: {int(hud.display_rpm_r)}",
        ]
        for i, text in enumerate(metrics):
            surf = menu_font.render(text, True, (0, 0, 0))
            screen.blit(surf, (20, 20 + i * 25))

        # FINISH LINE
        for body in [truck.chassis_body, truck.wheel_rear_body, truck.wheel_front_body]:
            for shape in body.shapes:
                if shape.bb.left <= finish_line <= shape.bb.right:
                    state = MENU_STATE.GAME_OVER

        # space.debug_draw(draw_options)
        pygame.display.flip()
        level_time += dt


if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()
