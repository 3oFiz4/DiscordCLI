from discord_terminal.commands.base import CommandHandler


class GeneralCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "exit", exact=True):
            self.log("exit", "onExit")
            await self.client.close()
            return True
        if self.matches(text, "changelog", exact=True):
            self.ui.print(self.config.log("changelog", "content"))
            return True
        if self.matches(text, "help", exact=True):
            self.ui.print(self.config.log("help", "content"))
            return True
        if self.matches(text, "config_editor", exact=True):
            self.ui.print("Do not use me yet. I am not finished yet")
            return True
        if self.matches(text, "typing_indicator"):
            self._typing(text)
            return True
        return False

    def _typing(self, text):
        value = self.arguments(text, "typing_indicator").strip().lower()
        if value in ("on", "true", "1"):
            self.client.typing.set_outgoing(True)
            self.log("typing_indicator", "enabled")
            return
        if value in ("off", "false", "0"):
            self.client.typing.set_outgoing(False)
            self.log("typing_indicator", "disabled")
            return
        state = "on" if self.client.typing.outgoing_enabled() else "off"
        self.log("typing_indicator", "status", state=state)
