from discord_terminal.commands.base import CommandHandler


class QuickGoCommands(CommandHandler):
    async def handle(self, text):
        if not self.matches(text, "quick_go"):
            return False
        await self._go(text)
        return True

    async def _go(self, text):
        query = self.arguments(text, "quick_go").strip()
        if query.isdigit():
            entry = self.client.quick_go.numbered(int(query))
            if entry:
                await self.client.quick_go.go(entry)
                return
        results = self.client.quick_go.search(query)
        if len(results) == 1:
            await self.client.quick_go.go(results[0])
            return
        if not results:
            self.log("quick_go", "not_found", query=query)
            return
        self.log("quick_go", "results")
        for index, entry in enumerate(results, start=1):
            self.ui.print(
                "[i]{}. {}[/i]".format(index, entry["label"])
            )
        self.log("quick_go", "choose")
