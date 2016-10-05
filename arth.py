#!/usr/bin/env python

import subprocess, sys

if sys.stdout.isatty():
    def esc(code, text): return '\033[%sm%s\033[0m' % (code, text)
else:
    def esc(code, text): return text


def bold(text): return esc(1, text)
def reverse(text): return esc(7, text)


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
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

###################################################################################################

dbgr = subprocess.Popen(['ocamldebug', '/Users/frantic/code/flow/bin/flow', '--help'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def debugger_command(cmd):
    if cmd != '':
        print('>> ' + cmd)
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    res = ''
    while True:
        res += dbgr.stdout.read(1)
        if '(ocd) ' in res:
            return res[:-6]

def hl(src):
    for line in src.split('\n'):
        if '<|a|>' in line or '<|b|>' in line:
            print(reverse(line.replace('<|a|>', '').replace('<|b|>', '')))
        else:
            print(line)


print(debugger_command(''))
print(debugger_command('help'))
print(debugger_command('goto 200'))
print(debugger_command('bt'))

op = ''
while op != 'q':
    # remember
    sys.stdout.write('\0337')
    print(bold(debugger_command('b')))
    print(hl(debugger_command('list')))
    op = getch()
    sys.stdout.write('\0338')
    sys.stdout.write('\033[J')
    # restore and clear


# stdout, stderr = dbgr.communicate()
# # print('arth, the ocaml debugger')
# print(stdout)
# print(stderr)
