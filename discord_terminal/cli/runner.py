import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style

from discord_terminal.cli.completer import DiscordCompleter
from discord_terminal.cli.lexer import CommandLexer


class CliRunner:
    def __init__(self, client, config, ui, handlers):
        self.client = client
        self.config = config
        self.ui = ui
        self.handlers = handlers
        self.style = Style.from_dict(self.config.get("colorInput", default={}))
        self.session = PromptSession(
            completer=DiscordCompleter(client, config),
            lexer=CommandLexer(config),
            style=self.style,
            bottom_toolbar=self.client.typing.toolbar,
        )
        self.session.default_buffer.on_text_changed += self._input_changed
        self.client.input_session = self.session

    def _input_changed(self, buffer):
        self.client.typing.input_changed(buffer.text)

    async def run(self):
        self.ui.clear()
        self.ui.print(self.config.get("events", "preReady", default=""))
        while not self.client.is_closed():
            try:
                with patch_stdout(sys.__stdout__):
                    text = await self.session.prompt_async(
                        [("class:prompt", "> ")],
                        style=self.style,
                    )
            except (EOFError, KeyboardInterrupt):
                await self.client.close()
                break

            command = text.strip()
            self.ui.clear()
            handled = False
            for handler in self.handlers:
                if await handler.handle(command):
                    handled = True
                    break
            if not handled:
                await self.client.send_message(command)
