import random
import json
import os
from typing import List, Dict, Tuple, Any, Optional

# --- Utility Classes & Functions (from Pseudocode) ---

class FileIO:
    def __init__(self):
        pass

    def read(self, filepath: str) -> Tuple[bool, Optional[str]]:
        try:
            with open(filepath, 'r') as file:
                content = file.read()
            return (True, content)
        except Exception:
            return (False, None)

    def write(self, filepath: str, data: str, append: bool = False) -> bool:
        mode = 'a' if append else 'w'
        try:
            with open(filepath, mode) as file:
                file.write(data)
            return True
        except Exception:
            return False

class Config:
    def __init__(self, controller, data: str = ""):
        self.configs = {}
        defaults = {"grid_size": 10, "num_bombs": 10}
        if not data:
            self.configs = defaults
        else:
            try:
                # Simple JSON parse for config data
                self.configs = json.loads(data)
                # Ensure defaults exist if keys are missing
                for k, v in defaults.items():
                    if k not in self.configs:
                        self.configs[k] = v
            except Exception:
                self.configs = defaults

    def get_config_value(self, key: str) -> Any:
        return self.configs.get(key)

class Messages:
    def __init__(self, messages_data: Dict[str, str] = None):
        self.messages = {}
        default_messages = {
            "welcome": "Welcome to Minefield!",
            "rules": "Rules: Reveal squares. Avoid bombs. Flag suspect squares.",
            "menu_new": "New Game",
            "menu_load": "Load Game",
            "menu_reveal": "Reveal",
            "menu_flag": "Flag",
            "menu_question": "Question",
            "menu_clear": "Clear",
            "menu_quit": "Quit",
            "menu_help": "Help",
            "menu_save_quit": "Save & Quit",
            "lose": "Game Over! You hit a bomb.",
            "win": "Congratulations! You cleared the field.",
            "confirm_quit": "Are you sure you want to quit?",
            "play_again": "Play again?"
        }
        
        if messages_data:
            try:
                self.messages = messages_data
            except Exception:
                self.messages = default_messages
        else:
            self.messages = default_messages

    def get_message(self, key: str) -> str:
        return self.messages.get(key, "Unknown message")

class Vector2D:
    def __init__(self, x: int, y: int):
        self.X = x
        self.Y = y

class Menu:
    def __init__(self, text: str, options: List[str]):
        self.text = text
        self.options = options

    def interact(self) -> str:
        print(f"\n{self.text}")
        for i, opt in enumerate(self.options, 1):
            print(f"{i}. {opt}")
        
        while True:
            try:
                user_input = input("Select option number: ").strip()
                if user_input.isdigit():
                    idx = int(user_input) - 1
                    if 0 <= idx < len(self.options):
                        return self.options[idx]
            except ValueError:
                pass
            print("Invalid input. Please try again.")
        return ""

# --- Core Game Logic Classes ---

class Cell:
    def __init__(self, pos: Vector2D, is_bomb: bool, map_ref):
        self.pos = pos
        self.is_bomb = is_bomb
        self.bombs_around = 0
        self.is_hidden = True
        self.state = "NORMAL"  # NORMAL, FLAG, QUESTION, REVEALED

    def flag(self):
        self.state = "FLAG"
        # In a real UI, this would change visual appearance

    def question(self):
        self.state = "QUESTION"

    def clear(self):
        self.state = "NORMAL"

class Map:
    def __init__(self, controller, old_map_data: str = None):
        self.controller = controller
        self.size = int(controller.config.get_config_value("grid_size"))
        self.grid = [[Cell(Vector2D(i, j), False, self) for j in range(self.size)] for i in range(self.size)]
        self.moves = []
        self.revealed_cells = 0
        self.loaded = False
        self.bombs_placed = 0

        if old_map_data:
            self.load(old_map_data)
        else:
            self.generate_map()

    def generate_map(self):
        # Clear existing grid logic
        self.grid = [[Cell(Vector2D(i, j), False, self) for j in range(self.size)] for i in range(self.size)]
        self.bombs_placed = 0
        
        # Place random bombs
        total_cells = self.size * self.size
        num_bombs = int(self.controller.config.get_config_value("num_bombs"))
        
        if num_bombs >= total_cells:
            num_bombs = total_cells - 1

        while self.bombs_placed < num_bombs:
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)
            if not self.grid[x][y].is_bomb:
                self.grid[x][y].is_bomb = True
                self.bombs_placed += 1

        # Calculate bombs around
        for x in range(self.size):
            for y in range(self.size):
                if self.grid[x][y].is_bomb:
                    self.grid[x][y].bombs_around = 0 # Bombs usually show 0 or hidden
                else:
                    count = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.size and 0 <= ny < self.size:
                                if self.grid[nx][ny].is_bomb:
                                    count += 1
                    self.grid[x][y].bombs_around = count

    def get_cell(self, pos: Vector2D) -> Cell:
        if 0 <= pos.X < self.size and 0 <= pos.Y < self.size:
            return self.grid[pos.X][pos.Y]
        return None

    def reveal(self, pos: Vector2D) -> bool:
        cell = self.get_cell(pos)
        if not cell:
            return False
        
        if cell.is_bomb:
            self.controller.loose()
            return True
        
        if not cell.is_hidden:
            return False
        
        cell.is_hidden = False
        cell.state = "REVEALED"
        
        if cell.bombs_around == 0:
            self._reveal_neighbors(pos)
        
        self.revealed_cells += 1
        return True

    def _reveal_neighbors(self, pos: Vector2D):
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = pos.X + dx, pos.Y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    neighbor = self.grid[nx][ny]
                    if not neighbor.is_bomb and neighbor.is_hidden:
                        neighbor.is_hidden = False
                        neighbor.state = "REVEALED"
                        if neighbor.bombs_around == 0:
                            self._reveal_neighbors(Vector2D(nx, ny))
                        self.revealed_cells += 1

    def flag(self, pos: Vector2D):
        cell = self.get_cell(pos)
        if cell and cell.state == "NORMAL":
            cell.state = "FLAG"
            self.moves.append(("FLAG", pos))

    def question(self, pos: Vector2D):
        cell = self.get_cell(pos)
        if cell and cell.state == "NORMAL":
            cell.state = "QUESTION"
            self.moves.append(("QUESTION", pos))

    def clear(self, pos: Vector2D):
        cell = self.get_cell(pos)
        if cell and cell.state in ["FLAG", "QUESTION"]:
            cell.state = "NORMAL"
            self.moves.append(("CLEAR", pos))

    def register(self, move_type, pos):
        self.moves.append((move_type, pos))

    def serialise_map(self) -> str:
        # Simplified serialization for the purpose of this exercise
        # Stores grid state and move history
        data = {
            "grid": [],
            "moves": self.moves
        }
        for row in self.grid:
            data["grid"].append([
                {"bomb": c.is_bomb, "hidden": c.is_hidden, "state": c.state} 
                for c in row
            ])
        return json.dumps(data)

    def load(self, serialised_data: str):
        try:
            data = json.loads(serialised_data)
            # Reconstruct grid
            for r_idx, row_data in enumerate(data["grid"]):
                for c_idx, cell_data in enumerate(row_data):
                    x, y = c_idx, r_idx
                    is_bomb = cell_data["bomb"]
                    is_hidden = cell_data["hidden"]
                    state = cell_data["state"]
                    
                    # Update existing cell or create new if logic differs
                    # For simplicity, we assume structure matches or overwrite
                    if is_bomb:
                        self.grid[x][y].is_bomb = True
                    else:
                        self.grid[x][y].is_bomb = False
                    
                    self.grid[x][y].is_hidden = is_hidden
                    self.grid[x][y].state = state
            self.moves = data["moves"]
            self.loaded = True
        except Exception:
            print("Error loading map.")
            return False

    def display(self):
        print("\n" + "="*30)
        # Print Header
        print("   ", end="")
        for i in range(self.size):
            print(f"{i} ", end="")
        print()
        print("   " + "-" * (len(str(self.size)) + 1) * (self.size - 1) + "-")
        
        for x in range(self.size):
            print(f"{x} ", end="")
            for y in range(self.size):
                cell = self.grid[x][y]
                if cell.is_hidden:
                    if cell.state == "FLAG":
                        print("F ", end="")
                    elif cell.state == "QUESTION":
                        print("Q ", end="")
                    else:
                        print(". ", end="")
                else:
                    if cell.is_bomb:
                        print("X ", end="")
                    else:
                        print(f"{cell.bombs_around} ", end="")
            print()
        
        # Check Win Condition
        if self.revealed_cells == (self.size * self.size) - self.bombs_placed:
            self.controller.win()

    def simulate(self):
        # Used for loading games to replay moves
        for move_type, pos in self.moves:
            if move_type == "FLAG":
                self.flag(pos)
            elif move_type == "QUESTION":
                self.question(pos)
            elif move_type == "CLEAR":
                self.clear(pos)
            # Reveal logic is complex to simulate perfectly without state history,
            # but for this simplified version, we assume the current state reflects the simulation
            # or we skip simulation of reveals if the map is already loaded.

class Controller:
    def __init__(self):
        self.fileIO = FileIO()
        self.config = Config(self)
        self.messages = Messages()
        self.map = None
        self.is_running = True
        self.quit = False
        self.save = False
        self.tried_to_quit = False

    def init(self):
        print(self.messages.get_message("welcome"))
        print(self.messages.get_message("rules"))
        
        start_menu = Menu("Start Menu", [self.messages.get_message("menu_new"), self.messages.get_message("menu_load")])
        choice = start_menu.interact()
        
        if choice == self.messages.get_message("menu_new"):
            self.map = Map(self)
        else:
            # Load functionality
            filepath = "savegame.json"
            success, content = self.fileIO.read(filepath)
            if success:
                try:
                    data = json.loads(content)
                    self.map = Map(self, content)
                except:
                    self.map = Map(self)
            else:
                print("No save file found. Starting new game.")
                self.map = Map(self)
        
        action_menu = Menu("Actions", [
            self.messages.get_message("menu_reveal"),
            self.messages.get_message("menu_flag"),
            self.messages.get_message("menu_question"),
            self.messages.get_message("menu_clear"),
            self.messages.get_message("menu_help"),
            self.messages.get_message("menu_save_quit"),
            self.messages.get_message("menu_quit")
        ])

    def update(self):
        if not self.map:
            return

        self.map.display()
        
        action_menu = Menu("Actions", [
            self.messages.get_message("menu_reveal"),
            self.messages.get_message("menu_flag"),
            self.messages.get_message("menu_question"),
            self.messages.get_message("menu_clear"),
            self.messages.get_message("menu_help"),
            self.messages.get_message("menu_save_quit"),
            self.messages.get_message("menu_quit")
        ])
        
        action = action_menu.interact()

        if action == self.messages.get_message("menu_help"):
            print(self.messages.get_message("rules"))
            return

        if action == self.messages.get_message("menu_save_quit"):
            self.quit = True
            self.save = True
            self.is_running = False
            return

        if action == self.messages.get_message("menu_quit"):
            self.quit = True
            self.save = False
            self.is_running = False
            return

        # Action coordinates input
        print("Enter coordinates (x y):")
        try:
            coords_input = input().strip()
            parts = coords_input.split()
            if len(parts) != 2:
                print("Invalid format. Use 'x y'")
                return

            x, y = int(parts[0]), int(parts[1])
            pos = Vector2D(x, y)

            if action == self.messages.get_message("menu_reveal"):
                self.map.reveal(pos)
            elif action == self.messages.get_message("menu_flag"):
                self.map.flag(pos)
            elif action == self.messages.get_message("menu_question"):
                self.map.question(pos)
            elif action == self.messages.get_message("menu_clear"):
                self.map.clear(pos)
        except ValueError:
            print("Invalid coordinates.")

    def loose(self):
        print("\n" + "="*30)
        print(self.messages.get_message("lose"))
        print("="*30)
        self.is_running = False

    def win(self):
        print("\n" + "="*30)
        print(self.messages.get_message("win"))
        print("="*30)
        self.is_running = False

    def finalise(self) -> str:
        if self.quit:
            print("Session ended.")
            if self.save:
                # Save session
                filepath = "savegame.json"
                if self.map:
                    data = self.map.serialise_map()
                    self.fileIO.write(filepath, data, append=False)
                    print("Game saved.")
            return "quit"
        else:
            # Ask play again
            print("Play again? (y/n)")
            try:
                inp = input().strip().lower()
                if inp == 'y':
                    return "again"
                else:
                    return "quit"
            except:
                return "quit"

def main(controller):
    controller.init()
    while controller.is_running:
        controller.update()
    
    result = controller.finalise()
    
    if result == "keep":
        # Restart without full re-init to preserve context if needed, 
        # but usually means just looping logic. 
        # Based on pseudocode: CALL main(controller)
        # This effectively restarts the game loop logic if we wrap it.
        # However, to strictly follow:
        pass 
    elif result == "again":
        # CALL main()
        # Recreate controller
        controller = Controller()
        main(controller)

if __name__ == "__main__":
    # Initial setup
    controller = Controller()
    main(controller)
