import pymunk
from dataclasses import dataclass

FPS = 60.0

DEFAULT_GRAVITY = (0, -9.81)  # meters / s^2

# ---------- Screen / Scale ----------
PX_PER_METER = 30  # how many pixels equal 1 meter
SCREEN_W = 2048  # ~34m
SCREEN_H = 1200  # ~20m


# ---------- Truck Setup ----------
@dataclass
class TruckConfig:
    name: str
    chassis_sprite: str
    wheel_sprite: str
    length: float
    height: float
    mass: float
    friction: float
    top_speed: float
    accel_rate: float
    decel_rate: float
    brake_rate: float
    wheel_radius: float
    wheel_rear_offset: pymunk.Vec2d
    wheel_front_offset: pymunk.Vec2d
    wheel_mass: float
    wheel_friction: float
    max_wheel_speed: float
    wheel_torque: float

    @property
    def size(self):
        return (self.length, self.height)

    @property
    def wheel_diameter(self):
        return self.wheel_radius * 2

    @property
    def chassis_sprite_path(self):
        return f"assets/trucks/{self.chassis_sprite}"

    @property
    def wheel_sprite_path(self):
        return f"assets/trucks/{self.wheel_sprite}"


# Global dict holding all truck configs
TRUCKS: list[TruckConfig] = [
    TruckConfig(
        name="Gravedigger",
        chassis_sprite="truck_1_body.png",
        wheel_sprite="truck_1_wheel.png",
        length=4.7,
        height=2.0,
        mass=500,
        friction=0.32,
        top_speed=26.0,
        accel_rate=26.0 / 3,
        decel_rate=26.0 / 6,
        brake_rate=26.0 / 1.5,
        wheel_radius=0.9,
        wheel_rear_offset=pymunk.Vec2d(-4.7 / 3, -2.0 / 1.4),
        wheel_front_offset=pymunk.Vec2d(4.7 / 3, -2.0 / 1.4),
        wheel_mass=250,
        wheel_friction=0.81,
        max_wheel_speed=26.0,
        wheel_torque=60000,
    ),
    # Add more trucks here...
]

DEFAULT_TRUCK = TRUCKS[0].name


def load_truck_config(name: str) -> TruckConfig:
    for truck in TRUCKS:
        if truck.name == name:
            return truck
    raise ValueError(f"Truck '{name}' not found")


# ---------- World Setup -----------
@dataclass
class LevelConfig:
    name: str
    geometry_filename: str
    geometry_px_per_meter: int
    vehicle_start_position: pymunk.Vec2d
    ground_friction: float
    gravity: float

    @property
    def geometry_filepath(self):
        return f"assets/levels/{self.geometry_filename}"


# Global dict holding all level configs
LEVELS: list[LevelConfig] = [
    LevelConfig(
        name="Mega Mud",
        geometry_filename="level_1_geometry.png",
        geometry_px_per_meter=8,
        vehicle_start_position=pymunk.Vec2d(100, 20),
        ground_friction=1.0,
        gravity=(0, -8.81),
    ),
    # Add more levels here...
]

DEFAULT_LEVEL = LEVELS[0].name


def load_level_config(name: str) -> LevelConfig:
    for lvl in LEVELS:
        if lvl.name == name:
            return lvl
    raise ValueError(f"Level '{name}' not found")
