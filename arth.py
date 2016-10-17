#!/usr/bin/env python

from collections import namedtuple
import re
import sys
import subprocess
import vt100


debugger_log = open('/tmp/arth.log', 'w')
def trace(text):
    debugger_log.write(text + '\n')
    debugger_log.flush()


def read_until(stream, terminator):
    chunk = ''
    while True:
        chunk += stream.read(1)
        if chunk.endswith(terminator):
            return chunk[:-len(terminator)]


# Time: 53 - pc: 186180 - module Format
TIME_RE = re.compile('^(.*)Time: (\d+)( - pc: (\d+) - module (.+))?\n', re.MULTILINE)
# \032\032M/Users/frantic/.opam/4.02.3/lib/ocaml/camlinternalFormat.ml:64903:65347:before
LOCATION_RE = re.compile('^\x1a\x1aM(.+):(.+):(.+):(before|after)\n', re.MULTILINE)

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
        context['file'] = match.group(1)
        context['start'] = match.group(2)
        context['end'] = match.group(3)
        context['before_or_after'] = match.group(4)

    output = re.sub(TIME_RE, parse_time, output)
    output = re.sub(LOCATION_RE, parse_location, output)
    return output, context


def debugger_command(dbgr, cmd):
    if cmd != '':
        trace('>> ' + cmd + '\n')
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    output = read_until(dbgr.stdout, '(ocd) ')
    trace(output)
    return parse_output(output)


# 950   let ppf = pp_make_formatter output
LINE_RE = re.compile('(\d+) ?(.*)')

def hl(src):
    lines = []
    for line in src.split('\n'):
        match = LINE_RE.match(line)
        if not match:
            lines.append(line + '\n')
            continue
        line_number = vt100.dim(match.group(1).rjust(5, ' ') + ' ')
        text = match.group(2)

        is_current = '<|a|>' in text or '<|b|>' in text
        if is_current:
            line_number = vt100.reverse(line_number)
            text = vt100.reverse(text.replace('<|a|>', '').replace('<|b|>', '').ljust(80))

        lines.append(line_number + text + '\n')

    return ''.join(lines)



def main():
    console = vt100.Console()
    dbgr = subprocess.Popen(['ocamldebug', '-emacs', '/Users/frantic/code/flow/bin/flow', '--help'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(debugger_command(dbgr, ''))
    return repl(dbgr, console)


def repl(dbgr, console):
    loc = dict()
    def call(cmd):
        output, context = debugger_command(dbgr, cmd)
        loc.update(context)
        return output

    op = ''
    while True:
        console.disable_line_wrap()
        listing = hl(call('list'))
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
                print(call('goto ' + cmd))
            else:
                print(vt100.blue_fg('>> ' + cmd))
                print(call(d))

        if op == 'G':
            print(call('run'))
        if op == 'g':
            print(call('reverse'))
        if op == 's':
            print(call('step'))
        if op == 'S':
            print(call('backstep'))
        if op == 'j':
            print(call('next'))
        if op == 'k':
            print(call('prev'))

        if op == 'q':
            return 0

if __name__ == '__main__':
    sys.exit(main())
