import sys

from rich.console import Console


class TerminalUI:
    def __init__(self, theme):
        self.console = Console(theme=theme)

    def print(self, value=""):
        self.console.print(value)

    def rule(self):
        self.console.rule()

    def clear(self):
        self.console.clear()

    def clear_buffer(self):
        stream = self.console.file or sys.stdout
        stream.write("\033[3J\033[2J\033[H]")
        stream.flush()
