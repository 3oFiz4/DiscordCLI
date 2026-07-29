import discord


class VoiceService:
    def __init__(self, client):
        self.client = client
        self.voice_client = None

    def channels(self):
        guild = self.client.current_guild
        if not guild:
            return []
        return list(guild.voice_channels)

    def find(self, query):
        lowered = query.lower()
        for channel in self.channels():
            if str(channel.id) == query or channel.name.lower() == lowered:
                return channel
        return discord.utils.find(
            lambda channel: lowered in channel.name.lower(),
            self.channels(),
        )

    def current(self):
        if self.voice_client and self.voice_client.is_connected():
            return self.voice_client
        for voice_client in getattr(self.client, "voice_clients", []):
            if voice_client.is_connected():
                self.voice_client = voice_client
                return voice_client
        self.voice_client = None
        return None

    async def join(self, channel):
        current = self.current()
        if current:
            if current.channel.id != channel.id:
                await current.move_to(channel)
            return current
        self.voice_client = await channel.connect(
            reconnect=True,
            self_deaf=False,
            self_mute=False,
        )
        return self.voice_client

    async def leave(self):
        current = self.current()
        if not current:
            return False
        await current.disconnect(force=True)
        self.voice_client = None
        return True
