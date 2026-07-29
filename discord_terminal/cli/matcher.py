class CommandMatcher:
    def __init__(self, config):
        self.config = config

    def matches(self, text, command_name, exact=False):
        for alias in self.config.aliases(command_name):
            command = "{}{}".format(self.config.command_key, alias)
            if exact and text == command:
                return True
            if not exact and (text == command or text.startswith(command + " ")):
                return True
        return False

    def arguments(self, text, command_name):
        for alias in self.config.aliases(command_name):
            command = "{}{}".format(self.config.command_key, alias)
            if text == command:
                return ""
            prefix = command + " "
            if text.startswith(prefix):
                return text[len(prefix):]
        return ""
