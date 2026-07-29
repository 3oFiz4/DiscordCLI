from rich.markup import escape

from discord_terminal.commands.base import CommandHandler


class BookmarkCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "bookmark"):
            self._add(text)
            return True
        if self.matches(text, "bookmarks", exact=True):
            self._list()
            return True
        if self.matches(text, "delete_bookmark"):
            self._remove(text)
            return True
        if self.matches(text, "go_to_bookmark"):
            await self._go(text)
            return True
        return False

    def _add(self, text):
        value = self.arguments(text, "bookmark").strip()
        if not value.isdigit():
            self.log("bookmark", "usage")
            return
        try:
            message = self.client.message_at(int(value))
        except Exception:
            self.log("bookmark", "bad_index")
            return
        if self.client.bookmarks.add(message):
            self.log("bookmark", "saved")
        else:
            self.log("bookmark", "exists")

    def _list(self):
        bookmarks = self.client.bookmarks.all()
        if not bookmarks:
            self.log("bookmarks", "empty")
            return
        for index, record in enumerate(bookmarks, 1):
            self.log(
                "bookmarks",
                "details",
                index=index,
                author=escape(record.get("author", "?")),
                content=escape(record.get("content", "")[:80]),
                timestamp=escape(record.get("created_at", "")),
            )

    def _remove(self, text):
        value = self.arguments(text, "delete_bookmark").strip()
        if not value.isdigit():
            self.log("delete_bookmark", "bad_index")
            return
        if self.client.bookmarks.remove(int(value) - 1):
            self.log("delete_bookmark", "removed")
        else:
            self.log("delete_bookmark", "bad_index")

    async def _go(self, text):
        value = self.arguments(text, "go_to_bookmark").strip()
        bookmarks = self.client.bookmarks.all()
        if not value.isdigit():
            self.log("go_to_bookmark", "bad_index")
            return
        index = int(value) - 1
        if index < 0 or index >= len(bookmarks):
            self.log("go_to_bookmark", "bad_index")
            return
        await self.client.go_to_record(bookmarks[index])
