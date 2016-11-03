#!/usr/bin/env python

from collections import namedtuple
import re
import os
import sys
import subprocess
import vt100
import readline
import atexit
import textwrap


debugger_log = open('/tmp/red.log', 'w')
def trace(text):
    debugger_log.write(text + '\n')
    debugger_log.flush()


def read_until(stream, terminator):
    chunk = ''
    while not stream.closed:
        byte = stream.read(1)
        if not byte:
            return chunk

        chunk += byte
        if chunk.endswith(terminator):
            return chunk[:-len(terminator)]


# Time: 53 - pc: 186180 - module Format
TIME_RE = re.compile('^(.*)Time: (\d+)( - pc: (\d+) - module (.+))?\n', re.MULTILINE)
# \032\032M/Users/frantic/.opam/4.02.3/lib/ocaml/camlinternalFormat.ml:64903:65347:before
LOCATION_RE = re.compile('^\x1a\x1a(H|M(.+):(.+):(.+):(before|after))\n', re.MULTILINE)

def parse_output(output):
    context = dict()
    def parse_time(match):
        context['time'] = match.group(2)
        context['pc'] = match.group(4)
        context['module'] = match.group(5)
        prefix = match.group(1)
        if prefix:
            return match.group(1) + '\n'
        return ''

    def parse_location(match):
        context['file'] = match.group(2)
        context['start'] = match.group(3)
        context['end'] = match.group(4)
        context['before_or_after'] = match.group(5)

    output = re.sub(TIME_RE, parse_time, output)
    output = re.sub(LOCATION_RE, parse_location, output)
    return output, context


# 1    1646532  file src/flow.ml, line 62, characters 5-1272
BREAKPOINT_RE = re.compile("^\s*(\d+)\s+(\d+)\s+file (\S+), line (\d+)", re.MULTILINE)

def parse_breakpoints(output):
    breakpoints = []
    for match in BREAKPOINT_RE.finditer(output):
        breakpoints.append({'num': int(match.group(1)), 'pc': int(match.group(2)),
            'file': match.group(3), 'line': int(match.group(4))})

    return breakpoints

def breakpoint_lines_for_file(breakpoints, file_name):
    if not file_name:
        return []

    lines = []
    for b in breakpoints:
        if file_name.endswith(b.get('file')):
            lines.append(b.get('line'))

    return lines


def debugger_command(dbgr, cmd):
    if cmd != '':
        trace('>> ' + cmd + '\n')
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    output = read_until(dbgr.stdout, '(ocd) ') # TODO: support (y or n)
    trace(output)
    return parse_output(output)


# 950   let ppf = pp_make_formatter output
LINE_RE = re.compile('(\d+) ?(.*)')

def hl(src, breakpoint_lines):
    lines = []
    for line in src.split('\n'):
        match = LINE_RE.match(line)
        if not match:
            if line:
                lines.append(line + '\n')
            continue

        line_number = match.group(1)
        text = match.group(2)
        has_breakpoint = int(line_number) in breakpoint_lines
        is_current = '<|a|>' in text or '<|b|>' in text
        a_ptrn = re.compile("(\S?)<\|a\|>")
        b_ptrn = re.compile("<\|b\|>(\S?)")

        text = re.sub(a_ptrn, vt100.bold('\\1'), text)
        text = re.sub(b_ptrn, vt100.bold('\\1'), text)
        # text = text.replace('<|a|>', '').replace('<|b|>', '')

        symbol = u'\u2022' if has_breakpoint else ' '

        # Can't use red twice, the closing color tag will mess the outputs
        if not is_current:
            symbol = vt100.red(symbol)

        result = ' ' + symbol + ' ' + vt100.dim(line_number.rjust(3)) + ' ' + text.ljust(80)

        if is_current:
            if has_breakpoint:
                result = vt100.red(result)
            result = vt100.inverse(result)

        lines.append(result + '\n')

    return ''.join(lines)


def format_breakpoints(breakpoints):
    if len(breakpoints) == 0:
        return vt100.dim('  No breakpoins added yet')

    lines = []
    for b in breakpoints:
        lines.append(vt100.red(('#' + str(b.get('num'))).rjust(5)) + ' ' + (b.get('file') + ':' + str(b.get('line'))).ljust(30)
            + vt100.dim(' pc = ' + str(b.get('pc'))))

    return '\n'.join(lines)


def main():
    histfile = os.path.join(os.path.expanduser("~"), ".red_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)
    del histfile

    console = vt100.Console()
    dbgr = subprocess.Popen(['ocamldebug', '-emacs', '/Users/frantic/code/flow/bin/flow', '--help'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(debugger_command(dbgr, '')[0]) # TODO: issue `start`?
    return repl(dbgr, console)


def repl(dbgr, console):
    built_in_commands = {
        'G': 'run',  # also r, >
        'g': 'reverse', # also R, <
        's': 'step',
        'S': 'backstep',
        'j': 'next',
        'k': 'prev',
        'q': 'quit',
    }
    loc = dict()
    breakpoints = list()
    def call(cmd):
        output, context = debugger_command(dbgr, cmd)
        loc.update(context)
        return output

    op = ''
    while dbgr.poll() is None:
        console.disable_line_wrap()
        breakpoints = parse_breakpoints(call('info break'))
        file_name = loc.get('file')
        listing = hl(call('list'), breakpoint_lines_for_file(breakpoints, file_name))
        if listing:
            console.print_text((u'\u2500[ %s ]' % loc.get('file')) + u'\u2500' * 300)
            console.print_text(listing)
            console.print_text(u'\u2500' * 300)
        else:
            console.print_text(vt100.dim('(no source info)'))
        console.print_text(vt100.blue(vt100.bold('Time: {0} PC: {1}'.format(loc.get('time'), loc.get('pc')))))
        console.enable_line_wrap()

        op = vt100.getch()

        echo = False

        if op == ':' or op == ';':
            cmd = console.safe_input(':')
            if cmd.isdigit():
                cmd = 'goto ' + cmd
            else:
                echo = True
        elif op == 'p':
            cmd = 'print ' + console.safe_input('print ')
            echo = True
        elif op == 'b':
            console.print_text(vt100.bold(vt100.blue('\nBREAKPOINTS')))
            console.print_text(format_breakpoints(breakpoints))
            console.print_text(textwrap.dedent("""
                42        - add breakpoint for current module (%s) at line 42
                Module 42 - add breakpoint for specified module Module at line 42
                Module.foo - add breakpoint for Module.foo function
                -#2       - remove breakoint #2
                <enter>   - do nothing
            """ % (loc.get('module'))))
            bp_cmd = console.safe_input(': ')
            cmd = ''
            if bp_cmd:
                if bp_cmd.startswith('-#'):
                    cmd = 'delete ' + bp_cmd[2:]
                elif bp_cmd.isdigit():
                    if loc.get('module'):
                        cmd = 'break @ ' + loc.get('module') + ' ' + bp_cmd
                else:
                    if ' ' in bp_cmd:
                        cmd = 'break @ ' + bp_cmd
                    else:
                        cmd = 'break ' + bp_cmd
        elif op == 'B':
            # TODO: Toggle breakpoint on current line
            pass
        else:
            cmd = built_in_commands.get(op)

        console.clear_last_render()

        if not cmd:
            continue


        if echo:
            print(vt100.blue('>> ' + cmd))

        output = call(cmd)
        if output:
            print output

if __name__ == '__main__':
    sys.exit(main())
