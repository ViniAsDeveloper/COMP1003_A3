import curses
import time

WHITE = 0
RED = 1
BLACK = 2

MENU = 0
QUIT = 1
PLAYING = 2
VICTORY = 3
GAMEOVER = 4

FIXED_DT = 1000.0 / 30.0
MAX_FRAME_TIME = 25.0
FRAME_TIME = 32.0

class Vector2D:
    def __init__(self, X, Y):
        self.X = X
        self.Y = Y

class Object:
    def __init__(self, ID):
        self.ID = ID

class RigidBody:
    def __init__(self, X=0, Y=0, W=0, H=0, mass=0, gravity=0):
        self.pos = Vector2D(X, Y)
        self.size = Vector2D(W, H)
        self.mass = mass
        self.gravity = gravity
        self.force = Vector2D(0, 0)
        self.acceleration = Vector2D(0, 0)
        self.speed = Vector2D(0, 0)

    def translate(self, X, Y):
        self.X += X
        self.Y += Y

    def apply_force(self, force):
        self.force.X += force.X
        self.force.Y += force.Y

    def deny_force(self):
        self.force.X = 0
        self.force.Y = 0

    def update(self, delta_time):
        self.acceleration.X = self.force.X / mass
        self.acceleration.Y = self.gravity + self.force.Y / mass
        self.speed = Vector2D(self.acceleration.X * delta_time, self.acceleration.Y * delta_time)
        self.pos = Vector2D(self.speed.X * delta_time, self.speed.Y * delta_time)

class Section:
    def __init__(self, pos_x, content, color):
        self.pos_x = pos_x
        self.content = content
        self.color = color

class Line:
    sections = []
    def __init__(self, pos_y, sections):
        self.pos_y = pos_y
        for i in range(0, len(sections)):
            self.sections.append(Section(sections[i][0], sections[i][1], sections[i][2]))

class Texture:
    lines = []
    def __init__(self, data):
        for i in range(0, len(data), 4):
            lines.append

    def edit(self, section, data):
        if -1 < section < len(self.sections):
            self.section[section] = (data[1], data[2], data[3], data[4])

class TextureManager:
    def __init__(self):
        self.texture_map = {}

    def load_texture(self, texture_ID, filepath):
        try:
            file = open(filepath, "r")
            raw_data = file.read()
            data = raw_data.split("\n")
            self.texture_map[texture_ID] = Texture(data)
            return True
        except:
            return False

    def get_texture(self, texture_ID):
        return self.texture_map.get(texture_ID)

class Renderer:
    def __init__(self, window, texture_manager):
        self.window = window
        self.texture_manager = texture_manager

    def draw(self, texture_ID, pos_x, pos_y, sprite_w, sprite_h):
        texture = self.texture_manager.get_texture(texture_ID)
        if texture:
            for i in range(0, len(texture.sections)):
                if texture.sections[i][1] < sprite_h:
                    self.window

#    def draw_frame(self, texture_ID, pos_x, pos_y, sprite_w, sprite_h, sprite_frame):

class Animation:
    def __init__(self, renderer, texture_ID, frames, speed):
        self.renderer = renderer
        self.texture_ID = texture_ID
        self.frames = frames
        self.speed = speed * 1000
        self.sprite_frame = 0

    def update(self):
        self.sprite_frame = (time.perf_counter_ns()/speed) % frames

    def render(self, pos_x, pos_y, sprite_w, sprite_h):
        self.renderer.draw_frame(self.texture_ID. pos_x, pos_y, sprite_w, sprite_h, self.sprite_frame)

class MenuState:
    def __init__(self, engine, window):
        self.window = window
        self.engine = engine

    def init(self):
        self.objects = [
        Object("avude♠")
        ]
        self.text = ""

    def update(self, delta_time):
        key = self.window.getch()
        if key == ord('q'):
            self.engine.stop()
        self.text = str(time.perf_counter_ns())
        return MENU

    def render(self, interpol_ref):
        for object in self.objects:
            self.window.addstr(3, 0, object.ID, curses.color_pair(0))
        self.window.addstr(2, 0, self.text)

    def finalise(self):
        print("a")

class Quit:
    def __init__(self, engine, renderer):
        self.renderer = renderer
        self.engine = engine

    def init(self):
        self.text = ""
        print("init Quit")

    def update(self, delta_time):
        self.text += "#"
        return QUIT

    def finalise(self):
        print("end Quit")

states = [ MenuState, Quit ]

class Engine:
    current_state_code = MENU
    is_running = True
    time = 0
    def __init__(self, window):
        self.window = window
        self.window.nodelay(True)
        self.current_state = states[self.current_state_code](self, window)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

    def update(self, delta_time):
        next_state = self.current_state.update(delta_time)
        if next_state != self.current_state_code:
            self.change_state(next_state)

    def render(self, interpol_ref): # reference for linear interpolation between positions in frames
        self.window.erase()
        self.current_state.render(interpol_ref)
        self.window.refresh()

    def run(self):
        self.current_state.init()

        previous_time = time.perf_counter_ns() / 1000
        accumulator = 0.0

        while self.is_running:
            current_time = time.perf_counter_ns() / 1000
            frame_time = current_time - previous_time
            previous_time = current_time
            frame_time = min(frame_time, MAX_FRAME_TIME)
            accumulator += frame_time

            while accumulator >= FIXED_DT:
                self.update(FIXED_DT)
                accumulator -= FIXED_DT

            alpha = accumulator / FIXED_DT
            self.render(alpha)
            curses.napms(int(FRAME_TIME - frame_time))
        self.current_state.finalise()

    def change_state(self, next_state):
        self.current_state.finalise()
        self.current_state_code = next_state
        self.current_state = states[next_state](self, self.window)

    def stop(self):
        self.is_running = False

def main(window):
    engine = Engine(window)
    engine.run()

curses.wrapper(main)
