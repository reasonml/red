import subprocess, sys

# See http://www.ccs.neu.edu/research/gpc/MSim/vona/terminal/VT100_Escape_Codes.html

def color(code, text): return '\033[%sm%s\033[0m' % (code, text)
def bold(text): return color(1, text)
def reverse(text): return color(7, text)
def underline(text): return color(4, text)
def blue_fg(text): return color(34, text)
def red_fg(text): return color(31, text)
def red_bg(text): return color(41, text)
def green_bg(text): return color(42, text)

def push_state():
    sys.stdout.write('\0337')

def pop_state():
    sys.stdout.write('\0338')
    sys.stdout.flush()
    sys.stdout.write('\033[J')
    sys.stdout.flush()

class _Getch:
    """
    Gets a single character from standard input.
    Does not echo to the screen.
    """
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

