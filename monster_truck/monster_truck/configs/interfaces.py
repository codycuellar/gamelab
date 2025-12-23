from dataclasses import dataclass

from pymunk import Vec2d


# ---------- Truck Config Classes ----------
@dataclass
class ChassisConfig:
    """
    Configuration for a truck chassis.

    Attributes:
        sprite_path: The path to the chassis sprite image.
        dimensions: (meters) The dimensions of the chassis.
        mass: (Kg) The mass of the chassis.
        friciton:
            The friction coefficient of the chassis when it collides with
            objects and the ground surfaces.
    """

    sprite_path: str
    dimensions: Vec2d
    mass: float
    friction: float


# TODO: Since the ride height is actually determined by the spring stiffness,
# we probably don't need to specify both uptravel and downtravel, we could
# instead provide the initial wheel offsets as the max uptravel position,
# and just specify the downtravel in the suspension config.
@dataclass
class SuspensionConfig:
    """
    Configuration for an individual axle suspension.

    Attributes:
        uptravel:
            (meters) The distance from the wheel base position that the axle can
            travel upwards.
        downtravel:
            (meters) The distance from the wheel base position that the axle can
            travel downwards.
        stiffness: The spring stiffness to set vehicle ride-height.
        damping: The damping coefficient of the shocks.
    """

    uptravel: float
    downtravel: float
    stiffness: float
    damping: float


@dataclass
class WheelConfig:
    """
    The config for a wheel (technically both wheels on the axle when
    considering
    things like mass).

    Attributes:
        sprite_path: The path to the wheel sprite image.
        radius: (meters) The radius of the wheel in meters.
        mass: (Kg) The mass of entire axle and both wheels.
        friction:
            Friction coefficient of the wheel when colliding with objects or
            ground surface.
        offset: (meters) The
        suspension: SuspensionConfig
    """

    sprite_path: str
    radius: float
    mass: float
    friction: float
    offset: Vec2d
    suspension: SuspensionConfig

    @property
    def diameter(self):
        """The calculated diameter of the wheel."""
        return self.radius * 2

    @property
    def dimensions(self):
        """The x/y dimensions of the wheel."""
        diameter = self.diameter
        return Vec2d(diameter, diameter)


@dataclass
class TruckConfig:
    """
    Configuration for an entire truck.

    Attributes:
        name: The name of the truck. to appear in the truck selector.
        chassis: The chassis config.
        wheel_rear: The rear wheel config.
        wheel_front:
            The front wheel config, currently must match size of rear wheel,
            since the driveline is 4WD.
        top_speed: (m/s) The target top speed of the truck.
        rolling_resistance: (coeff) A coefficient of angular velocity to
        torque:
            (Nm) The amount of torque applied to each axle. Since the two axles
            are geared together they will both always receive the same torque.
        brake_torque: (Nm) The amount of braking force torque.
    """

    name: str
    chassis: ChassisConfig
    wheel_rear: WheelConfig
    wheel_front: WheelConfig
    top_speed: float
    rolling_resistance: float
    torque: float
    brake_torque: float


# ---------- Level Config Classes ----------
# TODO: Things like ground friction and gravity should be an array of tuples
# such as (start, end, gravity), or (start, end, color, friciton) for properties
# that we want to be able to specify more isolated world sections with different
# frictions or gravities.
@dataclass
class LevelConfig:
    """
    The config for a single level.

    Attributes:
        name: The name of the level to appear in the level selector.
        svg_path: The path to the svg file defining the level geometry.
        units_per_meter:
            The number of SVG document relative units per world meter.
        samples_per_meter:
            The target number of samples to take when lerping the terrain points
            in meters.
        ground_friction: (coeff) The friction coefficient of the ground.
        gravity: (m/s^2) The world gravity.
        start_position:
            The level SVG relative x/y coordinates to start the truck on.
        finish_line:
            The level SVG relative x coordinate the truck must pass to complete
            the level.
    """

    name: str
    svg_path: str
    units_per_meter: int
    samples_per_meter: int
    ground_friction: float
    gravity: float
    start_position: Vec2d
    finish_line: float
