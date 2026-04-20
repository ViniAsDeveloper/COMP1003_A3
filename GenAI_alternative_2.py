"""
Simple text-based Minefield (Minesweeper-like) game based on the provided pseudocode.

This is intentionally straightforward and not fully feature-complete compared to
a production game, but it follows the structure and flow of the pseudocode.
"""

import random
from dataclasses import dataclass


# -------------------- Utility -------------------- #

def safe_input(message, options_list):
    """Ask until user enters a valid option from options_list."""
    user_input = input(message).strip().lower()
    if user_input not in options_list:
        return safe_input(message, options_list)
    return user_input


# -------------------- FileIO -------------------- #

class FileIO:
    def read(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception:
            return False, None

    def write(self, filepath, data, append=False):
        mode = "a" if append else "w"
        try:
            with open(filepath, mode, encoding="utf-8") as f:
                f.write(data)
            return True
        except Exception:
            return False


# -------------------- Config -------------------- #

class Config:
    def __init__(self, controller, data=None):
        # Very simple config: board size and bomb count
        defaults = {
            "width": 9,
            "height": 9,
            "bombs": 10,
            "save_file": "minefield_save.txt"
        }

        if not data:
            self.configs = defaults
        else:
            # For simplicity, ignore parsing and fall back to defaults
            try:
                # You could parse JSON or key=value here if desired
                self.configs = defaults
            except Exception:
                self.configs = defaults

    def get_config_value(self, key):
        return self.configs.get(key)


# -------------------- Menu -------------------- #

class Menu:
    def __init__(self, text, options):
        """
        options: dict mapping option_key -> return_value
        e.g. {"1": "new", "2": "load"}
        """
        self.text = text
        self.options = options

    def interact(self):
        print(self.text)
        for key, value in self.options.items():
            print(f"  {key}) {value}")
        choice = input("Choose: ").strip()
        if choice in self.options:
            return self.options[choice]
        else:
            print("Invalid option, try again.")
            return self.interact()


# -------------------- Messages -------------------- #

class Messages:
    def __init__(self, messages_data=None):
        try:
            # Simple hard-coded messages; messages_data ignored for now
            self.messages = {
                "welcome": "Welcome to Minefield!",
                "rules": (
                    "Rules:\n"
                    "- Reveal cells to find safe spots.\n"
                    "- If you reveal a bomb, you lose.\n"
                    "- Flags (?) and ? marks are just for your notes.\n"
                ),
                "lose": "Boom! You hit a bomb. Game over.",
                "win": "Congratulations! You cleared the minefield!",
                "error": "An error occurred."
            }
        except Exception:
            self.messages = {"error": "An error occurred."}

    def get_message(self, key):
        return self.messages.get(key, self.messages["error"])


# -------------------- Vector2D -------------------- #

@dataclass
class Vector2D:
    x: int
    y: int


# -------------------- Cell -------------------- #

class Cell:
    def __init__(self, position, is_bomb, game_map):
        self.pos = position
        self.is_bomb = is_bomb
        self.bombs_around = 0
        self.is_hidden = True
        self.state = "normal"  # normal, flag, question
        self.map = game_map

    def flag(self):
        self.state = "flag"

    def question(self):
        self.state = "question"

    def clear(self):
        self.state = "normal"


# -------------------- Map -------------------- #

class Map:
    def __init__(self, controller, old_map_data=None):
        self.controller = controller
        self.size = Vector2D(
            controller.config.get_config_value("width"),
            controller.config.get_config_value("height"),
        )
        self.bomb_count = controller.config.get_config_value("bombs")
        self.grid = []
        self.moves = []
        self.revealed_cells = 0
        self.loaded = False

        if old_map_data:
            try:
                self.load(old_map_data)
                self.loaded = True
            except Exception:
                self.generate_map()
        else:
            self.generate_map()

    def generate_map(self):
        width, height = self.size.x, self.size.y
        self.grid = [[None for _ in range(width)] for _ in range(height)]

        # Place bombs
        bomb_positions = set()
        while len(bomb_positions) < self.bomb_count:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            bomb_positions.add((x, y))

        for y in range(height):
            for x in range(width):
                is_bomb = (x, y) in bomb_positions
                self.grid[y][x] = Cell(Vector2D(x, y), is_bomb, self)

        # Calculate bombs_around
        for y in range(height):
            for x in range(width):
                cell = self.grid[y][x]
                if cell.is_bomb:
                    cell.bombs_around = -1
                else:
                    cell.bombs_around = self.count_bombs_around(x, y)

    def count_bombs_around(self, x, y):
        count = 0
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue
                if 0 <= nx < self.size.x and 0 <= ny < self.size.y:
                    if self.grid[ny][nx].is_bomb:
                        count += 1
        return count

    def get_cell(self, pos):
        if 0 <= pos.y < self.size.y and 0 <= pos.x < self.size.x:
            return self.grid[pos.y][pos.x]
        return None

    def reveal(self, pos):
        cell = self.get_cell(pos)
        if cell is None:
            return

        if cell.is_bomb:
            self.controller.loose()
            return

        if not cell.is_hidden:
            return

        cell.is_hidden = False
        self.revealed_cells += 1

        # If no bombs around, reveal neighbours
        if cell.bombs_around == 0:
            for ny in range(pos.y - 1, pos.y + 2):
                for nx in range(pos.x - 1, pos.x + 2):
                    if nx == pos.x and ny == pos.y:
                        continue
                    if 0 <= nx < self.size.x and 0 <= ny < self.size.y:
                        self.reveal(Vector2D(nx, ny))

        # Check win condition
        total_cells = self.size.x * self.size.y
        if self.revealed_cells == total_cells - self.bomb_count:
            self.controller.win()

    def flag(self, pos):
        cell = self.get_cell(pos)
        if cell:
            cell.flag()
            self.register("flag", pos)

    def question(self, pos):
        cell = self.get_cell(pos)
        if cell:
            cell.question()
            self.register("question", pos)

    def clear(self, pos):
        cell = self.get_cell(pos)
        if cell:
            cell.clear()
            self.register("clear", pos)

    def register(self, move, pos):
        self.moves.append((move, pos.x, pos.y))

    def serialise_map(self):
        """
        Very simple serialisation:
        First line: width height bombs
        Next lines: y x is_bomb bombs_around is_hidden state
        Then a line: MOVES
        Then each move: move x y
        """
        lines = []
        lines.append(f"{self.size.x} {self.size.y} {self.bomb_count}")
        for y in range(self.size.y):
            for x in range(self.size.x):
                c = self.grid[y][x]
                lines.append(
                    f"{y} {x} {int(c.is_bomb)} {c.bombs_around} "
                    f"{int(c.is_hidden)} {c.state}"
                )
        lines.append("MOVES")
        for move, x, y in self.moves:
            lines.append(f"{move} {x} {y}")
        return "\n".join(lines)

    def load(self, serialised_data):
        lines = serialised_data.strip().splitlines()
        header = lines[0].split()
        width, height, bombs = map(int, header)
        self.size = Vector2D(width, height)
        self.bomb_count = bombs
        self.grid = [[None for _ in range(width)] for _ in range(height)]

        idx = 1
        while idx < len(lines) and lines[idx] != "MOVES":
            parts = lines[idx].split()
            y, x = int(parts[0]), int(parts[1])
            is_bomb = bool(int(parts[2]))
            bombs_around = int(parts[3])
            is_hidden = bool(int(parts[4]))
            state = parts[5]
            cell = Cell(Vector2D(x, y), is_bomb, self)
            cell.bombs_around = bombs_around
            cell.is_hidden = is_hidden
            cell.state = state
            self.grid[y][x] = cell
            if not is_hidden and not is_bomb:
                self.revealed_cells += 1
            idx += 1

        self.moves = []
        if idx < len(lines) and lines[idx] == "MOVES":
            idx += 1
            while idx < len(lines):
                parts = lines[idx].split()
                move, x, y = parts[0], int(parts[1]), int(parts[2])
                self.moves.append((move, x, y))
                idx += 1

        self.simulate()

    def display(self):
        # Column header
        print("\n   " + " ".join(f"{x:2d}" for x in range(self.size.x)))
        for y in range(self.size.y):
            row_str = f"{y:2d} "
            for x in range(self.size.x):
                c = self.grid[y][x]
                if c.is_hidden:
                    if c.state == "flag":
                        ch = "F"
                    elif c.state == "question":
                        ch = "?"
                    else:
                        ch = "#"
                else:
                    if c.is_bomb:
                        ch = "*"
                    else:
                        ch = str(c.bombs_around) if c.bombs_around > 0 else "."
                row_str += f" {ch}"
            print(row_str)
        print()

    def simulate(self):
        # Re-apply moves to ensure consistency (mainly for flags/questions)
        for move, x, y in self.moves:
            pos = Vector2D(x, y)
            if move == "flag":
                self.flag(pos)
            elif move == "question":
                self.question(pos)
            elif move == "clear":
                self.clear(pos)


# -------------------- Controller -------------------- #

class Controller:
    def __init__(self):
        self.fileIO = FileIO()
        self.config = Config(self, None)
        self.messages = Messages()
        self.map = None
        self.is_running = True
        self.quit = False
        self.save = False
        self.tried_to_quit = False
        self.action_menu = None

    def init(self):
        print(self.messages.get_message("welcome"))
        print(self.messages.get_message("rules"))

        start_menu = Menu(
            "Start Menu:",
            {
                "1": "new game",
                "2": "load game"
            }
        )
        choice = start_menu.interact()
        if choice == "new game":
            self.map = Map(self)
        else:
            ok, data = self.fileIO.read(self.config.get_config_value("save_file"))
            if ok and data:
                self.map = Map(self, old_map_data=data)
            else:
                print("No valid save found, starting new game.")
                self.map = Map(self)

        self.action_menu = Menu(
            "Actions:",
            {
                "1": "reveal",
                "2": "flag",
                "3": "question",
                "4": "clear",
                "5": "help",
                "6": "save and quit",
                "7": "quit"
            }
        )

    def update(self):
        if not self.is_running:
            return

        self.map.display()
        action = self.action_menu.interact()

        if action in ("reveal", "flag", "question", "clear"):
            pos = self.get_coordinates()
            if pos is None:
                return
            if action == "reveal":
                self.map.reveal(pos)
            elif action == "flag":
                self.map.flag(pos)
            elif action == "question":
                self.map.question(pos)
            elif action == "clear":
                self.map.clear(pos)
        elif action == "help":
            print(self.messages.get_message("rules"))
        elif action == "save and quit":
            self.quit = True
            self.save = True
            self.is_running = False
        elif action == "quit":
            self.quit = True
            self.save = False
            self.is_running = False

    def get_coordinates(self):
        try:
            x = int(input("Enter X coordinate: "))
            y = int(input("Enter Y coordinate: "))
            if 0 <= x < self.map.size.x and 0 <= y < self.map.size.y:
                return Vector2D(x, y)
            else:
                print("Coordinates out of range.")
                return None
        except ValueError:
            print("Invalid coordinates.")
            return None

    def loose(self):
        # Show full map
        for row in self.map.grid:
            for c in row:
                c.is_hidden = False
        self.map.display()
        print(self.messages.get_message("lose"))
        self.is_running = False

    def win(self):
        for row in self.map.grid:
            for c in row:
                c.is_hidden = False
        self.map.display()
        print(self.messages.get_message("win"))
        self.is_running = False

    def finalise(self):
        if self.quit:
            confirm = safe_input("Are you sure you want to quit? (y/n): ", ["y", "n"])
            if confirm == "y":
                if self.save:
                    data = self.map.serialise_map()
                    self.fileIO.write(self.config.get_config_value("save_file"), data, append=False)
                    print("Game saved.")
                return "quit"
            else:
                return "keep"
        else:
            again = safe_input("Play again? (y/n): ", ["y", "n"])
            if again == "y":
                return "again"
            else:
                return "quit"


# -------------------- Program entry -------------------- #

def main(existing_controller=None):
    if existing_controller is not None:
        controller = existing_controller
    else:
        controller = Controller()
    controller.init()

    while controller.is_running:
        controller.update()

    result = controller.finalise()
    if result == "keep":
        main(controller)
    elif result == "again":
        main()


if __name__ == "__main__":
    main()
