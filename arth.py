#!/usr/bin/env python

from collections import namedtuple
import re
import sys
import subprocess
import vt100

# Time: 53 - pc: 186180 - module Format
LOCATION_RE = re.compile('Time: (\d+) - pc: (\d+) - module (.+)')

# 950   let ppf = pp_make_formatter output
LINE_RE = re.compile('(\d+) ?(.*)')

dbgr = subprocess.Popen(['ocamldebug', '-emacs', '/Users/frantic/code/flow/bin/flow', '--help'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

Location = namedtuple('Location', ['time', 'pc', 'module'])
loc = Location(None, None, None)

def debugger_command(cmd):
    global loc
    if cmd != '':
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    res = ''
    while True:
        res += dbgr.stdout.read(1)
        if '(ocd) ' in res:
            match = LOCATION_RE.match(res)
            if match:
                loc = Location(match.group(1), match.group(2), match.group(3))

            return res[:-6].replace('\033', '^[')

def hl(src):
    for line in src.split('\n'):
        match = LINE_RE.match(line)
        if not match:
            print(line)
            continue
        line_number = vt100.dim(match.group(1).rjust(5, ' ') + ' ')
        text = match.group(2)

        is_current = '<|a|>' in text or '<|b|>' in text
        if is_current:
            line_number = vt100.reverse(line_number)
            text = vt100.reverse(text.replace('<|a|>', '').replace('<|b|>', '').ljust(80))

        sys.stdout.write(line_number + text + '\n')



print(debugger_command(''))
# print(debugger_command('help'))
# print(debugger_command('goto 200'))
# print(debugger_command('bt'))

op = ''
while True:
    vt100.push_state()
    print('')
    print(vt100.blue_fg(vt100.bold(':{0} @ {1}'.format(loc.time, loc.module))))
    print(''.ljust(86, '-'))
    print(hl(debugger_command('list')))
    vt100.pop_state()
    op = vt100.getch()

    cmd = None
    if op == ':' or op == ';':
        cmd = vt100.safe_input(':')
    if op == 'p':
        cmd = 'print ' + vt100.safe_input('print ')

    vt100.clear_to_eos()
    if cmd is not None:
        if cmd.isdigit():
            debugger_command('goto ' + cmd)
        else:
            print(vt100.blue_fg('>> ' + cmd))
            print(debugger_command(cmd))

    if op == 'G':
        debugger_command('run')
    if op == 'G':
        debugger_command('reverse')
    if op == 'j':
        debugger_command('step')
    if op == 'k':
        debugger_command('backstep')

    if op == 'q':
        sys.exit()
