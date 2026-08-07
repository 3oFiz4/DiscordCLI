class CommandMatcher:
    def __init__(self, config):
        self.config = config

    def matches(self, text, command_name, exact=False):
        for alias in self.config.aliases(command_name):
            prefixes = [self.config.command_key]
            if self.config.command_key != "/":
                prefixes.append("/")
            for prefix in prefixes:
                command = "{}{}".format(prefix, alias)
                if exact and text == command:
                    return True
                if not exact and (text == command or text.startswith(command + " ")):
                    return True
        return False

    def arguments(self, text, command_name):
        for alias in self.config.aliases(command_name):
            prefixes = [self.config.command_key]
            if self.config.command_key != "/":
                prefixes.append("/")
            for prefix in prefixes:
                command = "{}{}".format(prefix, alias)
                if text == command:
                    return ""
                pfx = command + " "
                if text.startswith(pfx):
                    return text[len(pfx):]
        return ""

