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

    def update(self, delta_time):
        print("a")
        return MENU

    def render(self):
        print("b")

    def finalise(self):
        print("a")

states = [ MenuState ]

class Engine:
    current_state_code = MENU
    is_running = True
    def __init__(self, window):
        self.current_state = states[self.current_state_code](window)
        self.window = window

    def update(self, delta_time):
        next_state = self.current_state.update(delta_time)
        if next_state != self.current_state_code:
            self.change_state(next_state)

    def render(self):
        self.current_state.render()

    def run(self):
        self.current_state.init()
        while self.is_running:
            # calculate delta_time
            delta_time = 10
            self.update(delta_time)
            self.render()

    def change_state(self, next_state):
        self.current_state.finalise()
        self.current_state_code = next_state
        self.current_state = states[next_state](self.window)



def main(window):
    engine = Engine(window)
    engine.run()

curses.wrapper(main)
