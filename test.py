import curses

class avude:
    def __init__(self):
        self.a = "a"

def main(window):
    eduva = avude()
    while type(eduva) == avude:
        key = window.getch()
        window.erase()
#        window.addch(0, 0, str(key))
        window.addstr(1, 0, chr(key))
#        swindow.addstr(2, 0, ord(key))
        window.refresh()

curses.wrapper(main)
