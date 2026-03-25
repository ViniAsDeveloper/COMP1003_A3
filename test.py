import curses

def main(window):
    while True:
        key = window.getch()
        window.erase()
        window.addch(0, 0, str(key))
        window.addstr(1, 0, chr(key))
        window.addstr(2, 0, ord(key))
        window.refresh()

curses.wrapper(main)
