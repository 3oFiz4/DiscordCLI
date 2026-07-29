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
        return False
