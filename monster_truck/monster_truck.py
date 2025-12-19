import math
from typing import List

import pygame
import pymunk
import pymunk.pygame_util
import pymunk.autogeometry
from PIL import Image

from monster_truck.config import *
from monster_truck.truck import Truck
from monster_truck.util import Camera

Polyline = List[pymunk.Vec2d]
PolylineSet = List[Polyline]

pygame.init()


def sample_terrain_surface(pixels, w: int, h: int) -> PolylineSet:
    def sampler(xy):
        x, y = xy
        ix = int(max(0, min(w - 1, x)))
        iy = int(max(0, min(h - 1, y)))
        return pixels[ix, iy] / 255.0

    # High-resolution sampling (1 px per sample)
    raw_polylines = pymunk.autogeometry.march_soft(
        pymunk.BB(0, 0, w, h), w, h, 0.5, sampler
    )

    # Ensure each line is treated as a separate polyline
    # (march_soft may return multiple lines as separate lists or just one big list)
    # Here we assume each item is already a continuous polyline
    # If it’s just a flat list, wrap it in another list:
    if all(isinstance(pt, pymunk.Vec2d) for pt in raw_polylines):
        return [raw_polylines]
    else:
        return raw_polylines  # Already a PolylineSet


def level_px_to_world_pos(loc: pymunk.Vec2d, src_height: int, pix_per_meter: int):
    return pymunk.Vec2d(loc.x / pix_per_meter, (src_height - loc.y) / pix_per_meter)


def add_terrain_to_space(
    space: pymunk.Space, sample_points: PolylineSet, friction: float
):
    for polyline in sample_points:
        for p1, p2 in zip(polyline, polyline[1:]):
            seg = pymunk.Segment(space.static_body, p1, p2, 0.2)
            seg.friction = friction
            space.add(seg)


def load_level_geometry(level_config: LevelConfig, space: pymunk.Space):
    terrain_image = Image.open(level_config.geometry_filepath).convert("L")
    tw, th = terrain_image.size
    terrain_pix = terrain_image.load()
    polylines = sample_terrain_surface(terrain_pix, tw, th)
    # convert to world-geometry
    terrain_polylines: list[list[pymunk.Vec2d]] = []
    for polyline in polylines:
        terrain_polylines.append(
            [
                level_px_to_world_pos(pt, th, level_config.geometry_px_per_meter)
                for pt in polyline
            ]
        )

    # Add the polylines as segments into the physics space
    add_terrain_to_space(space, terrain_polylines, level_config.ground_friction)
    truck_pos = level_px_to_world_pos(
        level_config.vehicle_start_position, th, level_config.geometry_px_per_meter
    )
    return terrain_polylines, truck_pos


def run_game():
    dt = 1.0 / FPS

    level_config = load_level_config(DEFAULT_LEVEL)
    truck_config = load_truck_config(DEFAULT_TRUCK)

    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.gravity = level_config.gravity

    terrain_segs, truck_pos = load_level_geometry(level_config, space)
    truck = Truck(truck_config, space, truck_pos)

    camera = Camera((SCREEN_W, SCREEN_H), screen_scale=PX_PER_METER)

    # ---------- Main loop ----------
    while True:
        camera.base_pos = truck.chassis_body.position

        keys = pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return

        if keys[pygame.K_q]:
            truck = Truck(truck_config, space, truck_pos)
            continue

        input_direction = 0
        if keys[pygame.K_RIGHT]:
            input_direction = -1  # Forward
        elif keys[pygame.K_LEFT]:
            input_direction = 1  # Reverse

        is_braking = keys[pygame.K_SPACE]  # New check for spacebar

        truck.motor_front.update_target(input_direction, is_braking)
        truck.motor_rear.update_target(input_direction, is_braking)

        truck.motor_front.step(dt)
        truck.motor_rear.step(dt)

        screen.fill((174, 211, 250))

        truck.draw(screen, camera)
        color = (173, 144, 127)
        for polyline in terrain_segs:
            if len(polyline) < 2:
                continue
            points_px = [camera.to_screen_coords(pt) for pt in polyline]
            pygame.draw.lines(screen, color, False, points_px, 2)

        pygame.display.flip()
        space.step(dt)
        clock.tick(FPS)


if __name__ == "__main__":
    run_game()
    pygame.quit()
