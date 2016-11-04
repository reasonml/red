#!/usr/bin/env python

from collections import namedtuple
import commands
import re
import os
import sys
import subprocess
import vt100
import readline
import atexit
import textwrap
import inspect


debugger_log = open('/tmp/red.log', 'w')
def trace(text):
    debugger_log.write(text)
    debugger_log.flush()


def read_until(stream, terminators):
    chunk = ''
    while not stream.closed:
        byte = stream.read(1)
        if not byte:
            return chunk

        trace(byte)

        chunk += byte
        for terminator in terminators:
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
        trace(cmd + '\n')
        dbgr.stdin.write(cmd + '\n')
        dbgr.stdin.flush()

    output = read_until(dbgr.stdout, ['(ocd) ', '(y or n) '])
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


def main(args):
    histfile = os.path.join(os.path.expanduser("~"), ".red_history")
    try:
        readline.read_history_file(histfile)
        readline.set_history_length(1000)
    except IOError:
        pass
    atexit.register(readline.write_history_file, histfile)
    del histfile


    command_line = []
    breakpoints = []
    for arg in args:
        if arg.startswith('@'):
            breakpoints.append(arg[1:])
        else:
            command_line.append(arg)
    dbgr = subprocess.Popen(['ocamldebug', '-emacs'] + command_line,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(debugger_command(dbgr, '')[0].replace('\tOCaml Debugger version ', vt100.red(u'\u2022 RED') + ' OCamlDebug v'))
    print(vt100.dim('Press ? for help'))
    print(debugger_command(dbgr, 'start')[0])

    auto_run = True
    for bp in breakpoints:
        if bp == '':
            auto_run = False
        else:
            print(debugger_command(dbgr, 'break @ ' + bp.replace(':', ' '))[0])

    console = vt100.Console()
    return repl(dbgr, console, auto_run)


def repl(dbgr, console, auto_run):
    command_classes = commands.all_command_classes()

    loc = dict()
    breakpoints = list()

    def execute(cmd):
        output, context = debugger_command(dbgr, cmd)
        loc.update(context)
        return output

    def prompt(text):
        lines = text.split('\n')
        if len(lines) > 1:
            console.print_text('\n'.join(lines[:-1]))
        return console.safe_input(lines[-1])

    if auto_run:
        print(execute('run'))

    op = ''
    show_help = False
    while dbgr.poll() is None:
        breakpoints = parse_breakpoints(execute('info break'))
        console.disable_line_wrap()
        file_name = loc.get('file')
        listing = hl(execute('list'), breakpoint_lines_for_file(breakpoints, file_name))
        if listing:
            console.print_text((u'\u2500[ %s ]' % loc.get('file')) + u'\u2500' * 300)
            console.print_text(listing)
            console.print_text(u'\u2500' * 300)
        else:
            module = loc.get('module')
            if module:
                console.print_text(vt100.dim('(no source info for {0})'.format(module)))
            else:
                console.print_text(vt100.dim('(no source info)'))
        console.print_text(vt100.blue(vt100.bold('Time: {0} PC: {1}'.format(loc.get('time'), loc.get('pc')))))
        console.enable_line_wrap()

        if show_help:
            console.print_text(help(command_classes))

        op = vt100.getch()
        show_help = op == '?'
        cmd_cls = find_command_for_key(command_classes, op)
        if not cmd_cls:
            console.clear_last_render()
            continue

        console.print_text(vt100.bold(op) + ' ' + vt100.dim(cmd_cls.HELP))
        output = cmd_cls().run(execute, prompt, {'breakpoints': breakpoints, 'loc': loc})
        console.clear_last_render()
        if output and len(output):
            print(output)

def help(command_classes):
    return '\n'.join([
        '{0}\t{1}'.format(vt100.bold(cls.KEYS[0]), cls.HELP)
        for cls in command_classes
        if not hasattr(command_classes, 'HIDDEN')])

def find_command_for_key(command_classes, key):
    for cls in command_classes:
        if key in cls.KEYS:
            return cls


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

