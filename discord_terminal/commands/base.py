from discord_terminal.cli.matcher import CommandMatcher


class CommandHandler:
    def __init__(self, client, config, ui):
        self.client = client
        self.config = config
        self.ui = ui
        self.matcher = CommandMatcher(config)

    def matches(self, text, command, exact=False):
        return self.matcher.matches(text, command, exact=exact)

    def arguments(self, text, command):
        return self.matcher.arguments(text, command)

    def log(self, command, name, **values):
        text = self.config.log(command, name)
        if text:
            self.ui.print(text.format(**values))
