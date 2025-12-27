import math
from enum import Enum

import pygame
from pymunk import Vec2d, Space

from monster_truck.config import *
from monster_truck.rendering_utils import Camera, print_time
from monster_truck.truck import Truck
from monster_truck.level_utils import (
    load_level_config,
    load_truck_config,
    level_units_to_world,
    load_level_geometry_from_svg,
)


class ENGINE_STATES:
    STOPPED = 0
    IDLE = 1
    ACCEL = 2
    DECEL = 3
    FULL_THROTTLE = 4


class EngineSounds:
    volume = 0.85

    def __init__(self):
        self.channel = pygame.mixer.Channel(2)  # reserve a channel

        self.start = pygame.mixer.Sound("assets/trucks/truck_1/sfx/truck_1_start.wav")
        self.idle = pygame.mixer.Sound("assets/trucks/truck_1/sfx/truck_1_idle.wav")
        self.accelerate = pygame.mixer.Sound("assets/trucks/truck_1/sfx/accelerate.wav")
        self.full_throttle = pygame.mixer.Sound(
            "assets/trucks/truck_1/sfx/full_throttle.wav"
        )
        self.decelerate = pygame.mixer.Sound("assets/trucks/truck_1/sfx/decelerate.wav")
        self.state = ENGINE_STATES.STOPPED
        self.wants_throttle = False

    def start_engine(self):
        if self.state != ENGINE_STATES.STOPPED:
            return

        self.channel.play(self.start)
        self.channel.queue(self.idle)
        self.state = ENGINE_STATES.IDLE

    def set_throttle(self, state: bool):
        self.wants_throttle = state

    def step(self, _):
        if self.channel.get_queue():
            return

        if self.state == ENGINE_STATES.IDLE:
            if self.wants_throttle:
                self.channel.play(self.accelerate)
                self.state = ENGINE_STATES.ACCEL
            else:
                self.channel.queue(self.idle)

        elif self.state == ENGINE_STATES.ACCEL:
            if self.wants_throttle:
                self.channel.queue(self.full_throttle)
                self.state = ENGINE_STATES.FULL_THROTTLE
            else:
                self.channel.play(self.decelerate)
                self.state = ENGINE_STATES.DECEL

        elif self.state == ENGINE_STATES.FULL_THROTTLE:
            if self.wants_throttle:
                self.channel.queue(self.full_throttle)
            else:
                self.channel.play(self.decelerate)
                self.state = ENGINE_STATES.DECEL

        elif self.state == ENGINE_STATES.DECEL:
            if self.wants_throttle:
                self.channel.queue(self.accelerate)
                self.state = ENGINE_STATES.ACCEL
            else:
                self.channel.queue(self.idle)
                self.state = ENGINE_STATES.IDLE


class Game:
    screen_dims = (SCREEN_W, SCREEN_H)
    px_per_meter = PX_PER_METER

    def __init__(self, clock: pygame.time.Clock):
        self.sfx = EngineSounds()

        self.level_config = load_level_config()
        self.truck_config = load_truck_config()
        self.default_start_position = level_units_to_world(
            self.level_config.start_position, self.level_config.units_per_meter
        )

        self.clock = clock
        self.screen = pygame.display.set_mode(self.screen_dims)
        self.camera = Camera(self.screen_dims, screen_scale=self.px_per_meter)
        self.finish_line = Vec2d(0, 0)
        self.level_time = 0

        self.hud_font = pygame.font.SysFont("Arial", 18, bold=True)

        self.space: Space = None
        self.terrain_points: list[Vec2d] = []
        self.truck: Truck = None

        self.hud = HUD()

        self.init()

    def init(self):
        f_coord = self.level_config.finish_line
        self.finish_line = level_units_to_world(
            Vec2d(f_coord, f_coord), self.level_config.units_per_meter
        ).x
        self.space = Space()
        self.space.gravity = self.level_config.gravity
        self.terrain_points = load_level_geometry_from_svg(
            self.space,
            self.level_config.svg_path,
            self.level_config.units_per_meter,
            self.level_config.samples_per_meter,
            self.level_config.ground_friction,
        )

        self.truck = Truck(
            self.truck_config,
            self.space,
            self.default_start_position,
        )

    def reset_truck(self):
        self.truck = Truck(
            self.truck_config,
            self.space,
            self.truck.chassis_body.position + Vec2d(0, 2),
        )
        self.level_time += 10

    def step(self, dt: float):
        self.space.step(dt)

        keys = pygame.key.get_pressed()
        self.camera.base_pos = self.truck.chassis_body.position

        input_direction = 0
        if keys[pygame.K_RIGHT]:
            input_direction = -1
        elif keys[pygame.K_LEFT]:
            input_direction = 1

        self.truck.motor.update_target(input_direction, keys[pygame.K_SPACE])
        self.truck.motor.step()

        # DRAWING
        self.screen.fill((174, 211, 250))
        color = (173, 144, 127)
        if len(self.terrain_points) >= 2:
            points_px = [self.camera.to_screen_coords(pt) for pt in self.terrain_points]
            pygame.draw.lines(self.screen, color, False, points_px, 3)
        self.truck.draw(self.screen, self.camera)

        # Draw HUD
        self.hud.step(dt, self.truck, self.clock.get_fps())
        metrics = [
            f"Time: {print_time(self.level_time)}",
            f"FPS: {int(self.hud.display_fps)}",
            f"Speed: {self.hud.display_speed:.1f} m/s",
            f"Front RPM: {int(self.hud.display_rpm_f)}",
            f"Rear RPM: {int(self.hud.display_rpm_r)}",
        ]
        for i, text in enumerate(metrics):
            surf = self.hud_font.render(text, True, (0, 0, 0))
            self.screen.blit(surf, (20, 20 + i * 25))

        # FINISH LINE
        for body in [
            self.truck.chassis_body,
            self.truck.wheel_rear_body,
            self.truck.wheel_front_body,
        ]:
            for shape in body.shapes:
                if shape.bb.left <= self.finish_line <= shape.bb.right:
                    return MENU_STATE.GAME_OVER

        # space.debug_draw(draw_options)
        pygame.display.flip()

        self.level_time += dt

        self.sfx.start_engine()  # always call this, but will only trigger once
        self.sfx.set_throttle(input_direction != 0)
        self.sfx.step(dt)

        return MENU_STATE.RUN_GAME


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
