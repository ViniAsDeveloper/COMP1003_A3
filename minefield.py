# Author: Vinicius Salem Henrique
# Student ID: 24897817

import random

SESSION_FILEPATH = "old_session.txt"
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
    "9",
    "c" # c to cancel the operation
]

YES_OR_NO = [
    "y",
    "n"
]

# this class could just be two separate functions. I just did it
# this way because I am used to keeping things inside classes and using
# resource locators or similar techniques to access functions.
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
    text_input = input(message + "\n_> ").strip().lower()
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
        self.tried_to_quit = False

    def init(self):
        if self.tried_to_quit:
            self.tried_to_quit = False
            return
        print(self.messages.get_message("welcome"))
        input("Press Enter to start!")
        print(self.messages.get_message("rules"))
        start_menu = Menu("Now, you can select to play a new game or resume the last one.", { "1. New game" : 1, "2. Resume game" : 2 })
        if start_menu.interact() == 1:
            self.map = Map(self)
            print("Starting fresh!\n")
        else:
            success, data = self.fileIO.read(SESSION_FILEPATH)
            if not success:
                print("Could not locate old session file. Starting fresh\n")
            self.map = Map(self, data)
            if self.map.loaded == "all":
                print("Loaded the previous session\n")
            elif self.map.loaded == "grid":
                print("Could only load the previous grid; moves were lost!\n")
            elif self.map.loaded == "nothing":
                print("Failed to load the previous session. Starting fresh!\n")

        self.action_menu = Menu("What do you want to do?",
        {
            "1. Reveal" : 1,
            "2. Flag" : 2,
            "3. Question" : 3,
            "4. Clear" : 4,
            "5. Help" : 5,
            "6. Save and quit" : 6,
            "7. Quit" : 7
        })

    def update(self):
        self.map.display()
        action = self.action_menu.interact()
        if action < 5:
            square_x = safe_input("Enter the X coordinate of the selected square", NUMBERS_LIST)
            if square_x == "c":
                return
            square_y = safe_input("Enter the Y coordinate of the selected square", NUMBERS_LIST)
            if square_y == "c":
                return
            pos = Vector2D(int(square_x), int(square_y))
            if action == 1:
                self.map.reveal(pos)
                if self.map.revealed_cells == 90:
                    self.win()
                else:
                    self.map.register("reveal", pos)
            elif action == 2:
                self.map.flag(pos)
                self.map.register("flag", pos)
            elif action == 3:
                self.map.question(pos)
                self.map.register("question", pos)
            elif action == 4:
                self.map.clear(pos)
                self.map.register("clear", pos)
            else:
                return
            return
        elif action < 8:
            if action == 5:
                print(self.messages.get_message("rules"))
            elif action == 6:
                self.is_running = False
                self.quit = True
                self.save = True
            elif action == 7:
                self.is_running = False
                self.quit = True
                self.save = False

    def loose(self):
        self.map.display()
        print(self.messages.get_message("loose"))
        self.is_running = False
        self.quit = False

    def win(self):
        self.map.display()
        print(self.messages.get_message("win"))
        self.is_running = False
        self.quit = False

    def finalise(self):
        if self.quit:
            if safe_input("Do you really want to quit? [y/n]", YES_OR_NO) == "y":
                if self.save:
                    self.fileIO.write(SESSION_FILEPATH, self.map.serialise_map(), False)
                return "quit"
            else:
                self.tried_to_quit = True
                self.is_running = True
                return "keep"
        else:
            if safe_input("Do you want to play again? [y/n]", YES_OR_NO):
                return "again"
            else:
                return "quit"

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
        self.moves = []
        self.revealed_cells = 0
        # try generating a map from data; fallback to default in case of failure
        if old_map_data:
            success, error = self.load(old_map_data)
            if not success:
                if error == "grid":
                    self.loaded = "nothing"
                    self.generate_map()
                elif error == "moves":
                    self.loaded = "grid"
            else:
                self.loaded = "all"
        else:
            self.generate_map()
            self.loaded = "new"

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
        """Returns the amound of bombs around a given location"""
        bombs_around = 0
        for offset_y in range(-1, 2):
            for offset_x in range(-1, 2):
                if self.is_bomb(Vector2D(pos.X + offset_x, pos.Y + offset_y)):
                    bombs_around += 1
        return bombs_around

    def reveal(self, pos):
        """Recursive method to reveal the map. It is adapted from a simple Flood Fill algorithm (in this case, DFS)"""
#        if pos in previous_pos:
#            return
#
#        previous_pos.append(pos)
        current_cell = self.get_cell(pos)

        if not current_cell:
            return

        if current_cell.is_bomb:
            self.controller.loose()
            return

        if not current_cell.is_hidden:
            return

        current_cell.is_hidden = False
        self.revealed_cells += 1
        if current_cell.bombs_around != 0:
            return

        for i in range(-1, 2):
            for j in range(-1, 2):
                next_cell = self.get_cell(Vector2D(pos.X + j, pos.Y + i))
                if not next_cell:
                    continue
                if next_cell.is_hidden:
                    self.reveal(next_cell.pos)

    def flag(self, pos):
        """Flags a cell and records the move"""
        cell = self.get_cell(pos)
        if not cell:
            return
        if not cell.is_hidden:
            return
        cell.flag()
        self.register("flag", pos)

    def question(self, pos):
        """Question a cell and records the move"""
        cell = self.get_cell(pos)
        if not cell:
            return
        if not cell.is_hidden:
            return
        cell.question()
        self.register("question", pos)

    def clear(self, pos):
        """Clears a cell flag or question and records the move"""
        cell = self.get_cell(pos)
        if not cell:
            return
        if not cell.is_hidden:
            return
        cell.clear()
        self.register("clear", pos)

    def register(self, move, pos):
        """Records a move if it was not already done in this game"""
        if (move, pos) not in self.moves:
            self.moves.append((move, pos))

    def generate_map(self):
        """Generates the map by populating the grid with Cells, then randomly adds bombs to some of these Cells"""
        self.grid.clear()
        for i in range(self.size.Y):
            self.grid.append([])
            for j in range(self.size.X):
                self.grid[i].append(Cell(Vector2D(j, i), False, self)) # populate with non-bombs
        i = 10
        bombs_placed = []
        while i > 0:
            bomb_x = random.randint(0, 9)
            bomb_y = random.randint(0, 9)
            pos = Vector2D(bomb_x, bomb_y)
            # skip the location if it already has a bomb in it
            if pos not in bombs_placed:
                self.grid[pos.Y][pos.X].is_bomb = True
                i -= 1
                bombs_placed.append(pos)

        for i in range(self.size.Y):
            for j in range(self.size.X):
                self.grid[i][j].bombs_around = self.bombs_around(Vector2D(j, i))

    def get_cell(self, pos):
        """Returns a cell if exists, False otherwise"""
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
                output += f"{self.grid[i][j].is_bomb}\n"
        for i in range(len(self.moves)):
            #               move type           move pos X          move pos Y
            output += f"{self.moves[i][0]},{self.moves[i][1].X},{self.moves[i][1].Y}\n"
        return output

    def load(self, serialised_data):
        """Loads a map from serialised data"""
        self.grid.clear()
        lines = serialised_data.split("\n")
        try:
            # I my loop considers X and Y meassures of the map instead of just looping though all lines,
            # because I have to make sure that the amount of lines in enough to populate the entire map
            # If there is an index out of range exception, I know that there were not enough lines and
            # this allows me to safely clear the grid and return False
            index = 0
            # parsing cells
            bombs = 0
            for i in range(self.size.Y):
                self.grid.append([])
                for j in range(self.size.X):
                    index = i * self.size.X + j
                    if lines[index].strip() == "True":
                        is_bomb = True
                        bombs += 1
                    else:
                        is_bomb = False
                    self.grid[i].append(Cell(Vector2D(j, i), is_bomb, self))
            if bombs != 10:
                return (False, "grid")

            # calculating bombs around each cell
            for i in range(self.size.Y):
                for j in range(self.size.X):
                    self.grid[i][j].bombs_around = self.bombs_around(Vector2D(j, i))
        except:
            self.grid.clear()
            return (False, "grid")

        try:
            # parsing moves
            for i in range(index + 1, len(lines)):
                move_data = lines[i].split(",")
                # ignore moves that don't follow the correct format
                if len(move_data) != 3:
                    continue
                if move_data[0] not in ["flag", "reveal", "question", "clear"]:
                    continue
                self.moves.append((move_data[0], Vector2D(int(move_data[1]), int(move_data[2]))))
        except:
            return (False, "moves")

        if self.simulate():
            return (False, "grid")
        return (True, "")

    def simulate(self):
        """Runs all moves from the moves list, simulating a player"""
        for move in self.moves:
            if move[0] == "reveal":
                if self.reveal(move[1]):
                    return True
            elif move[0] == "clear":
                self.clear(move[1])
            elif move[0] == "flag":
                self.flag(move[1])
            elif move[0] == "question":
                self.question(move[1])
            else:
                continue

    def display(self):
        print("  ", end="")
        for i in range(self.size.X):
            print(f"  {i} ", end="")

        for i in range(self.size.Y):
            print(f"\n{i} |", end="")
            for j in range(self.size.X):
                print(self.grid[i][j], sep="", end="")
            print(f" {i}", end="")

        print("\n  ", end="")
        for i in range(self.size.X):
            print(f"  {i} ", end="")

        print()

class Cell:

    NORMAL= "."
    FLAG = "F"
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
            return f" {self.state} |"

        if self.bombs_around == 0:
            return "   |"
        return f" {self.bombs_around} |"

    def flag(self):
        self.state = self.FLAG

    def question(self):
        self.state = self.QUESTION

    def clear(self):
        self.state = self.NORMAL

def main(controller=None):
    if not controller:
        controller = Controller()
    controller.init()
    while controller.is_running:
        controller.update()
    result = controller.finalise()
    if result == "quit":
        return
    elif result == "keep":
        main(controller)
    elif result == "again":
        main()

if __name__ == "__main__": main()
