import curses
import time

MENU = 0
QUIT = 1
PLAYING = 2
VICTORY = 3
GAMEOVER = 4

FIXED_DT = 1000.0 / 30.0
MAX_FRAME_TIME = 25.0
FRAME_TIME = 32.0

class MenuState:
    def __init__(self, window):
        self.window = window

    def init(self):
        self.text = ""

    def update(self, delta_time):
        self.text = str(time.perf_counter_ns())
        return MENU

    def render(self, interpol_ref):
        self.window.addstr(3, 0, self.text)

    def finalise(self):
        print("a")

class Quit:
    def __init__(self, window):
        self.window = window

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
        self.current_state = states[self.current_state_code](window)
        self.window = window

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
            curses.napms(int(FIXED_DT - frame_time))


    def change_state(self, next_state):
        self.current_state.finalise()
        self.current_state_code = next_state
        self.current_state = states[next_state](self.window)



def main(window):
    engine = Engine(window)
    engine.run()

curses.wrapper(main)
