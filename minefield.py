import random

SESSION_FILEPATH = "old_session.txt"
SCORE_FILEPATH = "scores.txt"
CONFIG_FILEPATH = "minefield.conf"
MESSAGES_FILEPATH = "messages.txt"
NUMBERS_LIST = [
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9"
]

class FileIO:

    def __init__(self):
        pass

    def read(self, filepath):
        try:
            with open(filepath, 'r') as file:
                content = file.read()
                return (True, content)
        except:
            return (False, None)

    def write(self, filepath, data, append=True):
        if append:
            flag = 'a'
        else:
            flag = 'w'

        try:
            with open(filepath, flag) as file:
                file.write(data)
            return True

        except:
            return False

class Config:

    def __init__(self, controller, data=None):
        if not data: # initialise to the defaults
            self.configs = {
                "map_size" : Vector2D(10, 10)
            }
            return

        try:
            options = data.split(",")
            self.configs = {
            "map_size" : Vector2D(int(options[0]), int(options[1]))
            }

        except: # if an error occurs, reset to the defaults
            self.configs = {
                "map_size" : Vector2D(10, 10)
            }

    def get_config_value(self, key):
        return self.configs.get(key)

def safe_input(message, options_list):
    text_input = input(message + "\n_> ")
    if not text_input in options_list:
        return safe_input(message, options_list)
    return text_input

class Menu:

    # to the option parameters should be passed a hashmap (or dictionary, in Python naming) containing
    # Keys:
    # strings to be displayed (these are options that can be selected)
    #
    # Values:
    # numeric values (int) associated with each option and will be returned if the option is selected
    def __init__(self, text, options):
        self.text = text
        self.options = options

    def interact(self):
        print(self.text, "\n")
        for option, index in self.options.items():
            print(f"{option}")
        option_input = input("Type the desired option index\n_> ")
        try:
            option = int(option_input)
            if option in self.options.values():
                return option
            else:
                return self.interact()
        except:
            return self.interact()

class Messages:

    def __init__(self, data):
        self.messages = {}
        try:
            # here I am using a separator which is very hard to accidentally write on the file
            messages = data.split("//$@#//")
            i = 0
            while i < len(messages) - 1:
                self.messages[messages[i].strip()] = messages[i + 1]
                i += 2
        except:
            self.messages.clear()
            self.messages = {
                "error": "No messages could be loaded"
            }

    def get_message(self, key):
        return self.messages.get(key)

class Controller:

    def __init__(self):
        """Here, I must initialise all components strictly necessary to the class, so that if something fails, it will throw and prevent object creation """
        self.fileIO = FileIO()
        success, data = self.fileIO.read(CONFIG_FILEPATH)
        self.config = Config(self)
        success, data = self.fileIO.read(MESSAGES_FILEPATH)
        self.messages = Messages(data)
        self.is_running = True

    def init(self):
        print(self.messages.get_message("welcome"))
        input("Press Enter to start!")
        print(self.messages.get_message("rules"))
        start_menu = Menu("Now, you can select to play a new game or resume a saved one.", { "1. New game" : 1, "2. Resume game" : 2 })
        if start_menu.interact() == 1:
            self.map = Map(self)
        else:
            success, data = self.fileIO.read(SESSION_FILEPATH)
            self.map = Map(data)

        self.action_menu = Menu("What do you want to do?",
        {
            "1. Reveal" : 1,
            "2. Flag" : 2,
            "3. Question" : 3,
            "4. Help" : 4,
            "5. Save and quit" : 5,
            "6. Quit" : 6
        })

    def update(self):
        self.map.display()
        action = self.action_menu.interact()
        if action < 4:
            square_x = int(safe_input("Enter the X coordinate of the selected square", NUMBERS_LIST))
            square_y = int(safe_input("Enter the Y coordinate of the selected square", NUMBERS_LIST))
            if action == 1:
                if self.map.reveal(Vector2D(square_x, square_y)):
                    self.is_running = False
                    self.state = "L"
            elif action == 2:
                self.map.flag(Vector2D(square_x, square_y))
            elif action == 3:
                self.map.question(Vector2D(square_x, square_y))
            else:
                return
            return
        elif action < 7:
            if action == 4:
                print(self.messages.get_message("rules"))
            elif action == 5:
                self.fileIO.write(SESSION_FILEPATH, self.map.serialise_map(), False)
                self.is_running = False
                self.state = "Q" # Q stands for "Quiting"
            elif action == 6:
                self.is_running = False
                self.state = "Q"

    def loose(self):
        self.is_running = False
        self.state = "L" # L stands for "Lose"

    def finalise(self):
        if self.state == "Q":
            return
        elif self.state == "W":
            print(self.messages.get_message("win"))
        elif self.state == "L":
            print(self.messages.get_message("loose"))
        else:
            return

class Vector2D:

    def __init__(self, X, Y):
        self.X = X
        self.Y = Y

    def __repr__(self):
        return f"({self.X}, {self.Y})"

    def __eq__(self, other):
        return self.X == other.X and self.Y == other.Y

class Map:

    def __init__(self, controller, old_map_data=None):
        self.controller = controller
        self.size = self.controller.config.get_config_value("map_size")
        self.grid = []
        if old_map_data:
            if self.load(old_map_data):
                self.new_game = False
            else:
                self.generate_map()
                self.new_map = True
        else:
            self.generate_map()
            self.new_game = True

    def is_bomb(self, pos):
        """Safe method to check if a cell has a bomb - indexes out of the map range simply return False"""
        if not (0 <= pos.X < self.size.X):
            return False

        if not (0 <= pos.Y < self.size.Y):
            return False

        try:
            result = self.grid[pos.Y][pos.X].is_bomb
        except:
            result = False

        return result

    def bombs_around(self, pos):
        bombs_around = 0
        for offset_y in range(-1, 2):
            for offset_x in range(-1, 2):
                if self.is_bomb(Vector2D(pos.X + offset_x, pos.Y + offset_y)):
                    bombs_around += 1
        return bombs_around

    def reveal(self, pos, previous_pos=[]):

        if pos in previous_pos:
            return
        previous_pos.append(pos)
        current_cell = self.get_cell(pos)
        if not current_cell:
            return

        if current_cell.is_bomb:
            return True

        if not current_cell.is_hidden:
            return

        current_cell.is_hidden = False
        if current_cell.bombs_around != 0:
            return

        for i in range(-1, 2):
            for j in range(-1, 2):
                next_cell = self.get_cell(Vector2D(pos.X + j, pos.Y + i))
                if (not next_cell) or (next_cell.pos in previous_pos):
                    continue
                if next_cell.is_hidden:
                    print(next_cell.pos)
                    self.reveal(next_cell.pos, previous_pos)

    def generate_map(self):
        """Generates the map by populating the grid with Cells, randomly add bombs to some of these Cells"""
        self.grid.clear()
        for i in range(self.size.Y):
            self.grid.append([])
            for j in range(self.size.X):
                self.grid[i].append(Cell(Vector2D(j, i), False, self))
        i = 10
        bombs_placed = []
        while i > 0:
            bomb_x = random.randint(0, 9)
            bomb_y = random.randint(0, 9)
            coordinates = (bomb_x, bomb_y)
            # skip the location if it already has a bomb in it
            if coordinates not in bombs_placed:
                self.grid[bomb_y][bomb_x].is_bomb = True
                i -= 1
        for i in range(self.size.Y):
            for j in range(self.size.X):
                self.grid[i][j].bombs_around = self.bombs_around(Vector2D(j, i))

    def get_cell(self, pos):

        if pos.X < 0 or pos.Y < 0:
            return None
        try:
            result = self.grid[pos.Y][pos.X]
            return result
        except:
            return None

    def serialise_map(self):
        """Serialises map data so that is can be written to a file as a string"""
        output = ""
        for i in range(self.size.Y):
            for j in range(self.size.X):
                output += f"{self.grid[j, i].is_bomb}\n"

    def load(self, serialized_data):

        self.grid.clear()
        lines = serialized_data.slipt("\n")
        try:
            # I my loop considers X and Y meassures of the map instead of just looping though all lines,
            # because I have to make sure that the amount of lines in enough to populate the entire map
            # If there is an index out of range exception, I know that there were not enough lines and
            # this allows me to safely clear the grid and return False
            for i in range(self.size.Y):
                self.grid.append([])
                for j in range(self.size.X):
                    if lines[i * self.size.X + j] == "True":
                        is_bomb = True
                    else:
                        is_bomb = False
                    self.grid[i].append(Cell(Vector2D(j, i), is_bomb, self))
        except:
            self.grid.clear()
            return False
        return True

    def display(self):
        for i in range(self.size.Y):
            print()
            for j in range(self.size.X):
                print(self.grid[i][j], end="")
        print()

class Cell:

    NORMAL= "+"
    FLAG= "F"
    QUESTION = "?"

#                       Vector2D  bool    map
    def __init__(self, position, is_bomb, map):
        self.pos = position
        self.is_bomb = is_bomb
        self.bombs_around = map.bombs_around(position)
        self.map = map
        self.is_hidden = True
        self.state = self.NORMAL

    def __repr__(self):
        if self.is_hidden:
            return f"[ {self.state} ]"

        if self.bombs_around == 0:
            return "[   ]"
        return f"[ {self.bombs_around} ]"

def main():
    controller = Controller()
    controller.init()
    while controller.is_running:
        controller.update()
    controller.finalise()

if __name__ == "__main__": main()
