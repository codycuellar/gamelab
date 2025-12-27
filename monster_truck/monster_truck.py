import sys

import pygame

from monster_truck.config import *
from monster_truck.game import Game
from monster_truck.menus import MENU_STATE, main_menu, game_over, pause_screen


pygame.init()


def run_game():
    clock = pygame.time.Clock()

    game = Game(clock)

    menu_font = pygame.font.SysFont("Impact", 25)

    state = MENU_STATE.MAIN_MENU

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return

        if state is MENU_STATE.MAIN_MENU:
            state = main_menu(game.screen, events, menu_font)
            continue
        elif state is MENU_STATE.GAME_OVER:
            state = game_over(game.screen, events, menu_font, game)
            continue
        elif state is MENU_STATE.PAUSE:
            state = pause_screen(game.screen, events, menu_font)
        elif state is MENU_STATE.QUIT:
            running = False
            continue
        elif state is MENU_STATE.START_GAME:
            game = Game(clock)
            state = MENU_STATE.RUN_GAME
        else:
            for e in events:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        state = MENU_STATE.PAUSE
                    if e.key == pygame.K_RETURN:
                        game.reset_truck()

            if state is MENU_STATE.RUN_GAME:
                state = game.step(dt)


if __name__ == "__main__":
    run_game()
    pygame.quit()
    sys.exit()
