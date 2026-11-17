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


def flip(sprites):
    return [
        pygame.transform.flip(sprite, True, False)
        for sprite in sprites
    ]
def load_sprite_sheets(
    dir1, dir2, width, height, direction=False
):
    path = join("textures and art", dir1, dir2)

    images = [
        f for f in listdir(path)
        if isfile(join(path, f)) and f.lower().endswith(".png")
    ]

    all_sprites = {}

    for image in images:
        sprite_sheet = pygame.image.load(
            join(path, image)
        ).convert_alpha()

        sprites = []

        for i in range(sprite_sheet.get_width() // width):
            surface = pygame.Surface(
                (width, height), pygame.SRCALPHA, 32
            )

            rect = pygame.Rect(i * width, 0, width, height)
            surface.blit(sprite_sheet, (0, 0), rect)

            sprites.append(pygame.transform.scale2x(surface))

        name = image[:-4]

        if direction:
            all_sprites[name + "_right"] = sprites
            all_sprites[name + "_left"] = flip(sprites)
        else:
            all_sprites[name] = sprites

    return all_sprites


def main():
    None