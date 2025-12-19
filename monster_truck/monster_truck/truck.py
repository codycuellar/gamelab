import pymunk
import pygame
from monster_truck.config import TruckConfig
from monster_truck.util import (
    Camera,
    SpriteRenderable,
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
        self.wheel_r_body = pymunk.Body(config.wheel_mass, wheel_moment)
        self.wheel_f_body = pymunk.Body(config.wheel_mass, wheel_moment)

        self.motor_rear = MotorController(config, self.wheel_r_body, self.chassis_body)
        self.motor_front = MotorController(config, self.wheel_f_body, self.chassis_body)

        self.chassis_renderable = load_sprite_for_body(
            self.chassis_body,
            config.chassis_sprite_path,
            pymunk.Vec2d(config.length, config.height),
        )
        wheel_size = pymunk.Vec2d(config.wheel_diameter, config.wheel_diameter)
        self.wheel_r_renderable = load_sprite_for_body(
            self.wheel_r_body, config.wheel_sprite_path, wheel_size
        )
        self.wheel_f_renderable = load_sprite_for_body(
            self.wheel_f_body, config.wheel_sprite_path, wheel_size
        )

        chassis_s = pymunk.Poly.create_box(self.chassis_body, config.size)
        chassis_s.friction = config.body_friction
        chassis_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        wheel_r_s = pymunk.Circle(self.wheel_r_body, config.wheel_radius)
        wheel_r_s.friction = config.wheel_friction
        wheel_r_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        wheel_f_s = pymunk.Circle(self.wheel_f_body, config.wheel_radius)
        wheel_f_s.friction = config.wheel_friction
        wheel_f_s.filter = pymunk.ShapeFilter(group=Truck.filter_group)

        self.wheel_r_body.position = config.wheel_rear_offset
        self.wheel_f_body.position = config.wheel_front_offset

        space.add(self.chassis_body, chassis_s)
        space.add(self.wheel_r_body, wheel_r_s)
        space.add(self.wheel_f_body, wheel_f_s)
        space.add(
            pymunk.PivotJoint(
                self.wheel_r_body, self.chassis_body, self.wheel_r_body.position
            ),
            pymunk.PivotJoint(
                self.wheel_f_body, self.chassis_body, self.wheel_f_body.position
            ),
        )

        self.init_position()

    def draw(self, screen: pygame.Surface, camera: Camera):
        draw_sprite(screen, self.chassis_renderable, camera)
        draw_sprite(screen, self.wheel_r_renderable, camera)
        draw_sprite(screen, self.wheel_f_renderable, camera)

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
