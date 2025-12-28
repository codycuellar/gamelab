from xml.dom import minidom

from pymunk import Vec2d, Space, Segment
from svg.path import parse_path, Move, CubicBezier, Line

from monster_truck.config import *


def load_svg(filepath: str):
    """
    Load a filepath, and parse the SVG paths command strings.

    Args:
        filepath:  The path to the SVG file.

    Returns:
        The path command strings. This is an array of N paths
        for each non-contiguous path shape in the SVG file.
    """
    doc = minidom.parse(filepath)
    return [path.getAttribute("d") for path in doc.getElementsByTagName("path")]


def sample_paths(
    paths: list[str],
    level_to_world_units: float,
    samples_per_world_unit: int,
):
    """
    Sample SVG path strings into lerped coordinates. This will approximate
    the curves length and take N number of samples to get close to the target
    samples_per_world_unit. Currently we only support one contiguous vector,
    so only the first path will be parsed and converted to points.

    Args:
        paths: The array of individual path strings to sample.
        level_to_world_units:
            The number of input file units per world unit. For instance, if 10
            pixels in the level design dimensions is meant to represent 1 world
            meter, this value would be 10, and we would divide all realtive point
            values by 10.
        samples_per_world_unit:
            Once converted to world units, such as meters, this determines how
            many samples to take between two curve endpoints to approximate
            this value. So a value of 1 here will take 10 sample points if the
            approximate length of the curve is 10 world units.

    Returns:
        The array of sampled points in world-relative units.
    """
    # currently we only support a single contiguous vector path.
    cmds = parse_path(paths[0])
    points: list[Vec2d] = []

    def add_point(pt: complex):
        points.append(
            level_units_to_world(Vec2d(pt.real, pt.imag), level_to_world_units)
        )

    # Iterate the point commands. Each iteration we add all the points up to the endpoint,
    # so on subsequent calls, we don't add the start point as it was already captured in the
    # previous iteration.
    for cmd in cmds:
        if isinstance(cmd, Move):
            # Moves are generally the first point, if we want to support noncontiguous ground
            # surfaces, we'll need to create a list of lists, and add new parent lists anytime
            # we get to a new move command.
            add_point(cmd.point(1.0))
        elif isinstance(cmd, Line):
            # Add the endpoint for straight line segments.
            add_point(cmd.end)
        elif isinstance(cmd, CubicBezier):
            # here we get the previous point, the next two control points and the end point
            # to lerp the cubic bez. We'll approximate the segment length to determine how many
            # points to sample based on our samples_per_world_unit.
            length = (
                abs(cmd.start - cmd.control1)
                + abs(cmd.control1 - cmd.control2)
                + abs(cmd.control2 - cmd.end)
            ) / level_to_world_units
            num_samples = max(2, int(length * samples_per_world_unit))
            # skip 0 since that's the start point added in the last loop
            for t in range(1, num_samples):
                t /= num_samples
                add_point(cmd.point(t))
    return points


def level_units_to_world(position: Vec2d | float, level_to_world_units: float):
    """
    Convert coordinates in level design space to world relative units. This
    scales the values and flips the Y-axis, since input files are +Y down, and
    physics world is +Y up.

    Args:
        position: The position vector to convert.
        level_to_world_units:
            The number of relative level design units per one world unit.

    Returns:
        The converted world relative position.
    """
    return Vec2d(position.x, -position.y) / level_to_world_units


def load_level_geometry_from_svg(
    space: Space,
    filepath: str,
    level_units_to_world: float,
    samples_per_world_unit: float,
    friction: float,
):
    """
    Load an SVG and sample it into world relative coordiantes. It then adds
    individual segments between each sampled point into the physics engine.

    Args:
        space: The physics space to add the sampled segments to.
        filepath: The SVG file to load.
        level_units_to_world:
            The number of level document relative units per world unit.
        samples_per_world_unit:
            The target approximate distance for each sampled point in world
            relative units.
        friction: The friction coefficient of the terrain geometry.

    Returns:
        The raw sampled points as world relative coordinates.
    """
    paths = load_svg(filepath)
    # load the SVG and lerp the points based on samples_per_world_unit
    points = sample_paths(paths, level_units_to_world, samples_per_world_unit)
    # add points to physcics Space
    for p1, p2 in zip(points, points[1:]):
        seg = Segment(space.static_body, p1, p2, 0.2)
        seg.friction = friction
        space.add(seg)
    return points
