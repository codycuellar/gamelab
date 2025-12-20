import math
import pymunk
import pygame
from monster_truck.config import TruckConfig
from monster_truck.util import (
    Camera,
    draw_sprite,
    load_sprite_for_body,
)


class Truck:
    filter_group = 100

    def __init__(
        self,
        config: TruckConfig,
        space: pymunk.Space,
        default_position: pymunk.Vec2d = pymunk.Vec2d(0, 0),
    ):
        wheel_moment = pymunk.moment_for_circle(
            config.wheel_mass, 0, config.wheel_radius
        )
        truck_moment = pymunk.moment_for_box(config.mass, config.size)

        self.config = config
        self.default_position = default_position

        self.chassis_body = pymunk.Body(config.mass, truck_moment)
        self.chassis_body.position = default_position

        self.wheel_r_body = pymunk.Body(config.wheel_mass, wheel_moment)
        self.wheel_r_body.position = default_position + config.wheel_rear_offset
        self.wheel_f_body = pymunk.Body(config.wheel_mass, wheel_moment)
        self.wheel_f_body.position = default_position + config.wheel_front_offset

        self.add_suspension(space, self.wheel_r_body, config.wheel_rear_offset)
        self.add_suspension(space, self.wheel_f_body, config.wheel_front_offset)

        self.gear_joint = pymunk.GearJoint(self.wheel_r_body, self.wheel_f_body, 0, 1.0)
        self.motor = MotorController(config, self.wheel_r_body, self.chassis_body)

        chassis_s = pymunk.Poly.create_box(self.chassis_body, config.size)
        chassis_s.friction = config.body_friction
        chassis_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        wheel_r_s = pymunk.Circle(self.wheel_r_body, config.wheel_radius)
        wheel_r_s.friction = config.wheel_friction
        wheel_r_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        wheel_f_s = pymunk.Circle(self.wheel_f_body, config.wheel_radius)
        wheel_f_s.friction = config.wheel_friction
        wheel_f_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        space.add(
            self.gear_joint,
            self.chassis_body,
            chassis_s,
            self.wheel_r_body,
            wheel_r_s,
            self.wheel_f_body,
            wheel_f_s,
        )

        # self.init_position()

        self.chassis_renderable = load_sprite_for_body(
            self.chassis_body,
            config.chassis_sprite_path,
            config.length,
        )
        wheel_size = pymunk.Vec2d(config.wheel_diameter, config.wheel_diameter)
        self.wheel_r_renderable = load_sprite_for_body(
            self.wheel_r_body, config.wheel_sprite_path, wheel_size.x
        )
        self.wheel_f_renderable = load_sprite_for_body(
            self.wheel_f_body, config.wheel_sprite_path, wheel_size.x
        )

    def draw(self, screen: pygame.Surface, camera: Camera):
        draw_sprite(screen, self.chassis_renderable, camera)
        draw_sprite(screen, self.wheel_r_renderable, camera)
        draw_sprite(screen, self.wheel_f_renderable, camera)

    def add_suspension(
        self, space: pymunk.Space, wheel_body: pymunk.Body, wheel_offset: pymunk.Vec2d
    ):
        up = wheel_offset + pymunk.Vec2d(0, self.config.suspension_uptravel)
        down = wheel_offset - pymunk.Vec2d(0, self.config.suspension_downtravel)

        # anchor_b is the center of the wheel (local)
        groove = pymunk.GrooveJoint(
            self.chassis_body,
            wheel_body,
            up,  # upper stop (body local)
            down,  # lower stop (body local)
            (0, 0),  # wheel center (wheel local)
        )
        groove.collide_bodies = False
        spring = pymunk.DampedSpring(
            self.chassis_body,
            wheel_body,
            up + pymunk.Vec2d(0, 0.2),  # chassis anchor
            (0, 0),  # wheel center
            abs((up - down).y),
            self.config.suspension_spring_stiffness,
            self.config.suspension_damping,
        )
        spring.collide_bodies = False

        space.add(groove, spring)

    def init_position(self):
        """Move the truck to a new base position and reset velocities."""
        # Compute current bottom-left of the whole truck
        bb_min = pymunk.Vec2d(float("inf"), float("inf"))

        for body in (self.chassis_body, self.wheel_r_body, self.wheel_f_body):
            for shape in body.shapes:
                bb_min = pymunk.Vec2d(
                    min(bb_min.x, shape.bb.left), min(bb_min.y, shape.bb.bottom)
                )

        # Desired bottom-left position (world meters)
        target_bl = self.default_position

        # How far we need to move the whole truck
        delta = target_bl - bb_min

        # Move EVERYTHING by the same delta
        for body in (self.chassis_body, self.wheel_r_body, self.wheel_f_body):
            body.position += delta


class MotorController:
    def __init__(
        self, config: TruckConfig, wheel_body: pymunk.Body, chassis_body: pymunk.Body
    ):
        self.max_speed = config.top_speed
        self.wheel_radius = config.wheel_radius
        self.wheel_body = wheel_body
        self.chassis_body = chassis_body  # Added chassis reference
        self.wheel_torque = config.wheel_torque
        self.braking_torque = config.brake_torque
        self.rolling_resistance = config.rolling_resistance

        self.input_direction = 0  # -1, 0, 1
        self.is_braking = False

    def update_target(self, direction: int, braking: bool = False):
        self.input_direction = direction
        self.is_braking = braking

    def step(self, dt: float):
        # Reset torque from previous step to avoid accumulation
        # (Alternatively, you can do this in your main loop)
        applied_torque = 0.0

        if self.is_braking:
            # Braking: Apply torque opposite to current rotation
            if abs(self.wheel_body.angular_velocity) > 0.1:
                direction = 1 if self.wheel_body.angular_velocity < 0 else -1
                applied_torque = direction * self.braking_torque

        elif self.input_direction != 0:
            # WIP - Torque limiting based on wheel speed
            # wheel_speed = abs(self.wheel_body.angular_velocity) * self.wheel_radius
            # lerped_torque = self.wheel_torque * (
            #     (self.max_speed - (wheel_speed / 2)) / self.max_speed
            # )

            # applied_torque = self.input_direction * lerped_torque
            # Acceleration
            applied_torque = self.input_direction * self.wheel_torque

        else:
            # Rolling resistance / Friction
            # We apply a small counter-torque proportional to velocity
            applied_torque = -self.wheel_body.angular_velocity * self.rolling_resistance

        # --- THE KEY FIX ---
        # 1. Apply torque to the wheel
        self.wheel_body.torque += applied_torque

        # 2. Apply EQUAL AND OPPOSITE torque to the chassis
        # This creates the "lift" or "squat" effect
        self.chassis_body.torque -= applied_torque
