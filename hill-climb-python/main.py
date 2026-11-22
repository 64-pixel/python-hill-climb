import pygame, sys, math, random, json, os, wave
from array import array
import numpy as np
# /// script
# dependencies = ["numpy"]
# ///
import asyncio

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()
pygame.display.set_caption("Hill Climb")

WIDTH = 960
HEIGHT = 600
FPS = 60

window = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hill_climb_save.json")


FONT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "font.ttf")


UNLOCK_ALL_LEVELS = True

SR = 44100

STEP = 1 / 240          
START_X = 200
PX_PER_M = 40.0         
GRAVITY = 1100.0

BODY_W = 78
BODY_H = 26
INERTIA = 1300.0

WHEEL_R = 15
WHEEL_X = 28
MOUNT_Y = 8
REST_LEN = 16
TRAVEL = 16
SUSP_K = 95.0
SUSP_C = 11.0
BUMP_K = 1400.0

ENGINE = 560.0
MAX_SPEED = 520.0
BRAKE = 700.0
REVERSE = 300.0
MAX_REVERSE = 220.0
ROLL_DAMP = 0.25
GRIP = 1.4

AIR_TORQUE = 9.0
ANG_DAMP = 0.8

BODY_K = 4000.0
BODY_C = 60.0


HEAD_X = -2
HEAD_Y = -BODY_H / 2 - 6
HEAD_R = 9

FUEL_MAX = 100.0
FUEL_DRAIN = 3.0
FUEL_GAS_DRAIN = 5.0
FUEL_PICKUP = 40.0
PICKUP_RADIUS = 48

END_DELAY = 1.2

LEVELS = [
    {"name": "MEADOW", "goal": 300, "amp": 0.45, "gap": (1200, 1800),
     "sky": (135, 206, 235), "grass": (80, 185, 70), "grass_dark": (55, 150, 50),
     "dirt": (120, 80, 45), "dirt_dark": (100, 65, 35),
     "hill1": (130, 175, 150), "hill2": (105, 160, 110)},
    {"name": "HILLS", "goal": 500, "amp": 0.70, "gap": (1300, 2000),
     "sky": (150, 205, 235), "grass": (95, 170, 60), "grass_dark": (65, 130, 40),
     "dirt": (115, 85, 50), "dirt_dark": (95, 68, 38),
     "hill1": (120, 165, 140), "hill2": (90, 140, 95)},
    {"name": "DESERT", "goal": 700, "amp": 0.80, "gap": (1400, 2100),
     "sky": (245, 205, 150), "grass": (232, 196, 110), "grass_dark": (205, 165, 80),
     "dirt": (200, 145, 80), "dirt_dark": (175, 120, 60),
     "hill1": (225, 170, 120), "hill2": (205, 145, 95)},
    {"name": "SNOW", "goal": 900, "amp": 0.90, "gap": (1400, 2200),
     "sky": (180, 208, 232), "grass": (245, 248, 252), "grass_dark": (200, 210, 225),
     "dirt": (130, 140, 160), "dirt_dark": (105, 115, 138),
     "hill1": (200, 215, 235), "hill2": (165, 185, 215)},
    {"name": "MOUNTAIN", "goal": 1200, "amp": 1.00, "gap": (1500, 2300),
     "sky": (120, 130, 175), "grass": (110, 145, 90), "grass_dark": (80, 110, 65),
     "dirt": (95, 82, 85), "dirt_dark": (75, 65, 70),
     "hill1": (95, 100, 145), "hill2": (75, 85, 120)},
]

CAR_COLORS = [
    ("RED", (205, 30, 30)),
    ("BLUE", (45, 100, 230)),
    ("GREEN", (45, 165, 65)),
    ("YELLOW", (240, 205, 35)),
    ("ORANGE", (245, 135, 25)),
    ("PURPLE", (145, 65, 195)),
    ("PINK", (245, 115, 175)),
    ("WHITE", (235, 235, 235)),
    ("BLACK", (55, 55, 60)),
]


MENU_BG = (151, 139, 56)
MENU_HILLS = (137, 126, 50)
BTN_BG = (117, 108, 72)
BTN_BG_SEL = (92, 85, 55)
BTN_TEXT = (216, 255, 216)
BTN_TEXT_DIM = (150, 150, 110)
TITLE_COLOR = (204, 226, 20)
TITLE_SHADOW = (110, 100, 30)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def square(freq, seconds, vol=0.1):
    t=np.arange(int(SR* seconds)) / SR
    sq = np.sign(np.sin(2*np.pi * freq * t))
    fade = np.exp(-t*6)
    return sq * fade * vol

def noise(seconds, vol=0.3):
    t=np.arange(int(SR * seconds)) / SR
    hiss = np.random.uniform(-1,1, len(t))
    return hiss * np.exp(-t*8) * vol

def gap(seconds):
    return np.zeros(int(SR * seconds))


save = {"volume": 0.7, "car_color": 0, "unlocked": 1, "best": {}, "music":True}


def load_save():
    global save
    try:
        f = open(SAVE_FILE)
        data = json.load(f)
        f.close()
        save["volume"] = clamp(float(data["volume"]), 0.0, 1.0)
        save["car_color"] = int(data["car_color"]) % len(CAR_COLORS)
        save["unlocked"] = clamp(int(data["unlocked"]), 1, len(LEVELS))
        save["best"] = dict(data["best"])
        save["music"] = bool(data.get("music", True))
    except Exception:
        pass   


def write_save():
    try:
        f = open(SAVE_FILE, "w")
        json.dump(save, f)
        f.close()
    except Exception:
        pass



base_font = None


def pixel_text(text, scale, color):

    global base_font
    if base_font is None:
        if os.path.exists(FONT_FILE):
            base_font = pygame.font.Font(FONT_FILE, 8)
        else:
            base_font = pygame.font.Font(None, 16)
            base_font.set_bold(True)
    img = base_font.render(text, False, color).convert_alpha()
    return pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))


hint_font = None


def draw_hint(text, x, y):
    global hint_font
    if hint_font is None:
        hint_font = pygame.font.Font(None, 24)
    window.blit(hint_font.render(text, True, (40, 40, 40)), (x, y))





level = LEVELS[0]
phase = [0, 0, 0, 0]


def get_height(x):
    t = clamp((x - 350) / 3500, 0.0, 1.0)
    d = t * t * (3 - 2 * t) * level["amp"]     
    y = (220 * math.sin(x / 1000 + phase[0])
         + 110 * math.sin(x / 280 + phase[1])
         + 35 * math.sin(x / 110 + phase[2])
         + 8 * math.sin(x / 34 + phase[3]))
    return 500 + d * y


def get_normal(x, w):
   
    s = (get_height(x + w) - get_height(x - w)) / (2 * w)
    inv = 1.0 / math.sqrt(1 + s * s)
    return pygame.Vector2(s, -1) * inv, pygame.Vector2(1, s) * inv, inv


def draw_terrain(cam_x, cam_y):
    top = []
    for sx in range(-10, WIDTH + 20, 10):
        top.append((sx, get_height(cam_x + sx) - cam_y))

    bottom_y = max(p[1] for p in top) + 600
    pygame.draw.polygon(window, level["dirt"], top + [(WIDTH + 10, bottom_y), (-10, bottom_y)])

    band = [(p[0], p[1] + 40) for p in top]
    pygame.draw.polygon(window, level["dirt_dark"], band + [(WIDTH + 10, bottom_y), (-10, bottom_y)])

    grass = top + [(p[0], p[1] + 16) for p in reversed(top)]
    pygame.draw.polygon(window, level["grass"], grass)
    pygame.draw.lines(window, level["grass_dark"], False, top, 3)


def draw_background(cam_x, cam_y):
    window.fill(level["sky"])

   
    for k in range(8):
        cx = (k * 420 - cam_x * 0.15) % (WIDTH + 400) - 200
        cy = 70 + (k * 53) % 130
        for dx, dy, r in ((0, 0, 26), (28, 8, 20), (-28, 8, 20), (8, -12, 22)):
            pygame.draw.circle(window, (250, 250, 255), (int(cx + dx), int(cy + dy)), r)

class Car:

    def __init__(self, x, y, color):
        self.color = color
        self.start_x = x
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0.0
        self.omega = 0.0
        self.crashed = False
        self.on_ground = False

        self.fuel = FUEL_MAX
        self.stall_time = 0.0
        self.stalled = False

        self.mounts = [pygame.Vector2(-WHEEL_X, MOUNT_Y), pygame.Vector2(WHEEL_X, MOUNT_Y)]
        self.comp_vis = [5.0, 5.0]
        self.spin = [0.0, 0.0]
        self.spin_speed = [0.0, 0.0]

        self.force = pygame.Vector2()
        self.torque = 0.0

    def rotate(self, v):
        c = math.cos(self.angle)
        s = math.sin(self.angle)
        return pygame.Vector2(v.x * c - v.y * s, v.x * s + v.y * c)

    def to_world(self, local):
        return self.pos + self.rotate(local)

    def point_velocity(self, p):
        r = p - self.pos
        return self.vel + self.omega * pygame.Vector2(-r.y, r.x)

    def add_force(self, f, point):
        r = point - self.pos
        self.force += f
        self.torque += r.x * f.y - r.y * f.x

    def wheel_center(self, i):
        down = self.rotate(pygame.Vector2(0, 1))
        return self.to_world(self.mounts[i]) + down * (REST_LEN - self.comp_vis[i])

    def distance(self):
        return max(0.0, (self.pos.x - self.start_x) / PX_PER_M)

    def wheel_physics(self, i, gas, brake):
        
        down = self.rotate(pygame.Vector2(0, 1))
        rc = self.to_world(self.mounts[i]) + down * REST_LEN

        
        pen = -1e9
        for k in range(-4, 5):
            phi = math.radians(k * 15)
            px = rc.x + WHEEL_R * math.sin(phi)
            py = rc.y + WHEEL_R * math.cos(phi)
            pen = max(pen, py - get_height(px))

        n, t, inv = get_normal(rc.x, WHEEL_R * 0.9)
        comp = pen * inv

        target = clamp(comp, -6.0, TRAVEL)
        self.comp_vis[i] += (target - self.comp_vis[i]) * 0.5

        if comp <= 0:
            return False

        v = self.point_velocity(rc)
        comp_rate = -v.dot(n)

        N = SUSP_K * comp + SUSP_C * comp_rate
        if comp > TRAVEL:
            N += BUMP_K * (comp - TRAVEL)
        N = clamp(N, 0.0, 8000.0)

      
        vt = v.dot(t)
        if gas:
            f = clamp(ENGINE * (1 - vt / MAX_SPEED), 0.0, ENGINE * 1.5)
        elif brake:
            if vt > 20:
                f = -min(BRAKE, vt * 20)
            else:
                f = -REVERSE * max(0.0, 1 + vt / MAX_REVERSE)
        else:
            f = -vt * ROLL_DAMP
        f = clamp(f, -GRIP * N, GRIP * N)

        self.add_force(n * N + t * f, rc)
        self.spin_speed[i] = vt / WHEEL_R
        return True

    def body_point(self, local, radius):
        
        p = self.to_world(local)
        n, t, inv = get_normal(p.x, 4.0)
        dist = (get_height(p.x) - p.y) * inv
        pen = radius - dist
        if pen <= 0:
            return False

        v = self.point_velocity(p)
        N = clamp(BODY_K * pen - BODY_C * v.dot(n), 0.0, 20000.0)
        Ft = clamp(-v.dot(t) * 8.0, -0.8 * N, 0.8 * N)
        self.add_force(n * N + t * Ft, p)
        return True

    def step(self, dt, gas, brake):
        
        if not self.crashed:
            drain = FUEL_DRAIN
            if gas:
                drain += FUEL_GAS_DRAIN
            self.fuel = max(0.0, self.fuel - drain * dt)

        if self.fuel <= 0:
            gas = False
            if not self.crashed and self.vel.length() < 20:
                self.stall_time += dt
            else:
                self.stall_time = 0.0
        else:
            self.stall_time = 0.0
        self.stalled = self.stall_time > 1.5

        if self.crashed:
            gas = False
            brake = False

        self.force = pygame.Vector2(0, GRAVITY)
        self.torque = 0.0

        contacts = 0
        for i in range(2):
            if self.wheel_physics(i, gas, brake):
                contacts += 1
        self.on_ground = contacts > 0

        for sx in (-1, 1):
            self.body_point(pygame.Vector2(sx * BODY_W / 2, BODY_H / 2), 0)
            self.body_point(pygame.Vector2(sx * BODY_W / 2, -BODY_H / 2), 0)
        if self.body_point(pygame.Vector2(HEAD_X, HEAD_Y), HEAD_R):
            self.crashed = True

        alpha = self.torque / INERTIA

        
        if contacts == 0:
            if gas:
                alpha -= AIR_TORQUE
            if brake:
                alpha += AIR_TORQUE
            self.omega -= self.omega * ANG_DAMP * dt
            for i in range(2):
                self.spin_speed[i] *= 1 - 0.3 * dt
                if gas:
                    self.spin_speed[i] += 400 * dt / WHEEL_R

        self.vel += self.force * dt
        self.pos += self.vel * dt
        self.omega += alpha * dt
        self.angle += self.omega * dt

        for i in range(2):
            self.spin[i] += self.spin_speed[i] * dt

    def draw(self, surface, cam_x, cam_y):
        cam = pygame.Vector2(cam_x, cam_y)

        def sc(p):
            q = p - cam
            return (int(q.x), int(q.y))

        
        for i in range(2):
            mount = self.to_world(self.mounts[i])
            center = self.wheel_center(i)
            pygame.draw.line(surface, (90, 90, 90), sc(mount), sc(center), 6)
            pygame.draw.circle(surface, (25, 25, 25), sc(center), WHEEL_R)
            pygame.draw.circle(surface, (170, 170, 170), sc(center), 8)
            for k in range(3):
                a = self.spin[i] + k * math.tau / 3
                end = center + pygame.Vector2(math.cos(a), math.sin(a)) * 8
                pygame.draw.line(surface, (60, 60, 60), sc(center), sc(end), 2)

        
        h = BODY_H / 2
        w = BODY_W / 2
        body = []
        for x, y in ((-w, -h), (w, -h), (w, h), (-w, h)):
            body.append(sc(self.to_world(pygame.Vector2(x, y))))
        dark = (int(self.color[0] * 0.5), int(self.color[1] * 0.5), int(self.color[2] * 0.5))
        pygame.draw.polygon(surface, self.color, body)
        pygame.draw.polygon(surface, dark, body, 2)

        
        cabin = []
        for x, y in ((-22, -h), (-14, -h - 15), (14, -h - 15), (26, -h)):
            cabin.append(sc(self.to_world(pygame.Vector2(x, y))))
        pygame.draw.polygon(surface, (150, 215, 245), cabin)
        pygame.draw.polygon(surface, (90, 90, 90), cabin, 2)

        
        light = []
        for x, y in ((w - 6, -4), (w, -4), (w, 3), (w - 6, 3)):
            light.append(sc(self.to_world(pygame.Vector2(x, y))))
        pygame.draw.polygon(surface, (255, 235, 120), light)

car = None
pickups = []
next_pickup_x = 900.0
level_index = 0
cam_y = 0.0
acc = 0.0
result = None        
end_timer = 0.0
finish_x = 0


def start_level(i):
    global level, level_index, phase, car, pickups, next_pickup_x
    global cam_y, acc, result, end_timer, finish_x, state, motor_chanel

    level_index = i
    level = LEVELS[i]
    phase = [random.uniform(0, math.tau) for _ in range(4)]
    car = Car(START_X, get_height(START_X) - 33, CAR_COLORS[save["car_color"]][1])
    pickups = []
    next_pickup_x = 900.0
    cam_y = car.pos.y - HEIGHT * 0.6
    acc = 0.0
    result = None
    end_timer = 0.0
    finish_x = START_X + level["goal"] * PX_PER_M
    state = "game"
    main_audio.stop()
    game_audio.stop()
    motor_audio.stop()

    motor_chanel = motor_audio.play(-1)
    motor_chanel.set_volume(save["volume"])

    if save["music"]:
        game_audio.play(-1)
        game_audio.set_volume(save["volume"])


def pickup_pos(p):
    return pygame.Vector2(p["x"], get_height(p["x"]) - 40)


def collect_pickups():
    
    if car.crashed:
        return False
    got = False
    for p in pickups:
        if p["taken"]:
            continue
        if (car.pos - pickup_pos(p)).length() < PICKUP_RADIUS:
            p["taken"] = True
            car.fuel = min(FUEL_MAX, car.fuel + FUEL_PICKUP)
            got = True
            pickup_audio.play()
            pickup_audio.set_volume(save["volume"])

    return got


def update_game(dt, gas, brake):
    global acc, cam_y, result, end_timer, next_pickup_x

    
    while next_pickup_x < car.pos.x + WIDTH + 400:
        pickups.append({"x": next_pickup_x, "taken": False})
        next_pickup_x += random.uniform(level["gap"][0], level["gap"][1])

    acc += dt
    got = False
    while acc >= STEP:
        car.step(STEP, gas, brake)
        if collect_pickups():
            got = True
        acc -= STEP

    if result is None:
        if car.distance() >= level["goal"]:
            result = "win"

        elif car.crashed:
            result = "crash"

        elif car.stalled:
            result = "fuel"
    else:
        end_timer += dt
        if end_timer >= END_DELAY:
            open_end()
            return 

    
    target_y = car.pos.y - HEIGHT * 0.6
    cam_y += (target_y - cam_y) * min(1.0, 4 * dt)


def draw_pickups(cam_x, cam_y):
    bob = math.sin(pygame.time.get_ticks() / 250) * 4
    for p in pickups:
        if p["taken"]:
            continue
        pos = pickup_pos(p)
        cx = int(pos.x - cam_x)
        cy = int(pos.y - cam_y + bob)
        if cx < -50 or cx > WIDTH + 50:
            continue
        pygame.draw.circle(window, (255, 240, 150), (cx, cy), 28, 2)
        can = pygame.Rect(cx - 12, cy - 14, 24, 28)
        pygame.draw.rect(window, (210, 35, 35), can, border_radius=4)
        pygame.draw.rect(window, (255, 215, 60), (cx - 12, cy - 3, 24, 7))
        pygame.draw.rect(window, (110, 10, 10), can, 2, border_radius=4)
        pygame.draw.rect(window, (110, 10, 10), (cx + 3, cy - 21, 9, 8), border_radius=2)
        pygame.draw.rect(window, (110, 10, 10), (cx - 12, cy - 20, 12, 6), 2, border_radius=2)


def draw_finish(cam_x, cam_y):
    fx = finish_x - cam_x
    if fx < -100 or fx > WIDTH + 100:
        return
    gy = get_height(finish_x) - cam_y
    for off in (-36, 36):
        pygame.draw.line(window, (235, 235, 235), (fx + off, gy), (fx + off, gy - 120), 6)
    for row in range(2):
        for col in range(6):
            if (row + col) % 2:
                color = (20, 20, 20)
            else:
                color = (245, 245, 245)
            pygame.draw.rect(window, color, (fx - 36 + col * 12, gy - 120 + row * 12, 12, 12))


def draw_fuel_bar():
    x = WIDTH - 245
    y = 15
    w = 220
    h = 26
    frac = car.fuel / FUEL_MAX

    pygame.draw.rect(window, (35, 35, 35), (x - 4, y - 4, w + 8, h + 8), border_radius=8)
    pygame.draw.rect(window, (90, 90, 90), (x, y, w, h), border_radius=5)

    if frac > 0.5:
        color = (70, 200, 70)
    elif frac > 0.2:
        color = (240, 200, 40)
    else:
        color = (220, 50, 40)
        if (pygame.time.get_ticks() // 250) % 2:    
            color = (255, 130, 110)

    if frac > 0:
        pygame.draw.rect(window, color, (x, y, int(w * frac), h), border_radius=5)

    label = pixel_text("FUEL", 2, (255, 255, 255))
    window.blit(label, (x + 8, y + (h - label.get_height()) // 2))


def draw_game():
    cam_x = car.pos.x - 300

    draw_background(cam_x, cam_y)
    draw_terrain(cam_x, cam_y)
    draw_finish(cam_x, cam_y)
    draw_pickups(cam_x, cam_y)
    car.draw(window, cam_x, cam_y)

    
    goal = level["goal"]
    dist = min(int(car.distance()), goal)
    ink = (35, 35, 30)
    window.blit(pixel_text(str(dist) + " / " + str(goal) + " M", 2, ink), (15, 12))


    draw_fuel_bar()
    draw_hint("→ / D gas    ← / A brake & reverse    R restart    ESC pause", 15, HEIGHT - 30)


state = "menu"          
menu_title = ""
menu_items = []        
menu_sel = 0
menu_title_scale = 6
menu_title_y = 40
menu_hills = False


state = "win"
win_title = ""
win_items = []
win_sel = 0
win_title_scale = 6
win_title_y = 40



def make_menu(title, items, top=None, gap=14, title_scale=6, title_y=40, hills=False):
    global menu_title, menu_items, menu_sel, menu_title_scale, menu_title_y, menu_hills
    menu_title = title
    menu_items = items
    menu_title_scale = title_scale
    menu_title_y = title_y
    menu_hills = hills

    total = 0
    for item in items:
        if item["enabled"]:
            color = BTN_TEXT
        else:
            color = BTN_TEXT_DIM
        img = pixel_text(item["text"], 3, color)
        w = max(item.get("min_w", 0), img.get_width() + 36)
        h = img.get_height() + 20
        item["rect"] = pygame.Rect(0, 0, w, h)
        total += h + gap
    total -= gap

    if top is None:
        title_h = pixel_text(title, title_scale, TITLE_COLOR).get_height()
        area_top = title_y + title_h + 30
        top = area_top + max(0, (HEIGHT - 30 - area_top - total) // 2)

    y = top
    for item in items:
        item["rect"].centerx = WIDTH // 2
        item["rect"].y = y
        y += item["rect"].h + gap

    menu_sel = 0
    for i, item in enumerate(items):
        if item["enabled"]:
            menu_sel = i
            break

def win_menu(title, items, top=None, gap=14, title_scale=6, title_y=40, hills=False):
    global win_title, win_items, win_sel, win_title_scale, win_title_y, menu_hills
    win_title = title
    win_items = items
    win_title_scale = title_scale
    win_title_y = title_y
    menu_hills = hills

    total = 0
    for item in items:
        if item["enabled"]:
            color = BTN_TEXT
        else:
            color = BTN_TEXT_DIM
        img = pixel_text(item["text"], 3, color)
        w = max(item.get("min_w", 0), img.get_width() + 36)
        h = img.get_height() + 20
        item["rect"] = pygame.Rect(0, 0, w, h)
        total += h + gap
    total -= gap

    if top is None:
        title_h = pixel_text(title, title_scale, TITLE_COLOR).get_height()
        area_top = title_y + title_h + 30
        top = area_top + max(0, (HEIGHT - 30 - area_top - total) // 2)

    y = top
    for item in items:
        item["rect"].centerx = WIDTH // 2
        item["rect"].y = y
        y += item["rect"].h + gap

    win_sel = 0
    for i, item in enumerate(items):
        if item["enabled"]:
            win_sel = i
            break


def move_selection(d):
    global menu_sel
    n = len(menu_items)
    i = menu_sel
    for _ in range(n):
        i = (i + d) % n
        if menu_items[i]["enabled"]:
            menu_sel = i
            return

def win_selection(d):
    global win_sel
    n = len(win_items)
    i = win_sel
    for _ in range(n):
        i = (i + d) % n
        if win_items[i]["enabled"]:
            win_sel = i
            return 

def menu_event(event):
    global menu_sel
    if event.type == pygame.MOUSEMOTION:
        for i, item in enumerate(menu_items):
            if item["enabled"] and item["rect"].collidepoint(event.pos):
                if menu_sel != i:
                    hover_sound.play()
                menu_sel = i
                break

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for item in menu_items:
            if item["enabled"] and item["rect"].collidepoint(event.pos):

                item["action"]()
                
                return

    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            move_selection(-1)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            move_selection(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            item = menu_items[menu_sel]
            if item["enabled"]:

                item["action"]()

def win_event(event):
    global win_sel
    if event.type == pygame.MOUSEMOTION:
        for i, item in enumerate(win_items):
            if item["enabled"] and item["rect"].collidepoint(event.pos):
                win_sel = i

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for item in win_items:
            if item["enabled"] and item["rect"].collidepoint(event.pos):

                item["action"]()
                return

    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            win_selection(-1)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            win_selection(1)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            item = win_items[win_sel]
            if item["enabled"]:

                item["action"]()




def draw_title(text, scale, y):
    img = pixel_text(text, scale, TITLE_COLOR)
    x = WIDTH // 2 - img.get_width() // 2
    window.blit(img, (x, y))


def draw_button(text, rect, selected, enabled=True):
    if selected and enabled:
        pygame.draw.rect(window, BTN_BG_SEL, rect)
        color = TITLE_COLOR
    else:
        pygame.draw.rect(window, BTN_BG, rect)
        color = BTN_TEXT
    if not enabled:
        color = BTN_TEXT_DIM
    img = pixel_text(text, 3, color)
    window.blit(img, img.get_rect(center=rect.center))


def draw_menu():
    window.fill(MENU_BG)

    draw_title(menu_title, menu_title_scale, menu_title_y)
    for i, item in enumerate(menu_items):
        draw_button(item["text"], item["rect"], i == menu_sel, item["enabled"])


def draw_win():
    window.fill(MENU_BG)

    draw_title(win_title, win_title_scale, win_title_y)
    for i, item in enumerate(win_items):
        draw_button(item["text"], item["rect"], i == win_sel, item["enabled"])




def item(text, action, enabled=True, min_w=0):
    return {"text": text, "action": action, "enabled": enabled, "min_w": min_w}


def open_main():
    global state
    make_menu("HILL CLIMB", [
        item("PLAY", open_levels),
        item("SETTINGS", open_settings),
        item("QUIT", quit_game),
    ], title_scale=7, hills=True)
    state = "menu"

    game_audio.stop()
    motor_audio.stop()

    if save["music"]:
        main_audio.stop()
        main_audio.play(-1)
        main_audio.set_volume(save["volume"])
    else:
        main_audio.stop()

def win_main():
    global state
    next_level = level_index + 1
    items = []

    if next_level < len(LEVELS):
        items.append(item("Next level", lambda: start_level(next_level)))

    items.append(item("SETTINGS", open_settings))
    items.append(item("QUIT", quit_game))

    win_menu("YOU WIN", items, title_scale=7, hills=False)
    state="win"


def open_levels():
    global state
    if UNLOCK_ALL_LEVELS:
        unlocked = len(LEVELS)
    else:
        unlocked = save["unlocked"]

    items = []
    for i in range(len(LEVELS)):
        name = LEVELS[i]["name"]
        if i < unlocked:
            text = str(i + 1) + " " + name
            best = save["best"].get(str(i), 0)
            if best > 0:
                text += "  BEST " + str(best) + "M"
            items.append(item(text, lambda i=i: start_level(i), True, 520))
        else:
            items.append(item(str(i + 1) + " " + name + "  LOCKED", None, False, 520))
    items.append(item("BACK", open_main, True, 520))

    make_menu("SELECT LEVEL", items, gap=10, title_scale=5, title_y=30)
    state = "levels"


def open_pause():
    global state
    i = level_index
    make_menu("PAUSED", [
        item("RESUME", resume_game),
        item("RESTART", lambda: start_level(i)),
        item("MENU", open_main),
    ], top=250, title_scale=8, title_y=60)
    state = "pause"


def resume_game():
    global state

    state = "game"

    if save["music"]:
        main_audio.stop()
        if not game_audio.get_num_channels():
            game_audio.play(-1)
        game_audio.set_volume(save["volume"])


def open_end():
    global state
    i = level_index
    goal = level["goal"]

    
    if result == "win":
        finish_audio.play()
        finish_audio.set_volume(save["volume"])
        reached = goal
        save["unlocked"] = max(save["unlocked"], min(i + 2, len(LEVELS)))
        save["best"][str(i)] = max(save["best"].get(str(i), 0), reached)
        write_save()
        win_main()
        reached = goal

        return
    else:
        reached = min(int(car.distance()), goal)
    save["best"][str(i)] = max(save["best"].get(str(i), 0), reached)
    write_save()

    if result == "win":
        title = "You Win"
    elif result == "crash":
        boom_audio.play()
        title = "Crashed"
    else:
        title = "No fuel"

    items = []
    if result == "win" and i + 1 < len(LEVELS):
        items.append(item("Next level", lambda: start_level(i + 1)))
    items.append(item("RESTART", lambda: start_level(i)))
    items.append(item("MENU", open_main))
    make_menu(title, items, top=250, title_scale=8, title_y=60)
    state = "end"


def quit_game():
    write_save()
    pygame.quit()
    sys.exit()

settings_row = 0        
slider_drag = False
settings_time = 0.0
preview_car = None

color_rect = None
vol_rect = None
slider_rect = None
swatches = []
color_left = None
color_right = None
vol_left = None
vol_right = None
back_rect = None

def toggle_music():
    save["music"] = not save["music"]

    if save["music"]:
        if previous_state == "game" or previous_state == "pause":
            game_audio.play(-1)
            game_audio.set_volume(save["volume"])
        else:
            main_audio.play(-1)
            main_audio.set_volume(save["volume"])
    else:
        main_audio.stop()
        game_audio.stop()

    write_save()


def setup_settings():
    global color_rect, vol_rect, slider_rect, swatches, color_left, color_right
    global vol_left, vol_right, back_rect, preview_car, music_rect, previous_state

    cx = WIDTH // 2
    color_rect = pygame.Rect(cx - 270, 255, 540, 100)
    vol_rect = pygame.Rect(cx - 270, 372, 540, 84)
    slider_rect = pygame.Rect(cx - 170, vol_rect.y + 54, 340, 14)

    music_rect = None

    previous_state = "menu"

    swatches = []
    total = len(CAR_COLORS) * 34 + (len(CAR_COLORS) - 1) * 8
    x = cx - total // 2
    for c in CAR_COLORS:
        swatches.append(pygame.Rect(x, color_rect.y + 56, 34, 34))
        x += 42

    color_left = pygame.Rect(color_rect.x + 8, color_rect.centery - 24, 48, 48)
    color_right = pygame.Rect(color_rect.right - 56, color_rect.centery - 24, 48, 48)
    vol_left = pygame.Rect(vol_rect.x + 8, vol_rect.centery - 24, 48, 48)
    vol_right = pygame.Rect(vol_rect.right - 56, vol_rect.centery - 24, 48, 48)

    music_rect = pygame.Rect(WIDTH // 2 - 110, 465, 220, 45)

    back_rect = pygame.Rect(0, 0, 200, 56)
    back_rect.center = (cx, 555)

    preview_car = Car(0, 0, CAR_COLORS[0][1])


def open_settings():
    global state, settings_row, previous_state

    previous_state = state
    settings_row = 0
    state = "settings"


def close_settings():
    global state

    write_save()
    state = previous_state


def set_color(i):
    save["car_color"] = i % len(CAR_COLORS)

    write_save()


def set_volume(v):
    save["volume"] = clamp(v, 0.0, 1.0)

    pygame.mixer.music.set_volume(save["volume"])

    hover_sound.set_volume(save["volume"])
    boom_audio.set_volume(save["volume"])
    motor_audio.set_volume(save["volume"])
    main_audio.set_volume(save["volume"])
    finish_audio.set_volume(save["volume"])
    pickup_audio.set_volume(save["volume"])
    game_audio.set_volume(save["volume"])


def change_setting(d):
    if settings_row == 0:
        set_color(save["car_color"] + d)
        hover_sound.play()
    elif settings_row == 1:
        steps = round(save["volume"] * 10) + d
        set_volume(clamp(steps, 0, 10) / 10)
        hover_sound.play()

        write_save()


def volume_from_mouse(x):
    frac = clamp((x - slider_rect.x) / slider_rect.w, 0.0, 1.0)
    set_volume(round(frac * 20) / 20)


def settings_event(e):
    global settings_row, slider_drag

    if e.type == pygame.KEYDOWN:
        if e.key == pygame.K_ESCAPE:
            close_settings()
        elif e.key == pygame.K_UP or e.key == pygame.K_w:
            settings_row = (settings_row - 1) % 4
        elif e.key == pygame.K_DOWN or e.key == pygame.K_s:
            settings_row = (settings_row + 1) % 4
        elif e.key == pygame.K_LEFT or e.key == pygame.K_a:
            change_setting(-1)
        elif e.key == pygame.K_RIGHT or e.key == pygame.K_d:
            change_setting(1)
        elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if settings_row == 2:
                toggle_music()
            elif settings_row == 3:
                close_settings()

    elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
        pos = e.pos
        if back_rect.collidepoint(pos):
            close_settings()
        elif color_left.collidepoint(pos):
            settings_row = 0
            change_setting(-1)
        elif color_right.collidepoint(pos):
            settings_row = 0
            change_setting(1)
        elif vol_left.collidepoint(pos):
            settings_row = 1
            change_setting(-1)
        elif vol_right.collidepoint(pos):
            settings_row = 1
            change_setting(1)
        elif slider_rect.inflate(10, 30).collidepoint(pos):
            settings_row = 1
            slider_drag = True
            volume_from_mouse(pos[0])
        elif music_rect.collidepoint(pos):
            settings_row = 2
            toggle_music()
        else:
            for i, r in enumerate(swatches):
                if r.collidepoint(pos):
                    settings_row = 0
                    set_color(i)

    elif e.type == pygame.MOUSEMOTION:
        if slider_drag:
            volume_from_mouse(e.pos[0])
        elif back_rect.collidepoint(e.pos):
            settings_row = 2
        elif music_rect.collidepoint(e.pos):
            settings_row = 3
        elif music_rect.collidepoint(e.pos):
            settings_row = 2

    elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
        if slider_drag:
            slider_drag = False

            write_save()


def draw_settings(dt):
    global settings_time
    settings_time += dt
    color_index = save["car_color"]
    name = CAR_COLORS[color_index][0]
    rgb = CAR_COLORS[color_index][1]

    window.fill(MENU_BG)
    draw_title("SETTINGS", 6, 20)

    arrow_l = pixel_text("<", 3, BTN_TEXT)
    arrow_r = pixel_text(">", 3, BTN_TEXT)

    

    label = pixel_text(name, 3, BTN_TEXT)
    window.blit(label, label.get_rect(center=(WIDTH // 2, color_rect.y + 50)))
    window.blit(arrow_l, arrow_l.get_rect(center=color_left.center))
    window.blit(arrow_r, arrow_r.get_rect(center=color_right.center))
    
    
    vol = save["volume"]
    label = pixel_text("VOLUME " + str(round(vol * 100)) + "%", 3, BTN_TEXT)
    window.blit(label, label.get_rect(center=(WIDTH // 2, vol_rect.y + 24)))
    window.blit(arrow_l, arrow_l.get_rect(center=vol_left.center))
    window.blit(arrow_r, arrow_r.get_rect(center=vol_right.center))
    pygame.draw.rect(window, (60,55,30), slider_rect)
    fill = slider_rect.copy()
    fill.w = int(slider_rect.w * vol)
    pygame.draw.rect(window, (180,170,90), fill)

    knob = pygame.Rect(slider_rect.x + fill.w - 5, slider_rect.y - 5, 10,24)
    pygame.draw.rect(window, BTN_TEXT, knob)

    music_text = "MUSIC: ON" if save["music"] else "MUSIC: OFF"
    draw_button(music_text, music_rect, settings_row == 2)

    draw_button("BACK", back_rect, settings_row == 3)

hover_sound = pygame.mixer.Sound("hover.ogg")
test_song = pygame.mixer.Sound("sounds.ogg")
boom_audio = pygame.mixer.Sound("boom.ogg")
main_audio = pygame.mixer.Sound("main_menu.ogg")
motor_audio = pygame.mixer.Sound("engine.ogg")
finish_audio = pygame.mixer.Sound("finish_sound.ogg")
pickup_audio = pygame.mixer.Sound("pickupCoin.ogg")
game_audio = pygame.mixer.Sound("Untitled.ogg")

async def main():
    global state

    load_save()
    setup_settings()
    open_main()
    

    while True:
        dt = min(clock.tick(FPS) / 1000, 0.05)

        

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state == "game":
                    open_pause()
                elif state == "levels" or state == "end":
                    open_main()
                elif state == "pause":
                    resume_game()
                elif state == "settings":
                    close_settings()
                continue

            if state == "game":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    start_level(level_index)
                    main_audio.stop()
            elif state == "settings":
                settings_event(event)
            elif state == "win":
                win_event(event)
            else:
                menu_event(event)

        if state == "game":
            keys = pygame.key.get_pressed()
            gas = keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_UP]
            brake = keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_DOWN]
            if motor_chanel:
                motor_chanel.set_volume(save["volume"] * (0.3 + 0.7 * (1 if gas else 0)))
            if result is not None:
                gas = False
                brake = False

            update_game(dt, gas, brake)


        if state == "game":
            draw_game()
        elif state == "settings":
            draw_settings(dt)
        elif state == "win":
            draw_win()
        else:
            draw_menu()

        pygame.display.flip()
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
