import pygame
from pygame import Surface
from pygame.event import Event
from pygame.font import Font

from monster_truck.config import *
from monster_truck.game import Game
from monster_truck.rendering_utils import print_time


MENU_BG_COLOR = (220, 247, 247)
MENU_FONT_COLOR = (125, 97, 95)


def main_menu(screen: Surface, events: list[Event], font: Font):
    screen.fill(MENU_BG_COLOR)
    text = font.render(
        f"Press spacebar to start the game! Q to Quit.",
        True,
        MENU_FONT_COLOR,
    )
    text_rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

    for e in events:
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_SPACE:
                return MENU_STATE.START_GAME
            elif e.key == pygame.K_q:
                return MENU_STATE.QUIT

    return MENU_STATE.MAIN_MENU


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
