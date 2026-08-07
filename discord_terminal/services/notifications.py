import asyncio


class NotificationService:
    def __init__(self, client, config, store, session, audio, ui):
        self.client = client
        self.config = config
        self.store = store
        self.session = session
        self.audio = audio
        self.ui = ui
        self.scan_task = None

    def all(self):
        records = self.store.all()
        return sorted(
            records,
            key=lambda record: record.get("created_at", ""),
            reverse=False,
        )

    def clear(self):
        self.store.clear()


    def is_notification(self, message):
        if message.author == self.client.user:
            return False
        if getattr(message, "guild", None) is None:
            return True
        if self.client.user in getattr(message, "mentions", []):
            return True
        if getattr(message, "mention_everyone", False):
            return True
        username = "@{}".format(self.client.user.name).lower()
        return username in (message.content or "").lower()

    def record_live(self, message):
        if not self.is_notification(message):
            return False
        added = self._record(message)
        if added:
            self.audio.play_for_message(message)
        return added

    def start_scan(self):
        if not self.config.get(
            "settings",
            "notification_scan",
            "enabled",
            default=True,
        ):
            return
        if self.scan_task and not self.scan_task.done():
            return
        after, before = self.session.scan_window()
        if not after or not before or after >= before:
            return
        self.scan_task = asyncio.create_task(self._scan(after, before))

    async def _scan(self, after, before):
        delay = self.config.get(
            "settings",
            "notification_scan",
            "channel_delay_seconds",
            default=0.75,
        )
        limit = self.config.get(
            "settings",
            "notification_scan",
            "max_messages_per_channel",
            default=None,
        )
        channels = self._channels()
        for channel in channels:
            try:
                async for message in channel.history(
                    limit=limit,
                    after=after,
                    before=before,
                    oldest_first=True,
                ):
                    if self.is_notification(message):
                        self._record(message)
            except Exception:
                pass
            if delay:
                await asyncio.sleep(delay)

    def _channels(self):
        channels = []
        seen = set()
        for channel in list(self.client.get_all_channels()) + list(
            self.client.private_channels
        ):
            channel_id = getattr(channel, "id", None)
            if channel_id is None or channel_id in seen:
                continue
            if not hasattr(channel, "history"):
                continue
            if not self._can_read(channel):
                continue
            seen.add(channel_id)
            channels.append(channel)
        return channels

    def _can_read(self, channel):
        guild = getattr(channel, "guild", None)
        if guild is None:
            return True
        member = guild.get_member(self.client.user.id)
        if not member:
            return True
        permissions = channel.permissions_for(member)
        return permissions.view_channel and permissions.read_message_history

    def _record(self, message):
        record = {
            "message_id": str(message.id),
            "channel_id": str(message.channel.id),
            "channel": str(message.channel),
            "guild_id": (
                str(message.guild.id)
                if getattr(message, "guild", None)
                else None
            ),
            "guild": str(message.guild) if getattr(message, "guild", None) else None,
            "author_id": str(message.author.id),
            "author": str(message.author),
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "jump_url": getattr(message, "jump_url", ""),
        }
        return self.store.append_unique(record, "message_id")
