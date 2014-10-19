import re
import actions


class Command(object):
    def __init__(self):
        pass

    @classmethod
    def parse_command(cls, line):
        """ Factory method to create a command from a line. """
        words = line.split(" ")
        if not len(words):
            return None
        command_name = words[0].lower()
        if command_name in COMMANDS.keys():
            return COMMANDS[command_name](line[len(command_name) + 1:])
        else:
            # TODO: what should I do if an unknown command is received?
            raise Exception("Unknown command received: '%s'" % command_name)

    def execute(self, device):
        pass


class CommandArgumentException(BaseException):
    pass


class SetModeCommand(Command):
    arguments_regex = re.compile("(?P<mode>\d+)")

    def __init__(self, line):
        args = self.arguments_regex.match(line)
        if not args:
            raise CommandArgumentException("Incorrect number of arguments to the 'mod'"
                                           " command. Arguments should be 'mode'.")

        self.mode = args.group("mode")

    def execute(self, device):
        device.set_mode(self.mode)


class SetColorCommand(Command):
    arguments_regex = re.compile("(?P<red>\d+) (?P<green>\d+) (?P<blue>\d+)")

    def __init__(self, line):
        args = self.arguments_regex.match(line)
        if not args:
            raise CommandArgumentException("Incorrect number of arguments to the 'rgb'"
                                           " command. Arguments should be 'red' 'green'"
                                           " 'blue'")

        self.red = int(args.group('red'))
        self.green = int(args.group('green'))
        self.blue = int(args.group('blue'))

    def execute(self, device):
        device.set_key_color(self.red, self.green, self.blue)


class BindToKeyCommand(Command):
    arguments_regex = re.compile("(?P<g13_key>[a-zA-Z0-9_]+) "
                                 "(?P<target_key>[a-zA-Z0-9_]+)")

    def __init__(self, line):
        args = self.arguments_regex.match(line)
        if not args:
            raise CommandArgumentException()

        self.g13_key = args.group("g13_key")
        self.target_key = args.group("target_key")

    def execute(self, device):
        device.bind_key(self.g13_key, actions.SendKeyAction(self.target_key))


class BindToSequenceCommand(Command):
    pass


class BindToScriptCommand(Command):
    pass


COMMANDS = {
    "rgb": SetColorCommand,
    "mod": SetModeCommand,
    "bind": BindToKeyCommand,
    "script": BindToScriptCommand,
    "seq": BindToSequenceCommand

}
