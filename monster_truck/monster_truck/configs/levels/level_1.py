from pymunk import Vec2d

from monster_truck.configs.interfaces import LevelConfig


CONFIG = LevelConfig(
    name="Mega Mud",
    svg_path="assets/levels/level_1.svg",
    units_per_meter=5,
    samples_per_meter=2,
    ground_friction=1.0,
    gravity=(0, -8.81),
    start_position=Vec2d(230, 440),
    # finish_line=3815,
    finish_line=400,
)
