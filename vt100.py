import subprocess, sys

# See http://www.ccs.neu.edu/research/gpc/MSim/vona/terminal/VT100_Escape_Codes.html

def color(code, text): return '\033[%sm%s\033[0m' % (code, text)
def bold(text): return color(1, text)
def dim(text): return color(2, text)
def reverse(text): return color(7, text)
def underline(text): return color(4, text)
def blue_fg(text): return color(34, text)
def red_fg(text): return color(31, text)
def red_bg(text): return color(41, text)
def green_bg(text): return color(42, text)

class Console:
    def __init__(self):
        self.out = sys.stdout
        self.lines_printed = 0

    def clear_last_render(self):
        for i in range(self.lines_printed):
            self.out.write('\033[1A\033[2K')
        self.lines_printed = 0

    def enable_line_wrap(self):
        self.out.write('\033[?7h')

    def disable_line_wrap(self):
        self.out.write('\033[?7l')

    def print_text(self, text):
        for line in text.splitlines():
            self.out.write(line + '\n')
            self.lines_printed += 1

    def safe_input(self, prompt=None):
        self.lines_printed += 1
        try:
            return raw_input(prompt)
        except:
            pass

def push_state():
    sys.stdout.write('\0337')

def pop_state():
    sys.stdout.write('\0338')
    sys.stdout.flush()

def clear_to_eos():
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

