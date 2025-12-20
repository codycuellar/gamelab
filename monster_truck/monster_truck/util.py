import math
import pygame
import pymunk
from monster_truck.config import *


def load_sprite_for_body(body: pymunk.Body, path: str, scale: float):
    """
    Loads a sprite and returns a SpriteRenderable attached to a Pymunk body.

    body: pymunk.Body to attach to
    path: file path to the sprite
    scale: physics dimensions in meters (width, height)
    """
    sprite = pygame.image.load(path).convert_alpha()
    return SpriteRenderable(body, sprite, scale)


class SpriteRenderable:
    def __init__(self, body: pymunk.Body, sprite: pygame.Surface, scale: float):
        self.body = body
        self.sprite = sprite
        self.scale = scale
        self.sprite_px_per_meter = sprite.get_size()[0] / scale


class Camera:
    def __init__(self, screen_dim: tuple[float], zoom=1.0, screen_scale=30):
        self.screen_w, self.screen_h = screen_dim
        self.screen_center = pymunk.Vec2d(self.screen_w / 2, self.screen_h / 2)
        self.zoom = zoom
        self.screen_scale = screen_scale
        self.base_pos = pymunk.Vec2d(0, 0)

    def to_screen_coords(self, world_pos):
        rel_pos = world_pos - self.base_pos
        rel_pos_px = rel_pos * self.screen_scale * self.zoom
        return self.screen_center + pymunk.Vec2d(rel_pos_px.x, -rel_pos_px.y)

    def to_screen_px(self, size: float):
        return size * self.screen_scale * self.zoom


def draw_sprite(screen: pygame.Surface, renderable: SpriteRenderable, camera: Camera):
    sprite_w_px, _ = renderable.sprite.get_size()
    # pixels per meter on screen / pixels per meter in sprite
    scale = (camera.screen_scale * camera.zoom) / renderable.sprite_px_per_meter

    img = pygame.transform.rotozoom(
        renderable.sprite, math.degrees(renderable.body.angle), scale
    )

    pos = camera.to_screen_coords(renderable.body.position)
    screen.blit(img, img.get_rect(center=pos))
