import subprocess, sys, re

# See https://github.com/chalk/ansi-styles

def reset(text):         return '\033[0m' + text + '\033[0m'
def bold(text):          return '\033[1m' + text + '\033[22m'
def dim(text):           return '\033[2m' + text + '\033[22m'
def italic(text):        return '\033[3m' + text + '\033[23m'
def underline(text):     return '\033[4m' + text + '\033[24m'
def inverse(text):       return '\033[7m' + text + '\033[27m'
def hidden(text):        return '\033[8m' + text + '\033[28m'
def strikethrough(text): return '\033[9m' + text + '\033[29m'
def black(text):         return '\033[30m' + text + '\033[39m'
def red(text):           return '\033[31m' + text + '\033[39m'
def green(text):         return '\033[32m' + text + '\033[39m'
def yellow(text):        return '\033[33m' + text + '\033[39m'
def blue(text):          return '\033[34m' + text + '\033[39m'
def magenta(text):       return '\033[35m' + text + '\033[39m'
def cyan(text):          return '\033[36m' + text + '\033[39m'
def white(text):         return '\033[37m' + text + '\033[39m'
def gray(text):          return '\033[90m' + text + '\033[39m'
def grey(text):          return '\033[90m' + text + '\033[39m'
def black_bg(text):      return '\033[40m' + text + '\033[49m'
def red_bg(text):        return '\033[41m' + text + '\033[49m'
def green_bg(text):      return '\033[42m' + text + '\033[49m'
def yellow_bg(text):     return '\033[43m' + text + '\033[49m'
def blue_bg(text):       return '\033[44m' + text + '\033[49m'
def magenta_bg(text):    return '\033[45m' + text + '\033[49m'
def cyan_bg(text):       return '\033[46m' + text + '\033[49m'
def white_bg(text):      return '\033[47m' + text + '\033[49m'

def tag_to_color(match):
    open_tag = match.group(1)
    text = match.group(2)

    color_fn = globals()[open_tag]
    return color_fn(from_tags_unsafe(text))


def from_tags_unsafe(text):
    """
    Replaces "color" tags in text with actual colors. Example:

        <red_fg>Hello</red_fg>

    Don't call this function on user-provided input, it uses dark runtime
    magic to lookup color functions
    """
    return re.sub(r'<([_\w]+)>(.*)<\/\1>', tag_to_color, text)

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

