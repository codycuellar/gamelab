import math
import pymunk
import pygame
from monster_truck.config import *
from monster_truck.util import to_screen_coords


class MotorController:
    def __init__(
        self, config: TruckConfig, motor: pymunk.SimpleMotor, initial_force: float
    ):
        self.config = config
        self.motor = motor
        self.current_rate = 0.0
        self.target_rate = 0.0
        self.is_neutral = True
        self.initial_force = initial_force
        self.motor.max_force = self.initial_force

    def update_target(self, input_direction: int):
        """Sets the target rate based on input (1=Right/Forward, -1=Left/Reverse, 0=None)."""
        if input_direction == 1:
            self.is_neutral = False
            self.target_rate = (
                -self.config.top_speed
            )  # Assuming Right is Forward/CW (negative rate)
        elif input_direction == -1:
            self.is_neutral = False
            self.target_rate = (
                self.config.top_speed  # Assuming Left is Reverse/CCW (positive rate)
            )
        else:
            self.is_neutral = True
            self.target_rate = 0.0

    def step(self, dt, is_braking: bool):
        """Smoothly moves the motor rate towards the target rate, respecting braking."""

        # If the spacebar is held, the target rate is ZERO, regardless of other input
        if self.is_neutral:
            self.motor.max_force = 0
            self.motor.rate = 0
            return
        else:
            self.motor.max_force = self.initial_force
            self.motor.rate = self.current_rate

        if is_braking:
            self.target_rate = 0.0

        delta = self.target_rate - self.current_rate

        if abs(delta) < 1e-6:
            self.current_rate = self.target_rate
            return

        # Determine the rate based on the action required:
        if is_braking:
            # 🚨 Case 1: Active Spacebar Braking
            # Highest rate to stop quickly
            rate = self.config.brake_rate

        elif self.current_rate * self.target_rate < 0:
            # 🛑 Case 2: Active Reversing/Hard Braking (Switching direction via arrow keys)
            rate = self.config.brake_rate

        elif self.target_rate == 0.0 and abs(self.current_rate) > 0:
            # 💨 Case 3: Coasting (No arrow key input, moving towards 0)
            rate = self.config.decel_rate

        else:
            # 🚀 Case 4: Acceleration/Holding Speed
            rate = self.config.accel_rate

        # Apply the step change
        step_change = rate * dt

        if delta > 0:
            self.current_rate += min(delta, step_change)
        else:
            self.current_rate += max(delta, -step_change)

        self.motor.rate = self.current_rate


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
        self.motor_rear = MotorController(
            config,
            pymunk.SimpleMotor(self.wheel_r_body, self.chassis_body, 0.0),
            config.wheel_torque,
        )
        self.motor_front = MotorController(
            config,
            pymunk.SimpleMotor(self.wheel_f_body, self.chassis_body, 0.0),
            config.wheel_torque,
        )

        self.chassis_sprite = None
        self.wheel_sprite = None

        chassis_s = pymunk.Poly.create_box(self.chassis_body, config.size)
        chassis_s.friction = config.friction
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
        space.add(self.motor_rear.motor)
        space.add(self.motor_front.motor)

        self.reset_position()
        self.load_sprites()

    def load_sprites(self):
        config = self.config

        dims = pymunk.Vec2d(config.length, config.height)
        self.chassis_sprite = pygame.image.load(config.chassis_sprite_path)
        self.chassis_sprite = pygame.transform.scale(
            self.chassis_sprite.convert_alpha(), list(dims * PX_PER_METER)
        )

        dims = pymunk.Vec2d(config.wheel_diameter, config.wheel_diameter)
        self.wheel_sprite = pygame.image.load(config.wheel_sprite_path)
        self.wheel_sprite = pygame.transform.scale(
            self.wheel_sprite.convert_alpha(), list(dims * PX_PER_METER)
        )

    def draw(self, screen: pygame.Surface, camera: pymunk.Vec2d):
        rotated_image = pygame.transform.rotate(
            self.chassis_sprite, math.degrees(self.chassis_body.angle)
        )
        pos = to_screen_coords(self.chassis_body.position + camera)
        rotated_rect = rotated_image.get_rect(center=pos)
        screen.blit(rotated_image, rotated_rect)

        rotated_image = pygame.transform.rotate(
            self.wheel_sprite, math.degrees(self.wheel_r_body.angle)
        )
        pos = to_screen_coords(self.wheel_r_body.position + camera)
        rotated_rect = rotated_image.get_rect(center=pos)
        screen.blit(rotated_image, rotated_rect)

        rotated_image = pygame.transform.rotate(
            self.wheel_sprite, math.degrees(self.wheel_f_body.angle)
        )
        pos = to_screen_coords(self.wheel_f_body.position + camera)
        rotated_rect = rotated_image.get_rect(center=pos)
        screen.blit(rotated_image, rotated_rect)

    def reset_position(self):
        """Move the truck to a new base position and reset velocities."""
        for body in (self.chassis_body, self.wheel_r_body, self.wheel_f_body):
            body.velocity = (0, 0)
            body.angular_velocity = 0
            body.angle = 0

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
