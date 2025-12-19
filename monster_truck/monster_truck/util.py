from monster_truck.config import *


def to_screen_coords(pos):
    """Converts a Pymunk (x, y) position to a Pygame (x_px, y_px) position."""
    x_px = int(pos.x * PX_PER_METER)
    # Apply the flip and offset
    y_px = int(SCREEN_H - (pos.y * PX_PER_METER))
    return x_px, y_px
