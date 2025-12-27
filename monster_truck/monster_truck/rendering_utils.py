import math
import pygame
import pymunk
from monster_truck.config import *


def print_time(t: float):
    minutes = int(t // 60)
    seconds = int(t % 60)
    return f"{minutes:02d}:{seconds:02d}"


class SpriteRenderable:
    def __init__(
        self,
        sprite: pygame.Surface,
        size_m: pymunk.Vec2d,
        body: pymunk.Body = None,
        is_world_texture: bool = False,
        world_pos: pymunk.Vec2d = None,
        tile: bool = False,
    ):
        """
        sprite: pygame.Surface
        size_m: size in world meters (width, height)
        body: optional physics body to follow
        is_world_texture: True if this is a world-level texture, not a body sprite
        world_pos: position in world meters (used for world textures)
        tile: if True, tile the texture to fill world size
        """
        self.sprite = sprite
        self.size_m = size_m
        self.body = body
        self.is_world_texture = is_world_texture
        self.world_pos = world_pos or pymunk.Vec2d(0, 0)
        self.tile = tile

        if not is_world_texture and body is not None:
            # Compute pixels per meter from sprite size and world size
            self.sprite_px_per_meter = sprite.get_width() / size_m.x


def load_sprite_for_body(body: pymunk.Body, path: str, size_m: pymunk.Vec2d):
    """Load a sprite attached to a physics body."""
    sprite = pygame.image.load(path).convert_alpha()
    return SpriteRenderable(sprite, size_m, body=body, is_world_texture=False)


def load_level_texture(
    path: str,
    world_size: pymunk.Vec2d,
    world_pos: pymunk.Vec2d = None,
    tile: bool = False,
):
    """
    Load a world-level texture, sized in world meters.
    world_size: desired size in world meters
    world_pos: optional position in world coordinates
    tile: repeat texture to fill the area
    """
    sprite = pygame.image.load(path).convert_alpha()
    return SpriteRenderable(
        sprite,
        world_size,
        body=None,
        is_world_texture=True,
        world_pos=world_pos,
        tile=tile,
    )


class Camera:
    def __init__(
        self,
        screen_dim: tuple[float, float],
        zoom: float = 1.0,
        screen_scale: float = 30,
    ):
        self.screen_w, self.screen_h = screen_dim
        self.screen_center = pymunk.Vec2d(self.screen_w / 2, self.screen_h / 2)
        self.zoom = zoom
        self.screen_scale = screen_scale  # pixels per meter
        self.base_pos = pymunk.Vec2d(0, 0)

    def to_screen_coords(self, world_pos: pymunk.Vec2d):
        rel_pos = world_pos - self.base_pos
        rel_px = rel_pos * self.screen_scale * self.zoom
        return self.screen_center + pymunk.Vec2d(rel_px.x, -rel_px.y)

    def to_screen_px(self, size_m: float):
        return size_m * self.screen_scale * self.zoom


def draw_sprite(screen: pygame.Surface, renderable: SpriteRenderable, camera: Camera):
    if renderable.is_world_texture:
        # Scale world meters → screen pixels
        scale_x = (
            camera.to_screen_px(renderable.size_m.x) / renderable.sprite.get_width()
        )
        scale_y = (
            camera.to_screen_px(renderable.size_m.y) / renderable.sprite.get_height()
        )

        # Apply scaling
        img = pygame.transform.smoothscale(
            renderable.sprite,
            (
                int(renderable.sprite.get_width() * scale_x),
                int(renderable.sprite.get_height() * scale_y),
            ),
        )

        # Position in screen space
        pos = camera.to_screen_coords(renderable.world_pos)

        if renderable.tile:
            # Tile texture to fill size
            tile_cols = math.ceil(
                renderable.size_m.x
                * camera.screen_scale
                * camera.zoom
                / img.get_width()
            )
            tile_rows = math.ceil(
                renderable.size_m.y
                * camera.screen_scale
                * camera.zoom
                / img.get_height()
            )
            for i in range(tile_cols):
                for j in range(tile_rows):
                    tile_pos = pos + pymunk.Vec2d(
                        i * img.get_width(), -j * img.get_height()
                    )
                    screen.blit(img, img.get_rect(topleft=tile_pos))
        else:
            # Draw single texture
            screen.blit(img, img.get_rect(topleft=pos))

    else:
        # Body sprite: scale + rotate
        scale = (camera.screen_scale * camera.zoom) / renderable.sprite_px_per_meter
        angle_deg = math.degrees(renderable.body.angle) if renderable.body else 0
        img = pygame.transform.rotozoom(renderable.sprite, angle_deg, scale)

        pos = camera.to_screen_coords(renderable.body.position)
        screen.blit(img, img.get_rect(center=pos))
