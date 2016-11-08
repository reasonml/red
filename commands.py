import sys
import vt100
import inspect
import functools
import textwrap

class Command:
    pass


class Shortcut(Command):
    def run(self, execute, prompt, ctx):
        return execute(self.COMMAND)


class Run(Shortcut):
    KEYS = ['>', 'r']
    HELP = 'Run the program forward'
    COMMAND = 'run'


class Reverse(Shortcut):
    KEYS = ['<', 'R']
    HELP = 'Run the program backward'
    COMMAND = 'reverse'


class Next(Shortcut):
    KEYS = ['j']
    HELP = 'Next line'
    COMMAND = 'next'


class Prev(Shortcut):
    KEYS = ['k']
    HELP = 'Previous line'
    COMMAND = 'prev'


class Step(Shortcut):
    KEYS = [']', 's']
    HELP = 'Step forward'
    COMMAND = 'step'


class Backstep(Shortcut):
    KEYS = ['[', 'S']
    HELP = 'Step backward'
    COMMAND = 'backstep'


class Yes(Shortcut):
    KEYS = ['y']
    HELP = 'Answer "y" to the question'
    COMMAND = 'y'
    HIDDEN = True


class No(Shortcut):
    KEYS = ['n']
    HELP = 'Answer "n" to the question'
    COMMAND = 'n'
    HIDDEN = True


class Timetravel(Shortcut):
    KEYS = ['t', 'g']
    HELP = 'Travel to specified time'

    def run(self, execute, prompt, ctx):
        banner = vt100.from_tags_unsafe(textwrap.dedent("""
            <bold><blue>TIME TRAVEL</blue></bold>

            <bold>1337 </bold> - jump to specified time
            <bold>+100 </bold> - jump 100 time units forward
            <bold>-100 </bold> - jump 100 time units backwards

            <dim>(time travel)</dim> """))

        time = prompt(banner)
        if not len(time):
            return

        now = int(ctx['loc'].get('time') or 0)
        if time.startswith('-'):
            location = now - int(time[1:])
        elif time.startswith('+'):
            location = now + int(time[1:])
        elif time.isdigit():
            location = int(time)
        else:
            return

        return execute('goto ' + str(location))


class Print(Command):
    KEYS = ['p']
    HELP = 'Print variable value'

    def run(self, execute, prompt, ctx):
        var = prompt(vt100.magenta(vt100.dim('(print) ')))
        if not len(var):
            return
        output = execute('print ' + var)
        return vt100.magenta(output)


class Quit(Shortcut):
    KEYS = ['q']
    HELP = 'Quit'
    COMMAND = 'quit'


class Breakpoint(Command):
    KEYS = ['b']
    HELP = 'Add, remove and list breakpoints'

    def format_breakpoints(self, breakpoints):
        if len(breakpoints) == 0:
            return vt100.dim('  No breakpoins added yet')

        lines = []
        for b in breakpoints:
            lines.append(vt100.red(('#' + str(b.get('num'))).rjust(5)) + ' ' + (b.get('file') + ':' + str(b.get('line'))).ljust(30)
                + vt100.dim(' pc = ' + str(b.get('pc'))))

        return '\n'.join(lines)

    def command(self, prompt, ctx):
        loc = ctx['loc']
        breakpoints = ctx['breakpoints']

        banner = vt100.from_tags_unsafe(textwrap.dedent("""
            <bold><blue>BREAKPOINTS</blue></bold>

            {0}

            <bold>42        </bold> - add breakpoint for current module ({1}) at line 42
            <bold>Module:42 </bold> - add breakpoint for specified module Module at line 42
            <bold>Module.foo</bold> - add breakpoint for Module.foo function
            <bold>-#2       </bold> - remove breakoint #2
            <bold><enter>   </bold> - do nothing


            <dim>(break)</dim> """)).format(self.format_breakpoints(breakpoints), loc.get('module'))

        command = prompt(banner)

        if command:
            if command.startswith('-#'):
                return 'delete ' + command[2:]
            elif command.isdigit():
                if loc.get('module'):
                    return 'break @ ' + loc.get('module') + ' ' + command
            else:
                if ':' in command:
                    return 'break @ ' + command.replace(':', ' ')
                else:
                    return 'break ' + command

    def run(self, execute, prompt, ctx):
        command = self.command(prompt, ctx)
        # TODO: check if the breakpoint was really added
        # TODO: breakpoints don't work at the beginning/end of the program
        if command:
            return execute(command)


class Custom(Command):
    KEYS = [':', ';']
    HELP = 'Custom OcamlDebug command'

    def run(self, execute, prompt, ctx):
        command = prompt(vt100.dim('(odb) '))
        if not len(command):
            return
        output = execute(command)
        return vt100.blue('>> {0}\n'.format(command)) + output


def all_command_classes():
    # Suck hack, wow
    with open(__file__.replace('.pyc', '.py'), 'r') as f:
        content = f.read()

    class_pos = lambda pair: content.find('class ' + pair[0])
    cmds = sorted(inspect.getmembers(sys.modules[__name__], inspect.isclass), key=class_pos)
    return [cls for (_, cls) in cmds if hasattr(cls, 'HELP')]
