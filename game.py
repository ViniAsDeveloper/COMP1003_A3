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
MAX_FRAME_TIME = 50.0
FRAME_TIME = 33.0

class Logger:
    def __init__(self):
        self.file = open("main.log", "a")

    def log(self, text):
        self.file.write(str(text) + "\n")

logger = Logger()

class Timer:
    def __init__(self, time_ms, repeat):
        self.start_time = time.perf_counter_ns()
        self.time_ns = time_ms * 1_000_000
        self.repeat = repeat
        self.is_over = False

class Clock:
    def __init__(self):
        self.init_time = time.perf_counter_ns()
        self.timers = {}

    def add_timer(self, ID, time_ms, repeat):
        self.timers[ID] = Timer(time_ms, repeat)

    def is_over(self, ID):
        timer = self.timers.get(ID)
        if timer and timer.is_over:
            if timer.repeat:
                timer.is_over = False
                timer.start_time = time.perf_counter_ns()
            return True
        else:
            return False

    def tick(self):
        current_time = time.perf_counter_ns()
        for timer in self.timers.values():
            if timer.start_time + timer.time_ns <= current_time:
                timer.is_over = True

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

class Rect:
    def __init__(self, X, Y, W, H):
        self.X = X
        self.Y = Y
        self.W = W
        self.H = H

    def intersect(self, rect):
        return rect.X < self.X + self.W and self.X < rect.X + rect.W and rect.Y < self.Y + self.H and self.Y < rect.Y + rect.H

class Pixel:
    def __init__(self, char, color):
        self.char = ord(char)
        self.color = color

class Texture:
    pixel_matrix = []
    def __init__(self, width, height, pixel_matrix):
        self.size = Vector2D(width, height)
        self.pixel_matrix = pixel_matrix

class TextureManager:
    def __init__(self):
        self.texture_map = {}

    def save_texture(self, texture_ID, texture):
        self.texture_map[texture_ID] = texture

    def load_texture(self, texture_ID, filepath):
        try:
            file = open(filepath, "r")
            raw_data = file.read()
            file.close()
            lines = raw_data.split("\n")
            rows = int(lines[0])
            cols = int(lines[1])
            pixel_matrix = []
            row = -1
            col = 0
            for i in range(2, len(lines) - 1, 2):
                if i % cols == 2:
                    pixel_matrix.append([])
                    row += 1
                pixel_matrix[row].append(Pixel(lines[i], int(lines[i+1])))
                col += 1
            if row == rows - 1 and col == cols:
                self.texture_map[texture_ID] = Texture(cols, rows, pixel_matrix)
                return True
            else:
                return False
        except:
            return False

    def get_texture(self, texture_ID):
        return self.texture_map.get(texture_ID)

class Renderer:
    def __init__(self, window, texture_manager):
        self.texture_manager = texture_manager
        self.window = window

    def draw(self, texture_ID, pos, src_rect):
        texture = self.texture_manager.get_texture(texture_ID)
        if texture:
            for i in range(0, src_rect.H):
                for j in range(0, src_rect.W):
                    if src_rect.X + j > texture.size.X:
                        break
                    window.addch(pos.X + j, pos.Y + i, texture.pixel_matrix[src_rect.Y + i][src_rect.X + j].char, texture.pixel_matrix[src_rect.Y + i][src_rect.X + j].color)
                if src_rect.Y + i > texture.size.Y:
                    break

#    def draw_frame(self, texture_ID, pos_x, pos_y, sprite_w, sprite_h, sprite_frame):
#        

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
    def __init__(self, engine, window, texture_manager, clock, renderer):
        self.window = window
        self.renderer = renderer
        self.engine = engine
        self.texture_manager = texture_manager
        self.clock = clock
        self.FPS_text = 0

    def init(self):
        self.objects = [
        Object("avude♠")
        ]
        self.text = ""
        self.FPS = 0
        self.clock.add_timer(-99, 1000, True)
#        self.texture_manager.load_texture("avude", "avude.txt")

    def update(self, delta_time):
        key = self.window.getch()
        if key == ord('q'):
            self.engine.stop()
        self.text = str(time.perf_counter_ns())
        if self.clock.is_over(-99):
            self.FPS_text = self.FPS
            self.FPS = 0
        return MENU

    def render(self, interpol_ref):
        for object in self.objects:
            self.window.addstr(3, 0, object.ID, curses.color_pair(0))
        self.window.addstr(2, 0, self.text)
        self.window.addch(1, 0, self.texture_manager.get_texture("avude").pixel_matrix[0][0].char)
        self.window.addstr(4, 0, str(self.FPS_text))
        self.FPS += 1

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
    texture_manager = TextureManager()
    clock = Clock()
    def __init__(self, window):
        self.window = window
        self.window.nodelay(True)
        self.current_state = states[self.current_state_code](self, window, self.texture_manager, self.clock, 0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.texture_manager.load_texture("avude", "avude.txt")

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

        previous_time = time.perf_counter_ns() / 1_000_000
        accumulator = 0.0

        while self.is_running:
            self.clock.tick()
            current_time = time.perf_counter_ns() / 1_000_000
            frame_time = current_time - previous_time
            previous_time = current_time
            frame_time = min(frame_time, MAX_FRAME_TIME)
            accumulator += frame_time

            while accumulator >= FIXED_DT:
                self.update(FIXED_DT)
                accumulator -= FIXED_DT

            alpha = accumulator / FIXED_DT
            self.render(alpha)
            delay = int(FRAME_TIME - (previous_time - time.perf_counter_ns() / 1_000_000))
            logger.log(delay)
            curses.napms(delay)
        self.current_state.finalise()

    def change_state(self, next_state):
        self.current_state.finalise()
        self.current_state_code = next_state
        self.current_state = states[next_state](self, self.window, self.texture_manager, self.clock, 0)

    def stop(self):
        self.is_running = False

def main(window):
    engine = Engine(window)
    engine.run()

curses.wrapper(main)
