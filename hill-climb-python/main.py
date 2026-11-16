import pygame, time, sys, asyncio
from os import listdir
from os.path import isfile, join

pygame.init()
pygame.display.set_caption("Hill climb")

BG_COLOR = (255,255,255)
HEIGHT = 1000
WIDTH = 1000
FPS = 60
PLAYER_VEL = 4

BACKGROUND_DIR = join('models', 'background')
BACKGROUND_FILES = sorted(f for f in listdir(BACKGROUND_DIR)
                          if isfile(join(BACKGROUND_DIR, f))
                           and f.lower().endswith(".png") )

selected_background = (
    "background.png"
    if "background.png" in BACKGROUND_FILES
    else BACKGROUND_FILES[0]
)

CONTROLS = (
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT
)

window = pygame.display.set_mode((WIDTH, HEIGHT))




def main():
    None