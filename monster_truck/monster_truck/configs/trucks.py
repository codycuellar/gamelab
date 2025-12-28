import copy

from pymunk import Vec2d

from monster_truck.configs.interfaces import (
    TruckConfig,
    ChassisConfig,
    WheelConfig,
    SuspensionConfig,
)


def truck_1():
    chassis = ChassisConfig(
        sprite_path="assets/trucks/truck_1/truck_1_body.png",
        dimensions=Vec2d(4.7, 2.0),
        mass=3500,
        friction=0.15,
    )

    suspension = SuspensionConfig(
        uptravel=0.2,
        downtravel=0.6,
        stiffness=70000.0,
        damping=9000.0,
    )

    wheel_r = WheelConfig(
        sprite_path="assets/trucks/truck_1/truck_1_wheel.png",
        radius=0.9,
        mass=600,
        friction=0.75,
        offset=Vec2d(-chassis.dimensions.x / 3, -chassis.dimensions.y / 1.8),
        suspension=suspension,
    )

    wheel_f = copy.deepcopy(wheel_r)
    wheel_f.offset = Vec2d(chassis.dimensions.x / 3, -chassis.dimensions.y / 1.8)

    return TruckConfig(
        name="Simple Green™",
        chassis=chassis,
        wheel_rear=wheel_r,
        wheel_front=wheel_f,
        top_speed=25.0,  # m/s
        rolling_resistance=0.3,
        torque=22000,
        brake_torque=35000,
    )


TRUCKS = [
    truck_1(),
]
