import copy

from pymunk import Vec2d

from monster_truck.configs.interfaces import (
    TruckConfig,
    ChassisConfig,
    WheelConfig,
    SuspensionConfig,
)

CHASSIS = ChassisConfig(
    sprite_path="assets/trucks/truck_1/truck_1_body.png",
    dimensions=Vec2d(4.7, 2.0),
    mass=3500,
    friction=0.15,
)

SUSPENSION = SuspensionConfig(
    uptravel=0.2,
    downtravel=0.6,
    stiffness=70000.0,
    damping=9000.0,
)

WHEEL_R = WheelConfig(
    sprite_path="assets/trucks/truck_1/truck_1_wheel.png",
    radius=0.9,
    mass=600,
    friction=0.75,
    offset=Vec2d(-CHASSIS.dimensions.x / 3, -CHASSIS.dimensions.y / 1.8),
    suspension=SUSPENSION,
)

WHEEL_F = copy.deepcopy(WHEEL_R)
WHEEL_F.offset = Vec2d(CHASSIS.dimensions.x / 3, -CHASSIS.dimensions.y / 1.8)


CONFIG = TruckConfig(
    name="Truck 1",
    chassis=CHASSIS,
    wheel_rear=WHEEL_R,
    wheel_front=WHEEL_F,
    top_speed=25.0,  # m/s
    rolling_resistance=0.3,
    torque=22000,
    brake_torque=35000,
)
