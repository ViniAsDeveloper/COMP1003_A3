import curses

MENU = 0
QUIT = 1
PLAYING = 2
VICTORY = 3
GAMEOVER = 4

class MenuState:
    def __init__(self, window):
        self.window = window

    def init(self):
        print("a")

    def updtate(self, delta_time):
        print("a")

    def render(self):
        print("a")

    def finalise(self):
        print("a")

states = [ MenuState ]

class Engine:
    current_state_code = MENU
    def __init__(self):
        self.current_state = states[self.current_state_code]("avude")
        self.current_state.init()

avude = Engine()
