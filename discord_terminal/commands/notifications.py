from rich.markup import escape

from discord_terminal.commands.base import CommandHandler


class NotificationCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "notifications", exact=True):
            self._list()
            return True
        if self.matches(text, "clear_notifications", exact=True):
            self._clear()
            return True
        if self.matches(text, "go_to_notification"):
            await self._go(text)
            return True
        return False

    def _clear(self):
        self.client.notifications.clear()
        self.log("clear_notifications", "cleared")


    def _list(self):
        notifications = self.client.notifications.all()
        if not notifications:
            self.log("notifications", "no_pings")
            return

        total = len(notifications)
        num_gradient = min(total, 10)
        start_gradient_idx = total - num_gradient

        for index, record in enumerate(notifications, 1):
            list_idx = index - 1
            if list_idx < start_gradient_idx:
                t = 0.0
            elif num_gradient <= 1:
                t = 1.0
            else:
                pos = list_idx - start_gradient_idx
                t = pos / (num_gradient - 1)

            r = int(90 + (228 - 90) * t)
            g = int(90 + (228 - 90) * t)
            b = int(90 + (228 - 90) * t)
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            author = escape(record.get("author", "?"))
            channel = escape(record.get("channel", "?"))
            content = escape(record.get("content", "")[:80])
            timestamp = escape(record.get("created_at", ""))

            line = f"[{color_hex}]{index}. {author} @ {channel}: {content} ({timestamp})[/{color_hex}]"
            self.ui.print(line, highlight=False)


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
