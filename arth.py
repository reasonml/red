#!/usr/bin/env python

import sys
import subprocess
import vt100

dbgr = subprocess.Popen(['ocamldebug', '/Users/frantic/code/flow/bin/flow', '--help'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def debugger_command(cmd):
    if cmd != '':
        # print('>> ' + cmd)
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
            print(vt100.reverse(line.replace('<|a|>', '').replace('<|b|>', '')))
        else:
            print(line)


print(debugger_command(''))
# print(debugger_command('help'))
# print(debugger_command('goto 200'))
# print(debugger_command('bt'))

op = ''
while True:
    vt100.push_state()
    print(hl(debugger_command('list')))
    op = vt100.getch()

    cmd = None
    if op == ':':
        try:
            cmd = raw_input(':')
        except:
            cmd = None

    vt100.pop_state()
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
