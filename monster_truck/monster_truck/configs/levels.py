from pymunk import Vec2d

from monster_truck.configs.interfaces import LevelConfig

LEVELS = [
    LevelConfig(
        name="A 'lil Muddy",
        svg_path="assets/levels/level_1.svg",
        units_per_meter=5,
        samples_per_meter=2,
        ground_friction=1.0,
        gravity=(0, -8.81),
        start_position=Vec2d(230, 440),
        finish_line=3815,
    ),
    LevelConfig(
        name="Hills-n-Gaps",
        svg_path="assets/levels/level_2.svg",
        units_per_meter=5,
        samples_per_meter=2,
        ground_friction=1.2,
        gravity=(0, -6.81),
        start_position=Vec2d(130, 930),
        finish_line=3950,
    ),
]
