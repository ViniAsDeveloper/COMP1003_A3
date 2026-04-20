#!/usr/bin/env python3
"""
Minefield - simple text-based Minesweeper-like game
Implements the structure described in the provided pseudocode.
"""

import random
from dataclasses import dataclass

# -------------------- Utilities -------------------- #

def safe_input(message, options):
    """Prompt until user enters a valid option (case-insensitive)."""
    choice = input(message).strip().lower()
    if choice not in options:
        return safe_input(message, options)
    return choice

# -------------------- FileIO -------------------- #

class FileIO:
    def read(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return True, f.read()
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
    def __init__(self, controller=None, data=None):
        defaults = {"width": 9, "height": 9, "bombs": 10, "save_file": "minefield_save.txt"}
        if not data:
            self.configs = defaults
        else:
            try:
                # placeholder for parsing data if needed
                self.configs = defaults
            except Exception:
                self.configs = defaults

    def get_config_value(self, key):
        return self.configs.get(key)

# -------------------- Menu -------------------- #

class Menu:
    def __init__(self, text, options):
        """
        options: dict mapping key -> description (and return value is key)
        Example: {"1": "new game", "2": "load game"}
        """
        self.text = text
        self.options = options

    def interact(self):
        print(self.text)
        for k, v in self.options.items():
            print(f"  {k}) {v}")
        choice = input("Choose: ").strip()
        if choice in self.options:
            return choice
        print("Invalid option, try again.")
        return self.interact()

# -------------------- Messages -------------------- #

class Messages:
    def __init__(self, data=None):
        try:
            self.messages = {
                "welcome": "Welcome to Minefield!",
                "rules": (
                    "Rules:\n"
                    "- Reveal cells to find safe spots.\n"
                    "- Revealing a bomb ends the game.\n"
                    "- Use flags and question marks as notes.\n"
                ),
                "lose": "Boom! You hit a bomb. Game over.",
                "win": "You cleared the minefield. Well done!",
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
    def __init__(self, pos, is_bomb=False):
        self.pos = pos
        self.is_bomb = is_bomb
        self.bombs_around = 0
        self.is_hidden = True
        self.state = "normal"  # normal, flag, question

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
        cfg = controller.config
        self.size = Vector2D(cfg.get_config_value("width"), cfg.get_config_value("height"))
        self.bomb_count = cfg.get_config_value("bombs")
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
        w, h = self.size.x, self.size.y
        self.grid = [[Cell(Vector2D(x, y), False) for x in range(w)] for y in range(h)]
        bombs = set()
        while len(bombs) < self.bomb_count:
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            bombs.add((x, y))
        for (x, y) in bombs:
            self.grid[y][x].is_bomb = True
        for y in range(h):
            for x in range(w):
                if not self.grid[y][x].is_bomb:
                    self.grid[y][x].bombs_around = self.count_bombs_around(x, y)

    def count_bombs_around(self, x, y):
        cnt = 0
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue
                if 0 <= nx < self.size.x and 0 <= ny < self.size.y:
                    if self.grid[ny][nx].is_bomb:
                        cnt += 1
        return cnt

    def get_cell(self, pos):
        if 0 <= pos.x < self.size.x and 0 <= pos.y < self.size.y:
            return self.grid[pos.y][pos.x]
        return None

    def reveal(self, pos):
        cell = self.get_cell(pos)
        if cell is None:
            return
        if cell.is_bomb:
            # reveal all and lose
            for row in self.grid:
                for c in row:
                    c.is_hidden = False
            self.controller.loose()
            return
        if not cell.is_hidden:
            return
        cell.is_hidden = False
        self.revealed_cells += 1
        if cell.bombs_around == 0:
            for ny in range(pos.y - 1, pos.y + 2):
                for nx in range(pos.x - 1, pos.x + 2):
                    if nx == pos.x and ny == pos.y:
                        continue
                    if 0 <= nx < self.size.x and 0 <= ny < self.size.y:
                        self.reveal(Vector2D(nx, ny))
        # win check
        total = self.size.x * self.size.y
        if self.revealed_cells == total - self.bomb_count:
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
        lines = []
        lines.append(f"{self.size.x} {self.size.y} {self.bomb_count}")
        for y in range(self.size.y):
            for x in range(self.size.x):
                c = self.grid[y][x]
                lines.append(f"{y} {x} {int(c.is_bomb)} {c.bombs_around} {int(c.is_hidden)} {c.state}")
        lines.append("MOVES")
        for m, x, y in self.moves:
            lines.append(f"{m} {x} {y}")
        return "\n".join(lines)

    def load(self, data):
        lines = data.strip().splitlines()
        header = lines[0].split()
        w, h, bombs = map(int, header)
        self.size = Vector2D(w, h)
        self.bomb_count = bombs
        self.grid = [[None for _ in range(w)] for _ in range(h)]
        idx = 1
        while idx < len(lines) and lines[idx] != "MOVES":
            parts = lines[idx].split()
            y, x = int(parts[0]), int(parts[1])
            is_bomb = bool(int(parts[2]))
            bombs_around = int(parts[3])
            is_hidden = bool(int(parts[4]))
            state = parts[5]
            cell = Cell(Vector2D(x, y), is_bomb)
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
        # header
        print("\n   " + " ".join(f"{x:2d}" for x in range(self.size.x)))
        for y in range(self.size.y):
            row = f"{y:2d} "
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
                row += f" {ch}"
            print(row)
        print()

    def simulate(self):
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
        self.config = Config(self)
        self.messages = Messages()
        self.map = None
        self.is_running = True
        self.quit = False
        self.save = False
        self.action_menu = None

    def init(self):
        print(self.messages.get_message("welcome"))
        print(self.messages.get_message("rules"))
        start = Menu("Start Menu:", {"1": "new game", "2": "load game"})
        choice = start.interact()
        if choice == "1":
            self.map = Map(self)
        else:
            ok, data = self.fileIO.read(self.config.get_config_value("save_file"))
            if ok and data:
                try:
                    self.map = Map(self, old_map_data=data)
                except Exception:
                    print("Failed to load save, starting new game.")
                    self.map = Map(self)
            else:
                print("No save found, starting new game.")
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
        action_key = self.action_menu.interact()
        action_map = {
            "1": "reveal",
            "2": "flag",
            "3": "question",
            "4": "clear",
            "5": "help",
            "6": "save and quit",
            "7": "quit"
        }
        action = action_map.get(action_key)
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
            x = int(input("Enter X coordinate: ").strip())
            y = int(input("Enter Y coordinate: ").strip())
            if 0 <= x < self.map.size.x and 0 <= y < self.map.size.y:
                return Vector2D(x, y)
            print("Coordinates out of range.")
            return None
        except ValueError:
            print("Invalid coordinates.")
            return None

    def loose(self):
        self.map.display()
        print(self.messages.get_message("lose"))
        self.is_running = False

    def win(self):
        self.map.display()
        print(self.messages.get_message("win"))
        self.is_running = False

    def finalise(self):
        if self.quit:
            confirm = safe_input("Are you sure you want to quit? (y/n): ", {"y", "n"})
            if confirm == "y":
                if self.save:
                    data = self.map.serialise_map()
                    ok = self.fileIO.write(self.config.get_config_value("save_file"), data, append=False)
                    if ok:
                        print("Game saved.")
                    else:
                        print("Failed to save game.")
                return "quit"
            else:
                return "keep"
        else:
            again = safe_input("Play again? (y/n): ", {"y", "n"})
            return "again" if again == "y" else "quit"

# -------------------- Main program -------------------- #

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
