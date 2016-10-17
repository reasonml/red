#!/usr/bin/env python

from collections import namedtuple
import re
import sys
import subprocess
import vt100

# Time: 53 - pc: 186180 - module Format
TIME_RE = re.compile('.*Time: (\d+) - pc: (\d+) - module (.+)')
# \032\032M/Users/frantic/.opam/4.02.3/lib/ocaml/camlinternalFormat.ml:64903:65347:before
LOCATION_RE = re.compile('.*\x1a\x1aM(.+):(.+):(.+):(before|after)', re.S)

# 950   let ppf = pp_make_formatter output
LINE_RE = re.compile('(\d+) ?(.*)')

dbgr = subprocess.Popen(['ocamldebug', '-emacs', '/Users/frantic/code/flow/bin/flow', '--help'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Location = namedtuple('Location', ['time', 'pc', 'module'])
loc = dict()

debugger_log = open('/tmp/arth.log', 'w')
def trace(text):
    debugger_log.write(text + '\n')
    debugger_log.flush()

def debugger_command(cmd):
    if cmd != '':
        trace('>> ' + cmd + '\n')
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    res = ''
    while True:
        res += dbgr.stdout.read(1)
        if '(ocd) ' in res:
            trace(res)
            match = TIME_RE.match(res)
            if match:
                loc['time'] = match.group(1)
                loc['pc'] = match.group(2)
                loc['module'] = match.group(3)

            match = LOCATION_RE.match(res)
            if match:
                loc['file'] = match.group(1)
                loc['start'] = match.group(2)
                loc['end'] = match.group(3)
                loc['before_or_after'] = match.group(4)

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
        console.print_text((u'\u2500[ %s ]' % loc.get('file')) + u'\u2500' * 300)
        console.print_text(listing)
        console.print_text(u'\u2500' * 300)
    else:
        console.print_text(vt100.dim('(no source info)'))
    console.print_text(vt100.blue_fg(vt100.bold('Time: {0} PC: {1}'.format(loc.get('time'), loc.get('pc')))))
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
