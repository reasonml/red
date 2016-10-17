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

debugger_log = open('/tmp/arth.log', 'w')
def trace(text):
    debugger_log.write(text + '\n')
    debugger_log.flush()

def debugger_command(cmd):
    global loc
    if cmd != '':
        trace('>> ' + cmd + '\n')
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    res = ''
    while True:
        res += dbgr.stdout.read(1)
        if '(ocd) ' in res:
            trace(res)
            match = LOCATION_RE.match(res)
            if match:
                loc = Location(match.group(1), match.group(2), match.group(3))

            return res[:-6]

def hl(src):
    lines = []
    for line in src.split('\n'):
        match = LINE_RE.match(line)
        if not match:
            lines.append(line)
            continue
        line_number = vt100.dim(match.group(1).rjust(5, ' ') + ' ')
        text = match.group(2)

        is_current = '<|a|>' in text or '<|b|>' in text
        if is_current:
            line_number = vt100.reverse(line_number)
            text = vt100.reverse(text.replace('<|a|>', '').replace('<|b|>', '').ljust(80))

        lines.append(line_number + text + '\n')

    return ''.join(lines)



print(debugger_command(''))
# print(debugger_command('help'))
# print(debugger_command('goto 200'))
# print(debugger_command('bt'))

console = vt100.Console()

op = ''
while True:
    console.disable_line_wrap()
    listing = hl(debugger_command('list'))
    if listing:
        console.print_text((u'\u2500[ %s ]' % loc.module) + u'\u2500' * 300)
        console.print_text(listing)
        console.print_text(u'\u2500' * 300)
    else:
        console.print_text(vt100.dim('(no source info)'))
    console.print_text(vt100.blue_fg(vt100.bold(':{0} @ {1}'.format(loc.time, loc.module))))
    console.enable_line_wrap()

    op = vt100.getch()

    cmd = None
    if op == ':' or op == ';':
        cmd = console.safe_input(':')
    if op == 'p':
        cmd = 'print ' + console.safe_input('print ')

    console.clear_last_render()

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
