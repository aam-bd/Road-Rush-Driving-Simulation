from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# ---------- Window & Camera ----------
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / WIN_H
fovY = 90

# Camera follow settings
camera_distance = 220
camera_height = 120

# Camera modes
MODE_REGULAR = 0
MODE_FIRST_PERSON = 1
camera_mode = MODE_REGULAR

# ---------- Game Timer ----------
game_start_time = 0
game_duration = 60  # 1 minutes

# ---------- Road / Lanes ----------
ROAD_WIDTH = 360
LANE_COUNT = 3
LANE_WIDTH = ROAD_WIDTH / LANE_COUNT
LANE_X = [-(LANE_WIDTH), 0.0, (LANE_WIDTH)]
road_marker_spacing = 60
road_scroll = 0

# Map bounds (only used for cleanup limits)
MAP_LENGTH = 10000
MAP_WIDTH = ROAD_WIDTH + 400

# ---------- Player ----------
player_lane = 1
player_pos = [LANE_X[player_lane], 0.0, 0.0]
player_forward_speed = 6.0
player_speed = 0.0
player_max_speed = 16.0
player_acc = 1.5
player_angle = 0.0
turret_angle = 0.0

# Distance travelled (in world units ~ meters)
total_distance = 0.0

# ---------- Lives / Score ----------
max_life = 3
life = max_life
score = 0
game_over = False

# ---------- Bullets ----------
bullets = []  # {pos:[x,y,z], angle, speed, ttl}
bullet_speed = 28.0
bullet_ttl = 140

# ---------- Enemies ----------
enemies = []  # {lane,int; pos,[x,y,z]; alive,bool; hits,int; explode_t,int; speed,float; type,str; ...}
enemy_base_speed = 2.0
enemy_spawn_frames = 60
enemy_hits_to_die = 3
max_enemies = 12

# ---------- Effects ----------
muzzle_timer = 0
frames = 0
spawn_timer = 0

# ---------- Day/Night Cycle ----------
sky_transition = 0.0
SKY_STEP = 0.06
clouds, birds, stars = [], [], []
NUM_CLOUDS, NUM_BIRDS, NUM_STARS = 8, 6, 120
bird_flocks = []

# ---------- Visual Colors ----------
COLOR_ROAD = (0.15, 0.15, 0.15)
COLOR_GRASS = (0.10, 0.55, 0.18)
COLOR_LANE_MARK = (1.0, 1.0, 1.0)
COLOR_PLAYER = (0.18, 0.62, 1.0)
COLOR_ENEMY_CAR = (1.0, 0.35, 0.25)
COLOR_ENEMY_BIKE = (0.85, 0.1, 0.1)
COLOR_WHEEL = (0.0, 0.0, 0.0)
COLOR_BARREL = (0.6, 0.6, 0.6)
COLOR_BIKE = (0.30, 0.30, 0.32)
COLOR_HEADLIGHT = (1.0, 1.0, 0.8)
COLOR_TAIL = (1.0, 0.1, 0.1)

# ==========================
# Infinite view tuning
VIEW_DISTANCE = 2800.0
MARKER_SPACING = road_marker_spacing

# Enemy spawn "density window"
SPAWN_AHEAD_MIN = 350
SPAWN_AHEAD_MAX = 2000
ENEMY_DENSITY = 0.0025
SPAWN_CLEANUP_BEHIND = 1400

# ---------- Helper Functions ----------
def clamp(v, lo, hi):
    if v < lo: return lo
    if v > hi: return hi
    return v

def lerp(a, b, t): 
    return a + (b - a) * t

def vec_lerp(c1, c2, t): 
    return tuple(lerp(c1[i], c2[i], t) for i in range(3))

def lane_x(l):
    return LANE_X[l]

def dist2_xy(a, b):
    dx = a[0]-b[0]; dy = a[1]-b[1]
    return dx*dx + dy*dy

# ---------- Environment Init ----------
def init_environment():
    global clouds, birds, stars, bird_flocks
    clouds = [{
        "x": random.uniform(-0.3, 1.2),
        "y": random.uniform(0.62, 0.9),
        "speed": random.uniform(0.0008, 0.0024),
        "size": random.uniform(0.06, 0.18),
        "alpha": random.uniform(0.6, 0.95)
    } for _ in range(NUM_CLOUDS)]

    # Flocks
    bird_flocks = []
    num_flocks = 2
    for _ in range(num_flocks):
        leader = {
            "x": random.uniform(-0.2, 1.2),
            "y": random.uniform(0.65, 0.85),
            "speed": random.uniform(0.003, 0.005),
            "flap": random.uniform(0, math.pi*2)
        }
        members = []
        for i in range(NUM_BIRDS // num_flocks):
            members.append({"offset": (random.uniform(-0.05, 0.05),
                                       random.uniform(-0.02, 0.02)),
                            "flap": random.uniform(0, math.pi*2),
                            "scale": random.uniform(0.8, 1.4)})
        bird_flocks.append({"leader": leader, "members": members})

    stars = [{"x": random.random(), "y": random.uniform(0.5, 1.0),
              "alpha": random.uniform(0.4, 1.0),
              "twinkle": random.uniform(0.5, 2.0)} for _ in range(NUM_STARS)]

# ---------- Drawing Sky + Objects ----------
'''
def draw_sky():
    day_top, day_bottom = (0.50, 0.75, 1.0), (0.75, 0.9, 1.0)
    night_top, night_bottom = (0.03, 0.06, 0.15), (0.08, 0.12, 0.25)

    t = clamp(sky_transition, 0.0, 1.0)
    top, bottom = vec_lerp(day_top, night_top, t), vec_lerp(day_bottom, night_bottom, t)

    # 2D overlay
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Gradient
    glBegin(GL_QUADS)
    glColor3f(*top); glVertex2f(0, 1)
    glColor3f(*top); glVertex2f(1, 1)
    glColor3f(*bottom); glVertex2f(1, 0)
    glColor3f(*bottom); glVertex2f(0, 0)
    glEnd()

    # Sun/Moon
    sun_day, moon = (1.0, 0.92, 0.45), (0.95, 0.96, 1.0)
    sun_col = vec_lerp(sun_day, moon, t)
    sun_alpha, sun_r = lerp(1.0, 0.25, t), lerp(0.08, 0.035, t)
    sun_x, sun_y = lerp(0.18, 0.82, t), lerp(0.87, 0.72, t)

    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    for i in range(8, 0, -1):
        s = sun_r * (i/8); a = sun_alpha * (0.18 + 0.82*(i/8))
        glColor4f(*sun_col, a)
        glBegin(GL_QUADS)
        glVertex2f(sun_x-s, sun_y-s); glVertex2f(sun_x+s, sun_y-s)
        glVertex2f(sun_x+s, sun_y+s); glVertex2f(sun_x-s, sun_y+s)
        glEnd()

    # Stars (fade in at night)
    for s in stars:
        alpha = (t * s["alpha"]) * (0.5+0.5*math.sin(time.time()*s["twinkle"]))
        glColor4f(1,1,1,alpha)
        glBegin(GL_POINTS); glVertex2f(s["x"], s["y"]); glEnd()

    # Clouds
    for c in clouds:
        col = vec_lerp((1,1,1), (0.82,0.86,0.9), t)
        glColor4f(*col, c["alpha"]*(1-t*0.45))
        for ox, oy, rm in [(-0.35,0,0.8),(0,0.05,1.0),(0.3,-0.02,0.7)]:
            draw_circle(c["x"]+ox*c["size"], c["y"]+oy*c["size"], c["size"]*rm)

    # Birds in flocks
    for flock in bird_flocks:
        L = flock["leader"]
        draw_bird(L["x"], L["y"], 1.2, L["flap"], t)
        for m in flock["members"]:
            draw_bird(L["x"]+m["offset"][0], L["y"]+m["offset"][1],
                      m["scale"], m["flap"], t)

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW); glEnable(GL_DEPTH_TEST)
'''
def draw_sky():
    day_top, day_bottom = (0.50, 0.75, 1.0), (0.75, 0.9, 1.0)
    night_top, night_bottom = (0.03, 0.06, 0.15), (0.08, 0.12, 0.25)

    t = clamp(sky_transition, 0.0, 1.0)
    top, bottom = vec_lerp(day_top, night_top, t), vec_lerp(day_bottom, night_bottom, t)

    # 2D overlay
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1, 0, 1)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()

    # Gradient
    glBegin(GL_QUADS)
    glColor3f(*top); glVertex2f(0, 1)
    glColor3f(*top); glVertex2f(1, 1)
    glColor3f(*bottom); glVertex2f(1, 0)
    glColor3f(*bottom); glVertex2f(0, 0)
    glEnd()

    # Sun/Moon
    sun_day, moon = (1.0, 0.92, 0.45), (0.95, 0.96, 1.0)
    sun_col = vec_lerp(sun_day, moon, t)
    sun_alpha, sun_r = lerp(1.0, 0.25, t), lerp(0.08, 0.035, t)
    sun_x, sun_y = lerp(0.18, 0.82, t), lerp(0.87, 0.72, t)

    glEnable(GL_BLEND); glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # Sun glow effect (multiple concentric circles with decreasing alpha)
    glow_layers = 12
    for i in range(glow_layers, 0, -1):
        layer_alpha = sun_alpha * (0.05 + 0.95 * (i / glow_layers))
        layer_size = sun_r * (1.0 + (glow_layers - i) * 0.15)
        glColor4f(*sun_col, layer_alpha * 0.5)
        draw_circle(sun_x, sun_y, layer_size, segs=36)
    
    # Main sun circle
    glColor4f(*sun_col, sun_alpha)
    draw_circle(sun_x, sun_y, sun_r, segs=36)

    # Stars (fade in at night)
    for s in stars:
        alpha = (t * s["alpha"]) * (0.5+0.5*math.sin(time.time()*s["twinkle"]))
        glColor4f(1,1,1,alpha)
        glBegin(GL_POINTS); glVertex2f(s["x"], s["y"]); glEnd()

    # Clouds
    for c in clouds:
        col = vec_lerp((1,1,1), (0.82,0.86,0.9), t)
        glColor4f(*col, c["alpha"]*(1-t*0.45))
        for ox, oy, rm in [(-0.35,0,0.8),(0,0.05,1.0),(0.3,-0.02,0.7)]:
            draw_circle(c["x"]+ox*c["size"], c["y"]+oy*c["size"], c["size"]*rm)

    # Birds in flocks
    for flock in bird_flocks:
        L = flock["leader"]
        draw_bird(L["x"], L["y"], 1.2, L["flap"], t)
        for m in flock["members"]:
            draw_bird(L["x"]+m["offset"][0], L["y"]+m["offset"][1],
                      m["scale"], m["flap"], t)

    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW); glEnable(GL_DEPTH_TEST)
def draw_circle(x,y,r,segs=20):
    glBegin(GL_TRIANGLE_FAN); glVertex2f(x,y)
    for i in range(segs+1):
        a=2*math.pi*(i/segs); glVertex2f(x+math.cos(a)*r,y+math.sin(a)*r)
    glEnd()

def draw_bird(x,y,scale,flap,night_t):
    vis=max(0.25,1.0-night_t*0.9); glColor4f(0.06,0.06,0.06,vis)
    w=0.015*scale*(0.9+0.3*math.sin(flap)); l=0.03*scale
    glBegin(GL_LINES)
    glVertex2f(x-l,y-w); glVertex2f(x,y)
    glVertex2f(x+l,y-w); glVertex2f(x,y)
    glEnd()

# ---------- World with Tint ----------
def apply_tint(col):
    warm=(1.0,0.9,0.7); return vec_lerp(col, warm, (1.0-sky_transition)*0.4)

def draw_ground():
    glColor3f(*apply_tint((0.2,0.8,0.2)))
    glBegin(GL_QUADS)
    glVertex3f(-500,-500,0); glVertex3f(500,-500,0)
    glVertex3f(500,500,0); glVertex3f(-500,500,0)
    glEnd()

def draw_road():
    """
    Single-pass sliding window road + lane markers.
    Adds fog to fade into horizon for a strong "infinite" cue.
    """
    half = VIEW_DISTANCE * 0.5
    y_start = player_pos[1] - half
    y_end   = player_pos[1] + half

    # Grass shoulders
    glBegin(GL_QUADS)
    glColor3f(*apply_tint(COLOR_GRASS))
    glVertex3f(-MAP_WIDTH/2, y_start, 0)
    glVertex3f(-ROAD_WIDTH/2, y_start, 0)
    glVertex3f(-ROAD_WIDTH/2, y_end,   0)
    glVertex3f(-MAP_WIDTH/2, y_end,   0)

    glVertex3f( ROAD_WIDTH/2, y_start, 0)
    glVertex3f( MAP_WIDTH/2,  y_start, 0)
    glVertex3f( MAP_WIDTH/2,  y_end,   0)
    glVertex3f( ROAD_WIDTH/2, y_end,   0)
    glEnd()

    # Road
    glColor3f(*apply_tint(COLOR_ROAD))
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_WIDTH/2, y_start, 0)
    glVertex3f( ROAD_WIDTH/2, y_start, 0)
    glVertex3f( ROAD_WIDTH/2, y_end,   0)
    glVertex3f(-ROAD_WIDTH/2, y_end,   0)
    glEnd()

    # Lane markers (dashes) aligned to player_pos for smooth scroll
    glLineWidth(4)
    glBegin(GL_LINES)
    glColor3f(*apply_tint(COLOR_LANE_MARK))
    offset = (player_pos[1] % MARKER_SPACING)
    first_y = y_start - offset
    for i in range(1, LANE_COUNT):
        x = -ROAD_WIDTH/2 + i * LANE_WIDTH
        y = first_y
        while y < y_end + MARKER_SPACING:
            glVertex3f(x, y, 0.01)
            glVertex3f(x, y + MARKER_SPACING * 0.5, 0.01)
            y += MARKER_SPACING
    glEnd()
    glLineWidth(1)

# ---------- HUD / Text ----------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# ---------- Draw primitives ----------
def draw_head_tail_lights():
    # small helper for lights, drawn in local space (front at +Y)
    # headlights
    glColor3f(*COLOR_HEADLIGHT)
    for lx in (-22, 22):
        glPushMatrix()
        glTranslatef(lx, 28, 18)
        glutSolidSphere(4, 8, 8)
        glPopMatrix()
    # tail lights
    glColor3f(*COLOR_TAIL)
    for lx in (-22, 22):
        glPushMatrix()
        glTranslatef(lx, -28, 18)
        glutSolidSphere(4, 8, 8)
        glPopMatrix()

def draw_car_at(pos, color, with_turret=False, turret_deg=0):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])

    # chassis
    glColor3f(*color)
    glPushMatrix()
    glScalef(2.2, 1.1, 0.55)
    glutSolidCube(48)
    glPopMatrix()

    # cabin
    glColor3f(0.7, 0.9, 1.0)
    glPushMatrix()
    glTranslatef(0, 0, 22)
    glScalef(1.4, 0.8, 0.35)
    glutSolidCube(40)
    glPopMatrix()

    # spoiler
    glColor3f(color[0]*0.9, color[1]*0.9, color[2]*0.9)
    glPushMatrix()
    glTranslatef(0, -22, 26)
    glScalef(1.2, 0.2, 0.08)
    glutSolidCube(40)
    glPopMatrix()

    # wheels
    glColor3f(*COLOR_WHEEL)
    for x in (-40, 40):
        for y in (-18, 18):
            glPushMatrix()
            glTranslatef(x, y, -14)
            glRotatef(90, 0, 1, 0)
            gluCylinder(gluNewQuadric(), 9, 9, 10, 12, 2)
            glPopMatrix()

    draw_head_tail_lights()

    if with_turret:
        glColor3f(*COLOR_BARREL)
        glPushMatrix()
        glTranslatef(0, 10, 26)
        glRotatef(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 5, 5, 38, 12, 2)
        glPopMatrix()

        glColor3f(0.85, 0.25, 0.25)
        glPushMatrix()
        glTranslatef(0, 0, 26)
        glRotatef(turret_deg, 0, 0, 1)
        glScalef(0.5, 0.5, 0.28)
        glutSolidCube(38)
        glPopMatrix()

    glPopMatrix()

def draw_bike_at(pos, color):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])

    # main body
    glColor3f(*COLOR_BIKE)
    glPushMatrix()
    glTranslatef(0, 0, 14)
    glScalef(1.0, 2.6, 0.35)
    glutSolidCube(28)
    glPopMatrix()

    # seat
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, -9, 24)
    glScalef(1.2, 0.7, 0.18)
    glutSolidCube(24)
    glPopMatrix()

    # handlebars
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, 26, 24)
    glScalef(1.4, 0.2, 0.1)
    glutSolidCube(20)
    glPopMatrix()

    # wheels
    glColor3f(*COLOR_WHEEL)
    for y in (-24, 24):
        glPushMatrix()
        glTranslatef(0, y, 0)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 11, 11, 8, 12, 2)
        glPopMatrix()

    # rider
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(0, 0, 36)
    glScalef(0.8, 0.8, 1.5)
    glutSolidCube(18)
    glPopMatrix()

    glColor3f(1.0, 0.85, 0.7)
    glPushMatrix()
    glTranslatef(0, 0, 54)
    glutSolidSphere(9, 10, 10)
    glPopMatrix()

    glPopMatrix()

def draw_bullet(b):
    glPushMatrix()
    glTranslatef(b["pos"][0], b["pos"][1], b["pos"][2])
    glColor3f(1,1,0)
    glutSolidSphere(5, 10, 10)
    glPopMatrix()

def draw_explosion(e):
    t = e["explode_t"]
    scale = (30 - t) * 3.0
    glPushMatrix()
    glTranslatef(e["pos"][0], e["pos"][1], e["pos"][2]+10)
    glColor3f(1.0, 0.9, 0.2); glutSolidSphere(max(1, scale*0.3), 12, 10)
    glColor3f(1.0, 0.5, 0.1); glutSolidSphere(max(1, scale*0.6), 10, 8)
    glColor3f(1.0, 0.2, 0.1); glutSolidSphere(max(1, scale),     8, 6)
    glPopMatrix()

# ---------- Spawning & AI ----------
def spawn_enemy_in_lane(lane_index, at_y):
    if len(enemies) >= max_enemies:
        return

    enemy_type = random.choice(["car", "bike"])
    color = COLOR_ENEMY_CAR if enemy_type == "car" else COLOR_ENEMY_BIKE

    # Rubber-band: faster if far ahead of player, slightly slower if very close
    gap = at_y - player_pos[1]
    band = clamp((gap - 400.0) / 1200.0, -0.6, 0.9)

    speed_mod = min(1.0, player_speed / max(1.0, player_max_speed))
    aggressive_speed = enemy_base_speed + random.uniform(-0.4, 0.8) + speed_mod * 1.8 + band * 2.0

    e = {
        "lane": lane_index,
        "pos": [lane_x(lane_index), at_y, 0.0],
        "alive": True,
        "hits": 0,
        "explode_t": 0,
        "speed": aggressive_speed,
        "type": enemy_type,
        "block_cd": 0,                 # cooldown before trying to block again
        "signal_timer": 0,             # telegraph lane change
        "attack_timer": random.randint(60, 160),
        "color": color,
        "brake_timer": 0
    }
    enemies.append(e)

def spawn_wave_ahead():
    spawn_y = player_pos[1] + 900
    count = random.randint(1, 3)
    lanes = list(range(LANE_COUNT))
    random.shuffle(lanes)
    for i in range(count):
        spawn_enemy_in_lane(lanes[i], spawn_y + i * 140)

def enemy_ai_step(e):
    # random brief braking to create variability (but not unfair)
    if e["brake_timer"] > 0:
        e["brake_timer"] -= 1
        dy = 0.4 * e["speed"]
    else:
        dy = e["speed"]
        if random.random() < 0.004:
            e["brake_timer"] = random.randint(15, 30)

    e["pos"][1] += dy

    # Smooth lane centering
    target_x = lane_x(e["lane"])
    dx_lane = target_x - e["pos"][0]
    if abs(dx_lane) > 0.5:
        e["pos"][0] += 1.2 * math.copysign(1, dx_lane)

    # Telegraph lane change: brief signal period before snapping target lane (keeps motion smooth)
    if e["signal_timer"] > 0:
        e["signal_timer"] -= 1

    # "Attack" logic with cooldowns to keep it fair
    e["attack_timer"] -= 1
    if e["attack_timer"] <= 0:
        e["attack_timer"] = random.randint(80, 200)
        # attempt to align to player's lane only if not already very close to player
        if abs(e["pos"][1] - player_pos[1]) > 60 and random.random() < 0.65:
            if e["lane"] != player_lane:
                e["lane"] = player_lane
                e["signal_timer"] = 20  # telegraph

    # Blocking when player approaches from behind (with cooldown)
    same_lane = (e["lane"] == player_lane)
    dy_to_player = player_pos[1] - e["pos"][1]  # >0 if player behind
    if e["block_cd"] > 0:
        e["block_cd"] -= 1
    if same_lane and 0 < dy_to_player < 140 and e["block_cd"] == 0:
        # 50/50 chance to dodge into adjacent lane (if exists) instead of hard block -> fairer
        if random.random() < 0.5:
            target_lane = e["lane"] + (1 if e["lane"] == 0 else -1 if e["lane"] == 2 else random.choice([-1,1]))
            target_lane = clamp(target_lane, 0, LANE_COUNT-1)
            if target_lane != e["lane"]:
                e["lane"] = target_lane
                e["signal_timer"] = 16
        e["block_cd"] = 70

    # Cleanup far behind player
    if e["pos"][1] < player_pos[1] - SPAWN_CLEANUP_BEHIND:
        e["alive"] = False

# ---------- Update Loop ----------
def update_bullets():
    dead = []
    for i,b in enumerate(bullets):
        rad = math.radians(b["angle"])
        b["pos"][0] += b["speed"] * math.cos(rad)
        b["pos"][1] += b["speed"] * math.sin(rad)
        b["ttl"] -= 1
        if (b["ttl"] <= 0 or 
            abs(b["pos"][0]) > MAP_WIDTH/2 or 
            abs(b["pos"][1] - player_pos[1]) > 2200):
            dead.append(i)
    for i in reversed(dead):
        bullets.pop(i)

def update_enemies():
    global life, game_over, score
    for e in enemies:
        if e["alive"]:
            enemy_ai_step(e)

            # Collision with player (slightly smaller hitbox for fairness)
            if dist2_xy(e["pos"], player_pos) <= (44+44)**2:
                life -= 1
                e["pos"][1] -= 140
                e["block_cd"] = 50
                if life <= 0:
                    life = 0
                    game_over = True

            # bullets
            for b in bullets:
                if dist2_xy(b["pos"], e["pos"]) <= (38)**2:
                    b["ttl"] = 0
                    e["hits"] += 1
                    if e["hits"] >= enemy_hits_to_die:
                        e["alive"] = False
                        e["explode_t"] = 30
                        if life < max_life:
                            life += 1
                        score += 200
        else:
            if e["explode_t"] > 0:
                e["explode_t"] -= 1

    # remove finished explosions and far-behind
    remove_idx = []
    for i, e in enumerate(enemies):
        if (not e["alive"] and e["explode_t"] <= 0) or (e["pos"][1] < player_pos[1] - SPAWN_CLEANUP_BEHIND and e["explode_t"] <= 0):
            remove_idx.append(i)
    for i in reversed(remove_idx):
        enemies.pop(i)

def draw_speedometer():
    bar_w = 300
    bar_h = 18
    cx = WIN_W // 2
    cy = 30
    left = cx - bar_w//2
    right = cx + bar_w//2
    norm = (player_speed - (-6.0)) / (player_max_speed - (-6.0))
    norm = clamp(norm, 0.0, 1.0)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(0.15, 0.15, 0.15)
    glBegin(GL_QUADS)
    glVertex2f(left, cy - bar_h//2)
    glVertex2f(right, cy - bar_h//2)
    glVertex2f(right, cy + bar_h//2)
    glVertex2f(left, cy + bar_h//2)
    glEnd()

    fill_w = int(bar_w * norm)
    glColor3f(0.2, 0.7, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(left + 2, cy - bar_h//2 + 2)
    glVertex2f(left + 2 + fill_w, cy - bar_h//2 + 2)
    glVertex2f(left + 2 + fill_w, cy + bar_h//2 - 2)
    glVertex2f(left + 2, cy + bar_h//2 - 2)
    glEnd()

    draw_text(cx - 80, cy + 20, f"Speed: {player_speed:.1f} / {player_max_speed:.1f}")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_distance_hud():
    km = total_distance / 1000.0
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    draw_text(WIN_W - 260, WIN_H - 30, f"Distance: {int(total_distance)} m  ({km:.2f} km)")
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_player_motion():
    global road_scroll, score, total_distance
    player_pos[1] += player_speed
    road_scroll += player_speed

    # clamp within road, then auto-snap toward lane center
    player_pos[0] = clamp(player_pos[0], -ROAD_WIDTH/2 + 20, ROAD_WIDTH/2 - 20)
    target_x = lane_x(player_lane)
    dx = target_x - player_pos[0]
    if abs(dx) > 1.0:
        player_pos[0] += math.copysign(min(8.0, abs(dx)), dx)
    else:
        player_pos[0] = target_x

    # score & distance scale with forward motion only
    forward = max(0.0, player_speed)
    score += int(0.2 * forward)
    total_distance += forward

def spawn_manager():
    """
    Maintain target density ahead of player; scaled by difficulty (time & distance).
    """
    # difficulty scaling
    difficulty = clamp((time.time() - game_start_time) / 60.0 + total_distance / 5000.0, 0.0, 2.0)
    target_density = ENEMY_DENSITY * (1.0 + 0.35 * difficulty)

    window_len = SPAWN_AHEAD_MAX - SPAWN_AHEAD_MIN
    desired_count = max(1, int(window_len * target_density))

    ahead_min = player_pos[1] + SPAWN_AHEAD_MIN
    ahead_max = player_pos[1] + SPAWN_AHEAD_MAX

    current_count = 0
    for e in enemies:
        if e["alive"] and ahead_min <= e["pos"][1] <= ahead_max:
            current_count += 1

    to_spawn = desired_count - current_count
    if to_spawn > 0:
        to_spawn = min(to_spawn, 2)
        for _ in range(to_spawn):
            lane = random.randint(0, LANE_COUNT-1)
            y = random.uniform(ahead_min, ahead_max)
            spawn_enemy_in_lane(lane, y)

    global spawn_timer, enemy_base_speed
    spawn_timer += 1

    # faster spawn when player is faster
    spawn_rate = max(20, enemy_spawn_frames - int(player_speed / 2))
    if spawn_timer >= spawn_rate:
        spawn_timer = 0
        spawn_wave_ahead()

    # enemies get slightly faster over time (cap)
    enemy_base_speed = clamp(2.0 + 0.15 * difficulty, 2.0, 4.2)

def check_game_time():
    global game_over
    elapsed_time = time.time() - game_start_time
    if elapsed_time >= game_duration:
        game_over = True

# ---------- Input Handlers ----------
def keyboardListener(key, x, y):
    global player_speed, muzzle_timer, turret_angle, life, game_over, score, camera_mode
    global camera_distance, camera_height, sky_transition

    if isinstance(key, bytes):
        key = key.decode('utf-8')

    # Camera controls
    if key == 'w':
        camera_height += 10
    elif key == 's':
        camera_height -= 10
    elif key == 'a':
        camera_distance -= 10
    elif key == 'd':
        camera_distance += 10
    elif key == 'v':
        camera_mode = MODE_FIRST_PERSON if camera_mode == MODE_REGULAR else MODE_REGULAR
    # Day/night cycle controls
    elif key == 'n':
        sky_transition = clamp(sky_transition + SKY_STEP, 0, 1)
    elif key == 'm':
        sky_transition = clamp(sky_transition - SKY_STEP, 0, 1)

    if game_over:
        if key == 'r':
            reset_game()
        return

    # Fire
    if key == ' ':
        mx = player_pos[0]
        my = player_pos[1] + 60
        mz = player_pos[2] + 25
        bullets.append({
            "pos":[mx, my, mz],
            "angle": 90.0,
            "speed": bullet_speed,
            "ttl": bullet_ttl
        })
        muzzle_timer = 6
        score = max(0, score - 1)
    elif key == 'r':
        reset_game()

def specialKeyListener(key, x, y):
    global player_lane, player_speed
    if game_over:
        return
    if key == GLUT_KEY_UP:
        player_speed += player_acc
        player_speed = clamp(player_speed, -6.0, player_max_speed)
    elif key == GLUT_KEY_DOWN:
        player_speed -= player_acc
        player_speed = clamp(player_speed, -6.0, player_max_speed)
    elif key == GLUT_KEY_LEFT:
        if player_lane > 0:
            player_lane -= 1
    elif key == GLUT_KEY_RIGHT:
        if player_lane < LANE_COUNT-1:
            player_lane += 1

# ---------- Camera ----------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 6000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if camera_mode == MODE_REGULAR:
        cam_x = player_pos[0] - camera_distance * 0.02
        cam_y = player_pos[1] - camera_distance
        cam_z = player_pos[2] + camera_height
        gluLookAt(cam_x, cam_y, cam_z,
                  player_pos[0], player_pos[1] + 160, player_pos[2],
                  0, 0, 1)
    else:
        cam_x = player_pos[0]
        cam_y = player_pos[1] + 40
        cam_z = player_pos[2] + 30
        gluLookAt(cam_x, cam_y, cam_z,
                  player_pos[0], player_pos[1] + 220, player_pos[2],
                  0, 0, 1)

def setup_fog():
    # linear fog to fade into horizon -> "infinite" feel
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_LINEAR)
    # Use sky color for fog
    day_fog = (0.50, 0.75, 1.0)
    night_fog = (0.03, 0.06, 0.15)
    t = clamp(sky_transition, 0.0, 1.0)
    fog_color = vec_lerp(day_fog, night_fog, t)
    fogColor = (GLfloat * 4)(*fog_color, 1.0)
    glFogfv(GL_FOG_COLOR, fogColor)
    glFogf(GL_FOG_START, VIEW_DISTANCE * 0.55)
    glFogf(GL_FOG_END,   VIEW_DISTANCE * 0.95)
    glHint(GL_FOG_HINT, GL_NICEST)

# ---------- Idle (Game Loop) ----------
def idle():
    global frames, muzzle_timer
    if not game_over:
        frames += 1
        update_bullets()
        update_enemies()
        update_player_motion()
        spawn_manager()
        check_game_time()
        if muzzle_timer > 0:
            muzzle_timer -= 1
            
    # Clouds + flocks animate
    for c in clouds:
        c["x"] += c["speed"]
        if c["x"] > 1.3: c["x"] = -0.4
    for flock in bird_flocks:
        L = flock["leader"]; L["x"] += L["speed"]; L["flap"] += 0.2
        if L["x"] > 1.25: L["x"] = -0.25
        for m in flock["members"]: m["flap"] += 0.25
        
    glutPostRedisplay()

# ---------- Rendering ----------
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)

    # Draw sky (2D overlay)
    draw_sky()
    
    setupCamera()
    setup_fog()

    # Road & environment
    draw_road()

    # Enemies
    for e in enemies:
        if e["alive"]:
            if e["type"] == "car":
                draw_car_at(e["pos"], e["color"], with_turret=False, turret_deg=0)
            else:
                draw_bike_at(e["pos"], e["color"])
        else:
            if e["explode_t"] > 0:
                draw_explosion(e)

    # Bullets
    for b in bullets:
        draw_bullet(b)

    # Player
    draw_car_at(player_pos, COLOR_PLAYER, with_turret=True, turret_deg=turret_angle)

    # Muzzle flash
    if muzzle_timer > 0:
        glColor3f(1.0, 0.9, 0.1)
        glPushMatrix()
        glTranslatef(player_pos[0], player_pos[1] + 60, player_pos[2] + 25)
        glutSolidSphere(6, 8, 8)
        glPopMatrix()

    # HUD
    elapsed_time = time.time() - game_start_time
    time_left = max(0, game_duration - elapsed_time)
    minutes = int(time_left // 60)
    seconds = int(time_left % 60)

    draw_text(10, WIN_H - 30, f"Lives: {life}/{max_life}   Score: {score}   Lane: {player_lane+1}")
    draw_text(10, WIN_H - 60, f"Time: {minutes:02d}:{seconds:02d}")
    draw_text(10, WIN_H - 90, "Controls: Arrows to move  |  Space: Fire  |  V: Toggle view  |  R: Restart")
    draw_text(10, WIN_H - 120, "WASD: Camera height/distance  |  N/M: Day/Night cycle")
    draw_speedometer()
    draw_distance_hud()

    if game_over:
        if life <= 0:
            draw_text(WIN_W//2 - 70, WIN_H//2 + 40, "GAME OVER")
            draw_text(WIN_W//2 - 110, WIN_H//2, "You ran out of lives!")
        else:
            draw_text(WIN_W//2 - 70, WIN_H//2 + 40, "TIME'S UP!")
            draw_text(WIN_W//2 - 110, WIN_H//2, f"Final Score: {score}")
        draw_text(WIN_W//2 - 140, WIN_H//2 - 40, "Press 'R' to restart")

    glutSwapBuffers()

# ---------- Reset & Init ----------
def reset_game():
    global player_lane, player_pos, player_speed, turret_angle, bullets, enemies
    global life, score, game_over, frames, spawn_timer, road_scroll, camera_mode
    global camera_distance, camera_height, game_start_time, total_distance
    global enemy_base_speed, sky_transition

    player_lane = 1
    player_pos = [lane_x(player_lane), 0.0, 0.0]
    player_speed = 0.0
    turret_angle = 0.0
    bullets = []
    enemies = []
    life = max_life
    score = 0
    game_over = False
    frames = 0
    spawn_timer = 0
    road_scroll = 0
    camera_mode = MODE_REGULAR
    camera_distance = 220
    camera_height = 120
    total_distance = 0.0
    enemy_base_speed = 2.0
    sky_transition = 0.0  # Start at daytime
    game_start_time = time.time()

    # Initialize environment
    init_environment()

    # initial wave
    for i in range(3):
        spawn_enemy_in_lane(random.randint(0, LANE_COUNT-1), player_pos[1] + 800 + i*220)

def init_opengl():
    glClearColor(0.5, 0.75, 1.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 30)
    glutCreateWindow(b"Road Rush: Driving Simulation")

    init_opengl()
    reset_game()

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()