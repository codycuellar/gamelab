import pymunk
from dataclasses import dataclass

FPS = 60

DEFAULT_GRAVITY = (0, -9.81)  # meters / s^2

# ---------- Screen / Scale ----------
PX_PER_METER = 20  # how many pixels equal 1 meter
SCREEN_W = 2048  # ~34m
SCREEN_H = 1200  # ~20m


# ---------- Truck Setup ----------
@dataclass
class TruckConfig:
    name: str
    chassis_sprite: str
    wheel_sprite: str
    length: float  # meters
    height: float  # meters
    mass: float  # Kg
    body_friction: float  # friction coeff
    top_speed: float  # m/s
    wheel_radius: float  # meters
    wheel_rear_offset: pymunk.Vec2d  # meters
    wheel_front_offset: pymunk.Vec2d  # meters
    wheel_mass: float  # Kg
    wheel_friction: float  # friction coeff
    rolling_resistance: float  # coeff/sec
    wheel_torque: float  # nm
    brake_torque: float  # nm
    suspension_uptravel: float  # meters
    suspension_downtravel: float  # meters
    suspension_spring_stiffness: float
    suspension_damping: float

    @property
    def dimensions(self):
        return pymunk.Vec2d(self.length, self.height)

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
        length=4.7,  # meters
        height=2.0,  # meters
        mass=3500,
        body_friction=0.15,
        top_speed=25.0,  # m/s
        wheel_radius=0.9,
        wheel_rear_offset=pymunk.Vec2d(-4.7 / 3, -2.0 / 1.8),
        wheel_front_offset=pymunk.Vec2d(4.7 / 3, -2.0 / 1.8),
        wheel_mass=600,  # two wheels on axle
        wheel_friction=0.75,
        rolling_resistance=0.1,
        wheel_torque=22000,
        brake_torque=35000,
        suspension_uptravel=0.2,  # meters
        suspension_downtravel=0.6,  # meters
        suspension_spring_stiffness=70000.0,
        suspension_damping=9000.0,
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
    units_per_meter: int
    samples_per_meter: int
    ground_friction: float
    gravity: float

    @property
    def geometry_filepath(self):
        return f"assets/levels/{self.geometry_filename}"


# Global dict holding all level configs
LEVELS: list[LevelConfig] = [
    LevelConfig(
        name="Mega Mud",
        geometry_filename="level_1.svg",
        units_per_meter=5,
        samples_per_meter=2,
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
