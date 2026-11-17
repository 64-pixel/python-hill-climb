import pygame, time, sys, asyncio
from os import listdir
from os.path import isfile, join
import random, math

pygame.init()
pygame.display.set_caption("Hill climb")

BG_COLOR = (255,255,255)
HEIGHT = 800
WIDTH = 800
FPS = 60
ACCELERATION = 0.3
BRAKE_FORCE = 0.15
MAX_SPEED=5

BACKGROUND_DIR = join('textures', 'background')
BACKGROUND_FILES = sorted(f for f in listdir(BACKGROUND_DIR)
                          if isfile(join(BACKGROUND_DIR, f))
                           and f.lower().endswith(".png") )



CONTROLS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT
}

window = pygame.display.set_mode((WIDTH, HEIGHT))

TERRAIN_WIDTH = 50


terrain = []
y=450

for x in range(0,WIDTH + TERRAIN_WIDTH, TERRAIN_WIDTH):
     y += random.randint(-25,25)

     y = max(300, min(y,500))
     terrain.append((x,y))

def generate_terrain_until(end_x):
     while terrain[-1][0] < end_x:
          new_x = terrain[-1][0] + TERRAIN_WIDTH
          new_y = terrain[-1][1] + random.randint(-25, 25)
          new_y = max(300, min(new_y, 500))

          terrain.append((new_x, new_y))


def draw_terrain(window, offset_x):
     points = [(x - offset_x,y) for x,y in terrain]

     pygame.draw.polygon(window,(80,180,70),points + [(WIDTH, HEIGHT), (0, HEIGHT)])

def get_terrain_height(x):
    for i in range(len(terrain) - 1):
          x1,y1 = terrain[i]
          x2,y2 = terrain[i+1]

          if x1 <= x <= x2:
               t = (x-x1) / (x2 - x1)

               return y1 + t * (y2 - y1)
    return HEIGHT

class Car():
    def __init__(self, x,y):
        self.x = x
        self.y = y
        self.speed = 0
        self.gravity = 0.5
        self.y_vel = 0
        self.width = 60
        self.height = 30
        self.angle = 0
        self.wheel_radius = 10
        self.wheel_offset = 12
        self.suspension = 0
        self.suspension_vel = 0

    def draw_wheels(self, window, offset_x):
         rear_x = self.x + self.wheel_offset
         front_x = self.x + self.width - self.wheel_offset

         rear_y = get_terrain_height(rear_x)
         front_y = get_terrain_height(front_x)

         pygame.draw.circle(window, (30,30,30), (int(rear_x) - offset_x, int(rear_y - self.wheel_radius)), self.wheel_radius)

         pygame.draw.circle(window, (30,30,30), (int(front_x) - offset_x, int(front_y - self.wheel_radius)),self.wheel_radius)

    def update_angle(self):
        rear_x = self.x
        front_x = self.x + self.width

        rear_y = get_terrain_height(rear_x)
        front_y = get_terrain_height(front_x)

        self.angle = math.degrees(math.atan2(rear_y - front_y, front_x - rear_x))

    def update(self):
        self.x += self.speed

        rear_x = self.x + self.wheel_offset
        front_x = self.x + self.width - self.wheel_offset

        rear_y = get_terrain_height(rear_x)
        front_y = get_terrain_height(front_x)

        self.angle = math.degrees(math.atan2(rear_y - front_y, front_x - rear_x))

        wheel_y = (rear_y + front_y) /2
        target_y = wheel_y - self.height - self.wheel_radius

        self.y = target_y
        self.suspension_vel = 0

    def handle_controls(self):

        keys = pygame.key.get_pressed()

        if keys[pygame.K_RIGHT]:
             self.speed += ACCELERATION

        if keys[pygame.K_LEFT]:
             self.speed -= BRAKE_FORCE

        self.speed = max(0, min(self.speed, MAX_SPEED))

    def draw(self, window, offset_x):
        screen_x = self.x - offset_x
        car_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        pygame.draw.rect(car_surface, (200,0,0), (0, 0, self.width, self.height))

        rotated_car = pygame.transform.rotate(car_surface, self.angle)

        rect = rotated_car.get_rect(center=(screen_x + self.width /2 , self.y + self.height /2 - 5))

        self.draw_wheels(window, offset_x)

        window.blit(rotated_car, rect)
    
    

def main():
    running = True
    car = Car(100,300)
    keys = pygame.key.get_pressed()
    clock = pygame.time.Clock()

    offset_x = 0
    scroll_area_width = 200

    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        
        car.handle_controls()

        generate_terrain_until(car.x + WIDTH + TERRAIN_WIDTH)

        car.update()

        window.fill((135,206,235))
        draw_terrain(window, offset_x)
        car.draw(window, offset_x)
        height=get_terrain_height(500)
        pygame.draw.circle(window, (255,0,0), (500,int(height)),5)
        pygame.display.update()

        if (car.x - offset_x >= WIDTH - scroll_area_width and car.speed >0):
             offset_x += car.speed

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
         