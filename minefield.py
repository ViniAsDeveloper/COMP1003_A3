import random

SAVE_FILE_FILEPATH = "old_session.txt"
SAVE_SCORE_FILEPATH = "scores.txt"
SAVE_CONFIG_FILEPATH = "minefield.conf"

class FileIO:

    def __init__(self):
        pass

    def read(self, filepath):
        try:
            with open(filepath, 'r') as file:
                content = file.read()
                return (True, content)
        except:
            return (False, "")

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

    def __init__(self, controller):
        self.controller = controller
        success, data = self.controller.fileIO.read(SAVE_CONFIG_FILEPATH)
        if not success:
            self.map_size = Vector2D(9, 9)
        else:
            options = data.split(",")
            try:
                self.map_size = Vector2D(int(options[0]), int(options[1]))
            except:
                self.map_size = Vector2D(9, 9)

    def save_config(self):
        pass

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
        for index, option in options:
            print(f"{str(index)}. {option}")
        option_input = input("Type the desired option index\n_> ")
        try:
            option = int(option_input)
            if option in self.options.keys():
                return option
            else:
                return self.interact()
        except:
            return self.interact()

class Controller:

    def __init__(self):
        self.fileIO = FileIO()
        self.is_running = True
        self.welcome_user()
        self.display_rules()
#        self.start_menu = Menu(

    def update(self):
        pass

    def welcome_user(self):
        print("\n\n\n\n\nWelcome to the Minefield game!\nThis game was created by:\n----------------------------")
        print("| Vinicius Salem Henrique\n| Southern Cross University\n| Student ID = 24897817\n----------------------------")

    def display_rules(self):
        print("The game consists of a minefield, represented by a grid with several squares arranged in rows and columns.")
        print("Each square may or may not contain a mine, and your aim is to reveal all safe squares (those that don't contain a mine).")
        print("However, if you click on a square that contains a mine, it will explode and you’ll lose the game!\n")
        print("To select a square, simply type the X and Y coordinates of the square. Then, you can choose an action to perform over this square.")
        print("Your available actions are:\n1. Inspect -> this will reveal if there is a bomb on this square or not; You must do this for every safe square in the game")
        print("2. Flag -> This action marks the square as a bomb. It makes easier to keep track of all places you are sure to have a bomb")
        print("3. Question -> This action marks the square with a question mark (?), meaning 'it is possibly a bomb' to warn you to take care")
        print("That is it, super simple! Have fun!")

class Vector2D:

    def __init__(self, X, Y):
        self.X = X
        self.Y = Y

    def __repr__(self):
        return f"({self.X}, {self.Y})"

class Map:

    def __init__(self, controller, load_old_session=False):
        self.controller = controller
        self.size = self.contoller.config.get_map_size()
        self.grid = []
        if load_old_session:
            success, map_data = self.controller.fileIO.read(SAVE_FILE_FILEPATH)
            if not success:
                self.generate_map()
                self.new_game = True
            else:
                if self.load(map_data):
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

        return self.grid[pos.Y, pos.X].is_bomb

    def generate_map(self):
        """Generates the map by populating the grid with Cells, randomly add bombs to some of these Cells"""
        self.grid.clear()
        for i in range(self.size.Y):
            self.grid.append([])
            for j in range(self.size.X):
                if random.random() < 0.17:
                    is_bomb = True
                else:
                    is_bomb = False
                self.grid[i].append(Cell(Vector2D(j, i), is_bomb, self))

    def serialize_map(self):
        """Serializes map data so that is can be written to a file as a string"""
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

    def __repr__(self):
        for i in range(self.size.Y):
            for j in range(self.size.X):
                print(self.grid[i][j])

class Cell:
#                       Vector2D  bool    map
    def __init__(self, position, is_bomb, map):
        self.pos = position
        self.is_bomb = is_bomb
        self.bombs_around = 0
        self.map = map
        self.is_hidden = True

    def look_around(self):
        """Checks how many cells containing a bomb are around this cell to display this information to the player"""
        if self.map.is_bomb(self.pos.Y, self.pos.X - 1):
            self.bombs_around += 1
        if self.map.is_bomb(self.pos.Y, self.pos.X + 1):
            self.bombs_around += 1
        if self.map.is_bomb(self.pos.Y - 1, self.pos.X):
            self.bombs_around += 1
        if self.map.is_bomb(self.pos.Y + 1, self.pos.X):
            self.bombs_around += 1

    def show(self):
        self.is_hidden = False

    def __repr__(self):
        if self.is_hidden:
            return f"[   ]"

        if self.is_bomb:
            return f"[ B ]"

        return f"[ {self.bombs_around} ]"

def main():
    controller = Controller()
    while controller.is_running:
        controller.update()
    controller.finalise()

if __name__ == "__main__": main()
