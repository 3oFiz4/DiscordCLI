class BookmarkService:
    def __init__(self, store):
        self.store = store

    def all(self):
        return self.store.all()

    def add(self, message):
        record = {
            "message_id": str(message.id),
            "channel_id": str(message.channel.id),
            "guild_id": (
                str(message.guild.id)
                if getattr(message, "guild", None)
                else None
            ),
            "author_id": str(message.author.id),
            "author": str(message.author),
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "jump_url": getattr(message, "jump_url", ""),
            "attachments": [
                {
                    "id": str(attachment.id),
                    "filename": attachment.filename,
                    "url": attachment.url,
                }
                for attachment in message.attachments
            ],
        }
        return self.store.append_unique(record, "message_id")

    def remove(self, index):
        return self.store.remove_at(index)
