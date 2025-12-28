import math
from enum import Enum

import pygame
from pymunk import Vec2d, Space, BB

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
    volume = 0.45
    fade = 100

    def __init__(self):
        self.loop_ch = pygame.mixer.Channel(2)  # idle / full throttle loops
        self.trans_ch = pygame.mixer.Channel(3)  # accel / decel transitions
        self.loop_ch.set_volume(self.volume)
        self.trans_ch.set_volume(self.volume)

        self.start = pygame.mixer.Sound("assets/trucks/truck_1/sfx/truck_1_start.wav")
        self.idle = pygame.mixer.Sound("assets/trucks/truck_1/sfx/truck_1_idle.wav")
        self.accel = pygame.mixer.Sound("assets/trucks/truck_1/sfx/accelerate.wav")
        self.full_throttle = pygame.mixer.Sound(
            "assets/trucks/truck_1/sfx/full_throttle.wav"
        )
        self.decel = pygame.mixer.Sound("assets/trucks/truck_1/sfx/decelerate.wav")

        self.state = ENGINE_STATES.STOPPED
        self.wants_throttle = False
        self.next_loop = self.idle

    def start_engine(self):
        if self.state != ENGINE_STATES.STOPPED:
            return

        self.loop_ch.play(self.start)
        self.state = ENGINE_STATES.IDLE
        self.next_loop = self.idle

    def set_throttle(self, state: bool):
        self.wants_throttle = state

    def stop(self):
        """Stop all engine sounds immediately and reset state."""
        self.loop_ch.stop()
        self.trans_ch.stop()
        self.state = ENGINE_STATES.STOPPED
        self.next_loop = self.idle
        self.wants_throttle = False

    def step(self, _):
        # Handle throttle changes / transitions
        if self.state in [ENGINE_STATES.IDLE, ENGINE_STATES.FULL_THROTTLE]:
            if self.wants_throttle and self.state == ENGINE_STATES.IDLE:
                self._play_transition(self.accel, self.full_throttle)
                self.state = ENGINE_STATES.ACCEL
            elif not self.wants_throttle and self.state == ENGINE_STATES.FULL_THROTTLE:
                self._play_transition(self.decel, self.idle)
                self.state = ENGINE_STATES.DECEL

        if self.state == ENGINE_STATES.DECEL and self.wants_throttle:
            self._play_transition(self.accel, self.full_throttle)
            self.state = ENGINE_STATES.ACCEL
        elif self.state == ENGINE_STATES.ACCEL and not self.wants_throttle:
            self._play_transition(self.decel, self.idle)
            self.state = ENGINE_STATES.DECEL

        # **Restart loop channel if transition finished**
        if not self.trans_ch.get_busy():
            # Only restart if loop channel is not currently playing
            if not self.loop_ch.get_busy():
                self.loop_ch.play(self.next_loop, loops=-1)
                # Update state to loop type
                if self.next_loop == self.idle:
                    self.state = ENGINE_STATES.IDLE
                else:
                    self.state = ENGINE_STATES.FULL_THROTTLE

    def _play_transition(self, sound, next_loop):
        if self.trans_ch.get_busy():
            self.trans_ch.stop()

        # Fade the loop channel slightly
        self.loop_ch.fadeout(self.fade)

        # Play the new transition
        self.trans_ch.play(sound)

        # Update which loop to return to
        self.next_loop = next_loop


class Game:
    screen_dims = (SCREEN_W, SCREEN_H)
    px_per_meter = PX_PER_METER

    def __init__(self, clock: pygame.time.Clock):
        self.sfx = EngineSounds()

        self.level_config = load_level_config()
        self.truck_config = load_truck_config()
        self.default_start_position = Vec2d(0, 0)

        self.clock = clock
        self.screen = pygame.display.set_mode(self.screen_dims)
        self.camera = Camera(self.screen_dims, screen_scale=self.px_per_meter)
        self.finish_line = Vec2d(0, 0)
        self.level_time = 0

        self.hud_font = pygame.font.SysFont("Arial", 18, bold=True)

        self.space: Space = None
        self.terrain_points: list[Vec2d] = []
        self.truck: Truck = None

        self.checkpoints = []
        self.checkpoint_i = 0

        self.hud = HUD()

    def init(self):
        self.space = Space()
        self.space.gravity = self.level_config.gravity

        self.terrain_points = load_level_geometry_from_svg(
            self.space,
            self.level_config.svg_path,
            self.level_config.units_per_meter,
            self.level_config.samples_per_meter,
            self.level_config.ground_friction,
        )

        pos = Vec2d(self.level_config.start_position, 0)
        pos = self._to_world(pos)
        self.default_start_position = self._get_truck_pos(pos.x)

        self.finish_line = self._to_world(Vec2d(self.level_config.finish_line, 0))

        self.checkpoints = [self.default_start_position] + [
            self._to_world(Vec2d(x, 0)) for x in self.level_config.checkpoints
        ]

        self.truck = Truck(
            self.truck_config,
            self.space,
            self.default_start_position,
        )

    def reset_truck(self):
        self.truck = Truck(
            self.truck_config,
            self.space,
            self._get_truck_pos(self.checkpoints[self.checkpoint_i].x),
        )

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

        # CHECKPOINTS / FINISH LINE
        truck_bb = self.truck.bb
        if self.checkpoint_i < len(self.checkpoints) - 2:
            if truck_bb.right >= self.checkpoints[self.checkpoint_i + 1].x:
                self.checkpoint_i += 1

        if truck_bb.right >= self.finish_line.x:
            return MENU_STATE.GAME_OVER

        pygame.display.flip()

        self.level_time += dt

        self.sfx.start_engine()  # always call this, but will only trigger once
        self.sfx.set_throttle(input_direction != 0)
        self.sfx.step(dt)

        return MENU_STATE.RUN_GAME

    def _to_world(self, pos: Vec2d):
        return level_units_to_world(pos, self.level_config.units_per_meter)

    def _get_truck_pos(self, x_axis: float):
        points: list[Vec2d] = []
        for i, current in enumerate(self.terrain_points):
            if i >= len(self.terrain_points) - 1:
                continue
            next = self.terrain_points[i + 1]
            if (current.x <= x_axis and next.x >= x_axis) or (
                current.x >= x_axis and next.x <= x_axis
            ):
                points.append(current)
                points.append(next)

        print(points)
        if len(points) == 0:
            raise Exception(
                f"x-axis position {x_axis} does not intersect with ground plane."
            )

        highest = points.pop()
        while len(points) > 0:
            p = points.pop()
            if p.y > highest.y:
                highest = p

        print("highest", highest)
        return highest + Vec2d(0, 5)


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
