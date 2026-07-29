from rich.markup import escape

from discord_terminal.commands.base import CommandHandler


class NotificationCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "notifications", exact=True):
            self._list()
            return True
        if self.matches(text, "go_to_notification"):
            await self._go(text)
            return True
        return False

    def _list(self):
        notifications = self.client.notifications.all()
        if not notifications:
            self.log("notifications", "no_pings")
            return
        for index, record in enumerate(notifications, 1):
            self.log(
                "notifications",
                "ping_details",
                index=index,
                author=escape(record.get("author", "?")),
                channel=escape(record.get("channel", "?")),
                content=escape(record.get("content", "")[:80]),
                timestamp=escape(record.get("created_at", "")),
            )

    async def _go(self, text):
        value = self.arguments(text, "go_to_notification").strip()
        notifications = self.client.notifications.all()
        if not value.isdigit():
            self.log("go_to_notification", "bad_index")
            return
        index = int(value) - 1
        if index < 0 or index >= len(notifications):
            self.log("go_to_notification", "bad_index")
            return
        record = notifications[index]
        await self.client.go_to_record(record)
