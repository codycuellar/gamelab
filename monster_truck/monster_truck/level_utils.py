from typing import List
from xml.dom import minidom

import pymunk
import pymunk.autogeometry
from PIL import Image
from svg.path import parse_path, Move, CubicBezier, Line


from monster_truck.config import *

Polyline = List[pymunk.Vec2d]
PolylineSet = List[Polyline]


def load_svg_terrain(
    terrain_filepath: str, svg_units_to_meters: float, samples_per_meter: int
):
    doc = minidom.parse(terrain_filepath)
    path_strings = [path.getAttribute("d") for path in doc.getElementsByTagName("path")]
    cmds = parse_path(path_strings[0])
    points: list[pymunk.Vec2d] = []

    def add_point(pt: pymunk.Vec2d):
        points.append(pymunk.Vec2d(pt.x, -pt.y))

    for cmd in cmds:
        if isinstance(cmd, Move):
            pt = cmd.point(1.0) / svg_units_to_meters
            add_point(pymunk.Vec2d(pt.real, pt.imag))
        elif isinstance(cmd, Line):
            pt = cmd.end / svg_units_to_meters
            add_point(pymunk.Vec2d(pt.real, pt.imag))
        elif isinstance(cmd, CubicBezier):
            length = (
                abs(cmd.start - cmd.control1)
                + abs(cmd.control1 - cmd.control2)
                + abs(cmd.control2 - cmd.end)
            ) / svg_units_to_meters
            num_samples = max(2, int(length * samples_per_meter))
            for t in range(1, num_samples):
                t /= num_samples
                pt = cmd.point(t) / svg_units_to_meters
                add_point(pymunk.Vec2d(pt.real, pt.imag))
    return points


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
    space: pymunk.Space, sample_points: list[pymunk.Vec2d], friction: float
):
    for p1, p2 in zip(sample_points, sample_points[1:]):
        seg = pymunk.Segment(space.static_body, p1, p2, 0.2)
        seg.friction = friction
        space.add(seg)


def load_level_geometry(level_config: LevelConfig, space: pymunk.Space):
    points = load_svg_terrain(
        level_config.geometry_filepath,
        level_config.units_per_meter,
        level_config.samples_per_meter,
    )
    # Add the polylines as segments into the physics space
    add_terrain_to_space(space, points, level_config.ground_friction)

    return points
