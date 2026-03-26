import curses
import time

WHITE = 0
RED = 1
BLACK = 2

MENU = 0
QUIT = 1
EDIT = 2
PLAYING = 3
VICTORY = 4
GAMEOVER = 5

FIXED_DT = 1000.0 / 30.0
MAX_FRAME_TIME = 100.0
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

    def draw(self, texture_ID, pos, src_rect=None):
        texture = self.texture_manager.get_texture(texture_ID)
        if texture:
            if not src_rect:
                src_rect = Rect(0, 0, texture.size.X, texture.size.Y)
            for i in range(0, src_rect.H):
                for j in range(0, src_rect.W):
                    if src_rect.X + j > texture.size.X:
                        break
                    self.window.addch(pos.Y + i, pos.X + j, texture.pixel_matrix[src_rect.Y + i][src_rect.X + j].char, curses.color_pair(texture.pixel_matrix[src_rect.Y + i][src_rect.X + j].color))
                if src_rect.Y + i > texture.size.Y:
                    break

    def draw_text(self, text, pos, color):
        self.window.addstr(pos.Y, pos.X, text, curses.color_pair(color))

#    def draw_frame(self, texture_ID, pos, sprite_sizea, sprite_frame):
#        

class TextBox:
    def __init__(self, placeholder, dimensions, renderer, color=0, border=None, border_color=None):
        self.rect = dimensions
        if border and self.rect.H < 3:
            self.rect.H = 3
        if border and self.rect.W < 3:
            self.rect.W = 3
        self.has_border = border
        if border_color:
            self.border_color = border_color
        else:
            self.border_color = color
        self.color = color
        self.placeholder = placeholder
        self.renderer = renderer
        self.text = ""
        self.has_text = False
        self.cursor_pos = Vector2D(0, 0)

    def draw(self):
        if self.has_border:
            self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y), self.border_color)
            self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y), self.border_color)
            self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W, self.rect.Y), self.border_color)
            for i in range(self.rect.Y + 1, self.rect.Y + self.rect.H - 1):
                self.renderer.draw_text("|", Vector2D(self.rect.X + self.rect.W, i), self.border_color)
                self.renderer.draw_text("|", Vector2D(self.rect.X, i), self.border_color)
            self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W, self.rect.Y + self.rect.H - 1), self.border_color)
            self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y + self.rect.H - 1), self.border_color)
            self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y + self.rect.H - 1), self.border_color)
            if not self.has_text:
                self.renderer.draw_text(self.placeholder, Vector2D(self.rect.X + 1, self.rect.Y + 1), self.color)
                return
            self.renderer.draw_text(self.text, Vector2D(self.rect.X + 1, self.rect.Y + 1), self.color)
            return
        if not self.has_text:
            self.renderer.draw_text(self.placeholder, Vector2D(self.rect.X + 1, self.rect.Y + 1), self.color)
            return
        self.renderer.draw_text(self.text, Vector2D(self.rect.X + 1, self.rect.Y + 1), self.color)

    def add_char(self, char, index=None):
        if index:
            self.text = add_char_at_index(self.text, char, index)
            return
        self.has_text = True
        self.text += char

    def backspace(self):
        self.text = remove_char_at_index(self.text, len(self.text) - 1)

    def add_char_at_index(self, text, char, index):
        return text[:index] + char + text[index:]

    def remove_char_at_index(self, text, index):
        return text[:index] + text[index+1:]

    def process(self, key):
        if key == curses.KEY_BACKSPACE:
            if not self.has_text:
                return
            self.text = self.remove_char_at_index(self.text, self.cursor_pos.X - 1)
            self.cursor_pos.X -= 1
            if len(self.text) == 0:
                self.has_text = False
        elif key == curses.KEY_DC:
            if not self.has_text:
                return
            self.text = self.remove_char_at_index(self.text, self.cursor_pos.X)
            if self.cursor_pos.X > len(self.text):
                self.cursor_pos.X -= 1
            if len(self.text) == 0:
                self.has_text = False
        elif 31 < key < 127:
            self.text = self.add_char_at_index(self.text, chr(key), self.cursor_pos.X)
            self.cursor_pos.X += 1
            self.has_text = True

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
        elif key == ord('e'):
            return EDIT
        self.text = str(time.perf_counter_ns())
        if self.clock.is_over(-99):
            self.FPS_text = self.FPS
            self.FPS = 0
        return MENU

    def render(self, interpol_ref):
        for object in self.objects:
            self.window.addstr(3, 0, object.ID, curses.color_pair(0))
        self.window.addstr(2, 0, self.text)
        for i in range(0, 10):
            self.renderer.draw("avude", Vector2D(6, 5))
        self.window.addstr(4, 0, str(self.FPS_text))
        self.FPS += 1

    def finalise(self):
        print("a")

class Edit:
    def __init__(self, engine, window, texture_manager, clock, renderer):
        self.window = window
        self.renderer = renderer
        self.engine = engine
        self.texture_manager = texture_manager
        self.clock = clock

    def init(self):
        self.selected = None
        self.textbox = TextBox("Enter texture file name", Rect(10, 10, 50, 3), self.renderer, RED, True)

    def update(self, delta_time):
        key = self.window.getch()
        if key == ord('q') and str(self.selected) != str(self.textbox):
            self.engine.stop()
            return EDIT
        if key == 27:
            self.engine.stop()
            return EDIT
        if key == 9:
            if str(self.selected) == str(self.textbox):
                logger.log("Tab pressed")
                self.selected = None
            else:
                self.selected = self.textbox
        if self.selected == self.textbox:
            self.textbox.process(key)
        return EDIT

    def render(self, interpol_ref):
        self.textbox.draw()

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

states = [ MenuState, Quit, Edit ]

class Engine:
    current_state_code = MENU
    is_running = True
    time = 0
    texture_manager = TextureManager()
    clock = Clock()
    def __init__(self, window):
        self.window = window
        self.window.nodelay(True)
        self.renderer = Renderer(window, self.texture_manager)
        self.current_state = states[self.current_state_code](self, window, self.texture_manager, self.clock, self.renderer)
        curses.start_color()
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
            frame_start = time.perf_counter_ns() / 1_000_000
            frame_time = frame_start - previous_time
            previous_time = frame_start
            frame_time = min(frame_time, MAX_FRAME_TIME)
            accumulator += frame_time

            while accumulator >= FIXED_DT:
                self.update(FIXED_DT)
                accumulator -= FIXED_DT
            alpha = accumulator / FIXED_DT
            self.render(alpha)
            frame_end = time.perf_counter_ns() / 1_000_000
            elapsed = frame_end - frame_start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                curses.napms(int(sleep_time))
            else:
                curses.napms(1)
        self.current_state.finalise()

    def change_state(self, next_state):
        self.current_state.finalise()
        self.window.clear()
        self.current_state_code = next_state
        self.current_state = states[next_state](self, self.window, self.texture_manager, self.clock, self.renderer)
        self.current_state.init()

    def stop(self):
        self.is_running = False

def main(window):
    engine = Engine(window)
    engine.run()

curses.wrapper(main)
