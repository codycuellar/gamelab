import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

from monster_truck.config import *
from monster_truck.game import Game
from monster_truck.rendering_utils import print_time


MENU_BG_COLOR = (220, 247, 247)
MENU_FONT_COLOR = (125, 97, 95)


class MainMenu:
    bg_color = MENU_BG_COLOR
    selector_position = 800

    def __init__(self, screen: Surface):
        self.screen = screen
        self.logo = pygame.image.load("assets/menus/title.png").convert_alpha()
        self.play = pygame.image.load("assets/menus/play.png").convert_alpha()
        self.quit = pygame.image.load("assets/menus/quit.png").convert_alpha()
        self.selector = pygame.image.load("assets/menus/selector.png").convert_alpha()
        self.items = 2
        self.index = 0

    def step(self, events: Event, dt: float):
        self.screen.fill(self.bg_color)
        menu_item_rects = [
            self.play.get_rect(center=(SCREEN_W // 2, 400)),
            self.quit.get_rect(center=(SCREEN_W // 2, 500)),
        ]
        self.screen.blit(self.logo, self.logo.get_rect(center=(SCREEN_W // 2, 200)))

        self.screen.blit(self.play, menu_item_rects[0])
        self.screen.blit(self.quit, menu_item_rects[1])

        selector_rect = self.selector.get_rect()
        selector_rect.center = (
            menu_item_rects[self.index].left - (selector_rect.width),
            menu_item_rects[self.index].centery,
        )
        self.screen.blit(self.selector, selector_rect)

        pygame.display.flip()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    self.index = (self.index - 1) % self.items
                elif e.key == pygame.K_DOWN:
                    self.index = (self.index + 1) % self.items
                elif e.key == pygame.K_RETURN:
                    if self.index == 0:
                        return MENU_STATE.LEVEL_SELECT
                    else:
                        return MENU_STATE.QUIT

        return MENU_STATE.MAIN_MENU


class LevelSelectMenu:
    bg_color = MENU_BG_COLOR
    selector_position = 600

    def __init__(self, screen: Surface):
        self.screen = screen
        self.title = pygame.image.load("assets/menus/select_level.png").convert_alpha()
        self.level_1 = pygame.image.load("assets/menus/level_1.png").convert_alpha()
        self.level_2 = pygame.image.load("assets/menus/level_2.png").convert_alpha()
        self.selector = pygame.image.load("assets/menus/selector.png").convert_alpha()
        self.items = 2
        self.index = 0

    def step(self, events: Event, game: Game, dt: float):
        self.screen.fill(self.bg_color)
        menu_item_rects = [
            self.level_1.get_rect(center=(SCREEN_W // 2, 400)),
            self.level_2.get_rect(center=(SCREEN_W // 2, 500)),
        ]
        self.screen.blit(self.title, self.title.get_rect(center=(SCREEN_W // 2, 200)))

        self.screen.blit(self.level_1, menu_item_rects[0])
        self.screen.blit(self.level_2, menu_item_rects[1])

        selector_rect = self.selector.get_rect()
        selector_rect.center = (
            menu_item_rects[self.index].left - (selector_rect.width),
            menu_item_rects[self.index].centery,
        )
        self.screen.blit(self.selector, selector_rect)

        pygame.display.flip()

        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    self.index = (self.index - 1) % self.items
                elif e.key == pygame.K_DOWN:
                    self.index = (self.index + 1) % self.items
                elif e.key == pygame.K_RETURN:
                    game.level_config = load_level_config(self.index)
                    return MENU_STATE.START_GAME
                elif e.key == pygame.K_ESCAPE:
                    return MENU_STATE.MAIN_MENU

        return MENU_STATE.LEVEL_SELECT


def game_over(screen: Surface, events: list[Event], font: Font, game: Game):
    screen.fill(MENU_BG_COLOR)
    text = font.render(
        f"Level Complete! Your time: {print_time(game.level_time)}",
        True,
        MENU_FONT_COLOR,
    )
    text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
    screen.blit(text, text_rect)

    text = font.render(f"Press spacebar to try again!", True, MENU_FONT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 30))
    screen.blit(text, text_rect)
    pygame.display.flip()

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                return MENU_STATE.START_GAME
            if e.key == pygame.K_ESCAPE:
                return MENU_STATE.MAIN_MENU

    return MENU_STATE.GAME_OVER


def pause_screen(screen: Surface, events: list[Event], font: Font):
    screen.fill(MENU_BG_COLOR)
    text = font.render(
        f"Game paused, press spacebar to resume, or escape to exit to main menu.",
        True,
        MENU_FONT_COLOR,
    )
    text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                return MENU_STATE.MAIN_MENU
            elif e.key == pygame.K_SPACE:
                return MENU_STATE.RUN_GAME

    return MENU_STATE.PAUSE
