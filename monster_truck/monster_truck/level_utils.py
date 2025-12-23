from typing import List
from xml.dom import minidom

import pymunk
from svg.path import parse_path, Move, CubicBezier, Line

from monster_truck.config import *


def load_svg_terrain(
    terrain_filepath: str, svg_units_to_meters: float, samples_per_meter: int
):
    doc = minidom.parse(terrain_filepath)
    path_strings = [path.getAttribute("d") for path in doc.getElementsByTagName("path")]
    cmds = parse_path(path_strings[0])
    points: list[pymunk.Vec2d] = []

    def add_point(pt: complex):
        points.append(
            level_px_to_world_pos(pymunk.Vec2d(pt.real, pt.imag), svg_units_to_meters)
        )

    for cmd in cmds:
        if isinstance(cmd, Move):
            # Moves are generally the first point.
            add_point(cmd.point(1.0))
        elif isinstance(cmd, Line):
            add_point(cmd.end)
        elif isinstance(cmd, CubicBezier):
            length = (
                abs(cmd.start - cmd.control1)
                + abs(cmd.control1 - cmd.control2)
                + abs(cmd.control2 - cmd.end)
            ) / svg_units_to_meters
            num_samples = max(2, int(length * samples_per_meter))
            for t in range(1, num_samples):
                t /= num_samples
                add_point(cmd.point(t))
    return points


def level_px_to_world_pos(loc: pymunk.Vec2d, pix_per_meter: int):
    return pymunk.Vec2d(loc.x, -loc.y) / pix_per_meter


def load_level_geometry(
    space: pymunk.Space,
    filepath: str,
    level_units_to_world: float,
    samples_per_world_unit: float,
    friction: float,
):
    points = load_svg_terrain(filepath, level_units_to_world, samples_per_world_unit)
    # add points to physcics Space
    for p1, p2 in zip(points, points[1:]):
        seg = pymunk.Segment(space.static_body, p1, p2, 0.2)
        seg.friction = friction
        space.add(seg)
    return points
