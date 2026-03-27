import curses
import time

# object types
BASE = 0
DRAWABLE = 1

# color codes
WHITE = 0
RED = 1
BLACK = 2

# state codes
MENU = 0
QUIT = 1
EDIT = 2
PLAYING = 3
VICTORY = 4
GAMEOVER = 5

# framerate limiter constants
FIXED_DT = 1000.0 / 30.0
MAX_FRAME_TIME = 100.0
FRAME_TIME = 33.0

# event types
KEY = 0
FOCUS = 1
HIDE = 2

class Event:
    def __init__(self, type, data):
        self.type = type
        self.data = data

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

    def __init__(self, ID, type):
        self.ID = ID
        self.type = type

class Drawable(Object):

    def __init__(self, ID, is_visible, renderer):
        super().__init__(ID, DRAWABLE)
        self.is_visible = is_visible
        self.renderer = renderer

#    def draw(self):
        # draw itself

class ObjectContainer:

    def __init__(self):
        self.map = {}
        self.visible = []
        self.focusable = []
        self.in_focus = []

    def add_object(self, object, can_receive_focus):
        self.map[object.ID] = object
        if object.type == DRAWABLE and object.is_visible:
            self.visible.append(object.ID)
        if can_receive_focus:
            self.focusable.append(object.ID)

    def remove_object_by_id(self, ID):
        if not self.map.get(ID):
            return
        del self.map[ID]
        try:
            self.visible.remove(ID)
            self.focusable.remove(ID)
            self.in_focus.remove(ID)
            return
        except:
            return

    def get_object_by_id(self, ID):
        return self.map.get(ID)

    def draw(self):
        for i in range(0, len(self.visible)):
            self.map.get(self.visible[i]).draw()

    def show_object(self, ID):
        if not self.map.get(ID):
            return
        try:
            index = self.visible.index(ID)
        except:
            self.visible.append(ID)

    def hide_object(self, ID):
        if not self.map.get(ID):
            return
        try:
            index = self.visible.index(ID)
            del self.visible[index]
        except:
            return

    def get_focused(self):
        return self.in_focus

    def focus_by_id(self, ID):
        if len(self.focusable) < 1:
            return
        if not self.map.get(ID):
            return
        self.in_focus.append(ID)
        self.map.get(ID).handle(Event(FOCUS, True))

    def unfocus_by_id(self, ID):
        if len(self.in_focus) < 1:
            return
        if not self.map.get(ID):
            return
        try:
            index = self.in_focus.index(ID)
            self.in_focus[index].handle(Event(FOCUS, False))
            del self.in_focus[index]
        except:
            return

    def unfocus_all(self):
        for i in range(0, len(self.in_focus)):
            self.in_focus[i].handle(Event(FOCUS, False))
        self.in_focus.clear()

    def focus_next(self):
        for i in range(0, len(self.in_focus)):
            self.map.get(self.in_focus[i]).handle(Event(FOCUS, False))

        if not self.in_focus:
            index = 0
        else:
            index = self.focusable.index(self.in_focus[-1])
            if index == len(self.focusable) - 1:
                index = 0
            else:
                index += 1
        self.in_focus.clear()
        self.in_focus.append(self.focusable[index])
        self.map.get(self.focusable[index]).handle(Event(FOCUS, True))


    def handle(self, event):
        if self.in_focus:
            for i in range(0, len(self.in_focus)):
                self.map.get(self.in_focus[i]).handle(event)

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

class Border:

    def __init__(self, is_visible, renderer, rect, color=WHITE):
        self.is_visible = is_visible
        self.renderer = renderer
        self.rect = rect
        self.color = color

    def draw(self):
        if not self.is_visible:
            return
        self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y), self.color)
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y), self.color)
        self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W, self.rect.Y), self.color)
        for i in range(self.rect.Y + 1, self.rect.Y + self.rect.H - 1):
            self.renderer.draw_text("|", Vector2D(self.rect.X + self.rect.W, i), self.color)
            self.renderer.draw_text("|", Vector2D(self.rect.X, i), self.color)
        self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W, self.rect.Y + self.rect.H - 1), self.color)
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y + self.rect.H - 1), self.color)
        self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y + self.rect.H - 1), self.color)

class TextBox(Drawable):

    def __init__(self, ID, placeholder, dimensions, renderer, is_visible, color=0, border=None, border_color=None, allowed=""):
        super().__init__(ID, is_visible, renderer)
        self.rect = dimensions
        if border and self.rect.H < 3:
            self.rect.H = 3
        if border and self.rect.W < 3:
            self.rect.W = 3
        self.border = Border(True, self.renderer, self.rect)
        if not border:
            self.border.is_visible = False
        if border_color:
            self.border.color = border_color
        else:
            self.border.color = color
        self.color = color
        self.placeholder = placeholder
        self.renderer = renderer
        self.text = ""
        self.has_text = False
        self.cursor_pos = Vector2D(0, 0)
        self.is_visible = is_visible
        self.allowed = allowed

    def draw(self):
        if not self.is_visible:
            return
        
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

    def handle(self, event):
        if event.type == KEY:
            key = event.data
            if key == curses.KEY_BACKSPACE or key == 127:
                if not self.has_text:
                    return
                self.text = self.remove_char_at_index(self.text, self.cursor_pos.X - 1)
                self.cursor_pos.X -= 1
                if len(self.text) == 0:
                    self.has_text = False
            elif key == curses.KEY_DC or key == 127:
                if not self.has_text:
                    return
                self.text = self.remove_char_at_index(self.text, self.cursor_pos.X)
                if self.cursor_pos.X > len(self.text):
                    self.cursor_pos.X -= 1
                if len(self.text) == 0:
                    self.has_text = False
            elif 31 < key < 127:
                if self.allowed and chr(key) not in self.allowed:
                    return
                if len(self.text) == self.rect.W - 2:
                    return
                self.text = self.add_char_at_index(self.text, chr(key), self.cursor_pos.X)
                self.cursor_pos.X += 1
                self.has_text = True
        elif event.type == FOCUS:
            if event.data == True:
                self.border_color = RED
            else:
                self.border_color = WHITE
        elif event.type == HIDE:
            if event.type == True:
                self.is_visible = False
            else:
                self.is_visible = True

class EditableBuffer(Drawable):

    def __init__(self, ID, dimensions, is_visible, renderer, texture_ID=None)
        super().__init__(ID, is_visible, renderer)
        self.rect = dimensions
        self.texture_manager = renderer.texture_manager
        self.texture_ID = texture_ID
        self.border_color = WHITE
        if not texture_ID:
            self.texture_manager.save_texture(Texture(-99, self.rect.W, self.rect.H, [[]]))
            self.texture_UD = -99

        elif not self.texture_manager.get_texture(texture_ID):
            self.texture_manager.save_texture(Texture(texture_ID, self.rect.W, self.rect.H, [[]]))

        else:
            self.rect.W = self.texture_manager.get_texture(self.texture_ID).size.X
            self.rect.H = self.texture_manager.get_texture(self.texture_ID).size.Y

    def draw(self):
        self.renderer.draw(self.texture_ID, Vector2D(self.rect.X, self.rect.Y))

    def draw_border(self):
        self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y), self.border_color)
        self.renderer.draw_text("+", Vector2D(self.rect.X, self.rect.Y + self.rect.W - 1), self.border_color)
        self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W - 1, self.rect.Y), self.border_color)
        self.renderer.draw_text("+", Vector2D(self.rect.X + self.rect.W - 1, self.rect.Y + self.rect.H - 1), self.border_color)
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y), self.border_color)
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y + self.rect.H - 1), self.border_color)
        for i in range(self.rect.Y + 1, self.rect.Y + self.rect.H - 1):
            self.renderer.draw_text("|", Vector2D(self.rect.X + self.rect.W, i), self.border_color)
            self.renderer.draw_text("|", Vector2D(self.rect.X, i), self.border_color)

    def handle(self, event):
        if event.type == FOCUS:
            if event.data == True:
                self.border_color = RED
            else:
                self.border_color = WHITE

class QuitButton(Drawable):

    def __init__(self, ID, is_visible, renderer, pos):
        super().__init__(ID, is_visible, renderer)
        self.rect = Rect(pos.X, pos.Y, 6, 3)
        self.is_quiting = False
        self.border_color = WHITE

    def draw(self):
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y), self.border_color)
        self.renderer.draw_text("-" * (self.rect.W - 2), Vector2D(self.rect.X + 1, self.rect.Y + self.rect.H - 1), self.border_color)
        self.renderer.draw_text("|", Vector2D(self.rect.X, self.rect.Y + 1), self.border_color)
        self.renderer.draw_text("|", Vector2D(self.rect.X + self.rect.W, self.rect.Y + 1), self.border_color)
        self.renderer.draw_text("Quit", Vector2D(self.rect.X + 1, self.rect.Y + 1), WHITE)

    def handle(self, event):
        if event.type == FOCUS:
            if event.data == True:
                self.border_color = RED
            else:
                self.border_color = WHITE
        elif event.type == KEY:
            if event.data == ord('q') or event.data == 27 or event.data == ord("\n"):
                self.is_quiting = True

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
        Object("avude♠", BASE)
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
    FILE = 0
    WIDTH = 1
    HEIGHT = 2
    EDITING = 3

    def __init__(self, engine, window, texture_manager, clock, renderer):
        self.window = window
        self.renderer = renderer
        self.engine = engine
        self.texture_manager = texture_manager
        self.clock = clock
        self.texture = None
        self.objects = ObjectContainer()
        self.stage = self.FILE

    def init(self):
        self.objects.add_object(TextBox("filepath", "Enter the texture filepath", Rect(10, 10, 50, 3), self.renderer, True, WHITE, True, WHITE), True)
        self.objects.add_object(QuitButton("quit_button", True, self.renderer, Vector2D(168, 0)), True)
        self.objects.focus_by_id("filepath")

    def update(self, delta_time):
        key = self.window.getch()
        if key == 27:
            self.engine.stop()
            return EDIT
        if key == 9:
            self.objects.focus_next()
        if not self.objects.in_focus:
            return EDIT
        if self.objects.get_object_by_id("quit_button").is_quiting:
            self.engine.stop()
            return EDIT

        if self.stage == self.FILE:
            if key == ord("\n") and "filepath" in self.objects.in_focus:
                filepath = self.objects.get_object_by_id("filepath").text
                if not filepath:
                    return EDIT
                self.objects.remove_object_by_id("filepath")
                if self.load_texture(filepath):
                    self.stage = self.EDITING
                    return EDIT
                self.objects.add_object(TextBox("width", "Enter the texture width", Rect(10, 10, 50, 3), self.renderer, True, WHITE, True, WHITE, "0123456789"), True)
                self.objects.focus_by_id("width")
                self.stage = self.WIDTH
                return EDIT

        elif self.stage == self.WIDTH:
            if key == ord("\n") and "width" in self.objects.in_focus:
                text = self.objects.get_object_by_id("width").text
                if not text:
                    return EDIT
                self.texture.size.X = int(text)
                self.objects.remove_object_by_id("width")
                self.objects.add_object(TextBox("height", "Enter the texture height", Rect(10, 10, 50, 3), self.renderer, True, WHITE, True, WHITE, "0123456789"), True)
                self.objects.focus_by_id("height")
                self.stage = self.HEIGHT
                return EDIT

        elif self.stage == self.HEIGHT:
            if key == ord("\n") and "height" in self.objects.in_focus:
                text = self.objects.get_object_by_id("height").text
                if not text:
                    return EDIT
                self.texture.size.Y = int(text)
                self.objects.remove_object_by_id("height")
                self.engine.stop()
                self.stage = self.EDITING
                return EDIT

#        elif self.stage == self.EDITING:
#            

        self.objects.handle(Event(KEY, key))
        return EDIT

    def render(self, interpol_ref):
        self.objects.draw()

    def finalise(self):
        print("a")

    def load_texture(self, filepath):
        if self.texture_manager.load_texture(-99, filepath):
            self.texture = self.texture_manager.get_texture(-99)
            return True
        else:
            self.texture = Texture(0, 0, [[]])
            return False

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
