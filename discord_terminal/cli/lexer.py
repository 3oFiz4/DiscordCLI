from prompt_toolkit.lexers import Lexer


class CommandLexer(Lexer):
    def __init__(self, config):
        self.config = config
        self.command_key = config.command_key
        self.valid_commands = {
            "{}{}".format(self.command_key, alias)
            for command in config.commands.values()
            for alias in command.get("aliases", [])
        }

    def lex_document(self, document):
        lines = document.lines

        def get_line(lineno):
            text = lines[lineno]
            stripped = text.lstrip()
            if stripped.startswith(self.command_key):
                padding = text[:len(text) - len(stripped)]
                token, separator, remaining = stripped.partition(" ")
                style = (
                    "class:command.valid"
                    if token in self.valid_commands
                    else "class:command"
                )
                fragments = []
                if padding:
                    fragments.append(("class:default", padding))
                fragments.append((style, token))
                if separator:
                    fragments.append(("class:command", separator + remaining))
                return fragments
            return [("class:default", text)]

        return get_line
