import math

import pymunk
import pygame

from monster_truck.configs.interfaces import (
    TruckConfig,
    WheelConfig,
    SuspensionConfig,
    ChassisConfig,
)
from monster_truck.rendering_utils import (
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
        self.config = config
        self.space = space

        self.default_position = default_position
        self.chassis_body = self._build_chassis(config.chassis)
        self.wheel_rear_body = self._build_wheel(config.wheel_rear)
        self.wheel_front_body = self._build_wheel(config.wheel_front)

        self.motor = MotorController(config, self.wheel_rear_body, self.chassis_body)
        space.add(pymunk.GearJoint(self.wheel_rear_body, self.wheel_front_body, 0, 1.0))

        self.chassis_renderable = load_sprite_for_body(
            self.chassis_body, config.chassis.sprite_path, config.chassis.dimensions
        )

        self.wheel_r_renderable = load_sprite_for_body(
            self.wheel_rear_body,
            config.wheel_rear.sprite_path,
            config.wheel_rear.dimensions,
        )

        self.wheel_f_renderable = load_sprite_for_body(
            self.wheel_front_body,
            config.wheel_front.sprite_path,
            config.wheel_front.dimensions,
        )

    @property
    def bb(self):
        shapes = (
            list(self.chassis_body.shapes)
            + list(self.wheel_rear_body.shapes)
            + list(self.wheel_front_body.shapes)
        )

        return pymunk.BB(
            left=min(s.bb.left for s in shapes),
            right=max(s.bb.right for s in shapes),
            top=max(s.bb.top for s in shapes),
            bottom=min(s.bb.bottom for s in shapes),
        )

    def draw(self, screen: pygame.Surface, camera: Camera):
        draw_sprite(screen, self.chassis_renderable, camera)
        draw_sprite(screen, self.wheel_r_renderable, camera)
        draw_sprite(screen, self.wheel_f_renderable, camera)

    def _build_chassis(self, config: ChassisConfig):
        chassis_moment = pymunk.moment_for_box(config.mass, config.dimensions)
        chassis_body = pymunk.Body(config.mass, chassis_moment)
        chassis_body.position = self.default_position

        chassis_shape = pymunk.Poly.create_box(chassis_body, config.dimensions)
        chassis_shape.friction = config.friction
        chassis_shape.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        self.space.add(chassis_body, chassis_shape)

        return chassis_body

    def _build_wheel(self, config: WheelConfig):
        wheel_moment = pymunk.moment_for_circle(config.mass, 0, config.radius)
        wheel_body = pymunk.Body(config.mass, wheel_moment)
        wheel_body.position = self.default_position + config.offset

        wheel_shape = pymunk.Circle(wheel_body, config.radius)
        wheel_shape.friction = config.friction
        wheel_shape.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        self._add_suspension(config.suspension, wheel_body, config.offset)

        self.space.add(wheel_body, wheel_shape)
        return wheel_body

    def _add_suspension(
        self,
        config: SuspensionConfig,
        wheel_body: pymunk.Body,
        wheel_offset: pymunk.Vec2d,
    ):
        up = wheel_offset + pymunk.Vec2d(0, config.uptravel)
        down = wheel_offset - pymunk.Vec2d(0, config.downtravel)

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
            # add some extra offset so the spring joint and the groove
            up + pymunk.Vec2d(0, 0.2),  # chassis anchor
            (0, 0),  # wheel center
            abs((up - down).y),
            config.stiffness,
            config.damping,
        )
        spring.collide_bodies = False

        self.space.add(groove, spring)


class MotorController:
    def __init__(
        self, config: TruckConfig, wheel_body: pymunk.Body, chassis_body: pymunk.Body
    ):
        self.max_speed = config.top_speed
        self.wheel_body = wheel_body
        self.chassis_body = chassis_body
        self.wheel_torque = config.torque
        self.braking_torque = config.brake_torque
        self.rolling_resistance = config.rolling_resistance

        self.input_direction = 0  # -1, 0, 1
        self.is_braking = False

    def update_target(self, direction: int, braking: bool = False):
        self.input_direction = direction
        self.is_braking = braking

    def step(self):
        # Reset torque from previous step to avoid accumulation
        applied_torque = 0.0

        if self.is_braking:
            # Braking: Apply torque opposite to current rotation
            if abs(self.wheel_body.angular_velocity) > 0.1:
                direction = 1 if self.wheel_body.angular_velocity < 0 else -1
                applied_torque = direction * self.braking_torque

        elif self.input_direction != 0:
            # Acceleration
            applied_torque = self.input_direction * self.wheel_torque

        else:
            # Rolling resistance / Friction
            # We apply a small counter-torque proportional to velocity to simulate rolling
            # resistance, but this also gradually slows wheels mid-air when throttle is not
            # applied, and could be improvbed.
            applied_torque = math.copysign(
                self.wheel_torque * self.rolling_resistance,
                -self.wheel_body.angular_velocity,
            )

        # 1. Apply torque to the wheel
        self.wheel_body.torque += applied_torque

        # apply inverse torque of wheel to body (allows in-air rotation and wheelies)
        self.chassis_body.torque -= applied_torque
