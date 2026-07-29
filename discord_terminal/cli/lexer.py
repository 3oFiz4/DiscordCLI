from prompt_toolkit.lexers import Lexer


class CommandLexer(Lexer):
    def __init__(self, command_key):
        self.command_key = command_key

    def lex_document(self, document):
        text = document.text

        def get_line(lineno):
            if text.lstrip().startswith(self.command_key):
                return [("class:command", text)]
            return [("class:default", text)]

        return get_line
