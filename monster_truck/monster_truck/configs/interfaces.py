from dataclasses import dataclass

from pymunk import Vec2d


# ---------- Truck Config Classes ----------
@dataclass
class ChassisConfig:
    sprite_path: str
    dimensions: Vec2d
    mass: float
    friction: float


@dataclass
class SuspensionConfig:
    uptravel: float
    downtravel: float
    stiffness: float
    damping: float


@dataclass
class WheelConfig:
    sprite_path: str
    radius: float
    mass: float
    friction: float
    offset: Vec2d
    suspension: SuspensionConfig

    @property
    def diameter(self):
        return self.radius * 2

    @property
    def dimensions(self):
        diameter = self.diameter
        return Vec2d(diameter, diameter)


@dataclass
class TruckConfig:
    name: str

    chassis: ChassisConfig
    wheel_rear: WheelConfig
    wheel_front: WheelConfig

    top_speed: float  # m/s
    rolling_resistance: float  # coeff/sec

    torque: float  # nm
    brake_torque: float  # nm


# ---------- Level Config Classes ----------
@dataclass
class LevelConfig:
    name: str
    geometry_path: str
    units_per_meter: int
    samples_per_meter: int
    ground_friction: float
    gravity: float
    start_position: Vec2d
    end_flag: Vec2d
