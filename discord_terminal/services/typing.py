import asyncio
import time


class TypingService:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.active = {}
        self.expirations = {}
        self.last_sent = {}

    def mark(self, channel, user):
        if not self.config.get(
            "settings",
            "incoming_typing_indicator",
            default=True,
        ):
            return
        if self.client.user and user.id == self.client.user.id:
            return
        key = (channel.id, user.id)
        expires = time.monotonic() + 10
        self.active[key] = {
            "name": self.client.format_author(user),
            "expires": expires,
        }
        task = self.expirations.pop(key, None)
        if task:
            task.cancel()
        self.expirations[key] = asyncio.create_task(
            self._expire(key, expires)
        )
        self.invalidate()

    async def _expire(self, key, expires):
        try:
            await asyncio.sleep(max(0, expires - time.monotonic()))
        except asyncio.CancelledError:
            return
        current = self.active.get(key)
        if current and current["expires"] <= time.monotonic():
            self.active.pop(key, None)
            self.expirations.pop(key, None)
            self.invalidate()

    def toolbar(self):
        channel = self.client.current_channel
        if not channel:
            return []
        now = time.monotonic()
        names = []
        for key, entry in list(self.active.items()):
            if entry["expires"] <= now:
                self.active.pop(key, None)
                continue
            if key[0] == channel.id:
                names.append(entry["name"])
        names = sorted(set(names))
        if not names:
            return []
        if len(names) == 1:
            text = "{} is typing ...".format(names[0])
        else:
            text = "{} are typing ...".format(", ".join(names))
        return [("class:typing", text)]

    def input_changed(self, text):
        if not self.config.get(
            "settings",
            "outgoing_typing_indicator",
            default=True,
        ):
            return
        channel = self.client.current_channel
        if not channel or not text.strip():
            return
        if text.lstrip().startswith(self.config.command_key):
            return
        now = time.monotonic()
        if now - self.last_sent.get(channel.id, 0) < 8:
            return
        self.last_sent[channel.id] = now
        asyncio.create_task(self._send(channel))

    async def _send(self, channel):
        try:
            await channel.typing()
        except Exception:
            return

    def set_outgoing(self, enabled):
        self.config.data["settings"]["outgoing_typing_indicator"] = enabled
        self.config.save()

    def outgoing_enabled(self):
        return self.config.get(
            "settings",
            "outgoing_typing_indicator",
            default=True,
        )

    def invalidate(self):
        session = self.client.input_session
        application = getattr(session, "app", None)
        if application:
            application.invalidate()
