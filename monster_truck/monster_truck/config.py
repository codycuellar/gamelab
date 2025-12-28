from enum import Enum

from monster_truck.configs.interfaces import TruckConfig, LevelConfig
from monster_truck.configs.trucks import TRUCKS
from monster_truck.configs.levels import LEVELS


class MENU_STATE(Enum):
    MAIN_MENU = 2
    LEVEL_SELECT = 3
    TRUCK_SELECT = 4
    GAME_OVER = 5
    PAUSE = 6
    START_GAME = 100
    RUN_GAME = 110
    QUIT = 300


# ---------- GAME DEFAULTS ----------
FPS = 60
PX_PER_METER = 20  # how many pixels equal 1 meter
SCREEN_W = 2048  # ~34m
SCREEN_H = 1200  # ~20m


def load_truck_config(name: str | None = None) -> TruckConfig:
    if name is None:
        return TRUCKS[0]

    for truck in TRUCKS:
        if truck.name == name:
            return truck
    raise ValueError(f"Truck '{name}' not found")


def load_level_config(item: int = 0) -> LevelConfig:
    return LEVELS[item]
