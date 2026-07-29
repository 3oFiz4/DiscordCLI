import discord

from discord_terminal.services.native_voice import NativeVoiceLoader
from discord_terminal.services.voice_audio import VoiceAudioBridge


class VoiceService:
    def __init__(self, client):
        self.client = client
        self.voice_client = None
        self.audio = VoiceAudioBridge(client)
        self.native = NativeVoiceLoader()

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
        native_module = self.native.load()
        if current:
            if current.channel.id != channel.id:
                await current.move_to(channel)
            if not self.audio.active:
                current_module = (
                    native_module
                    if hasattr(current, "listen")
                    else None
                )
                self.audio.start(
                    current,
                    current_module,
                    self.native.diagnostic(),
                )
            return current
        voice_class = (
            native_module.VoiceClient
            if native_module
            else discord.VoiceClient
        )
        try:
            self.voice_client = await channel.connect(
                cls=voice_class,
                reconnect=True,
                self_deaf=False,
                self_mute=False,
            )
        except Exception as error:
            detail = self.native.diagnostic()
            raise RuntimeError(
                "{}: {}. Native voice diagnostic: {}".format(
                    type(error).__name__,
                    error,
                    detail,
                )
            )
        try:
            self.audio.start(
                self.voice_client,
                native_module,
                self.native.diagnostic(),
            )
        except Exception:
            await self.voice_client.disconnect(force=True)
            self.voice_client = None
            raise
        return self.voice_client

    async def leave(self):
        current = self.current()
        if not current:
            return False
        self.audio.stop()
        await current.disconnect(force=True)
        self.voice_client = None
        return True

    def members(self):
        current = self.current()
        if not current:
            return []
        speaking = self.audio.speaking_ids()
        entries = []
        for member in current.channel.members:
            voice = getattr(member, "voice", None)
            entries.append(
                {
                    "name": self.client.format_author(member),
                    "speaking": member.id in speaking,
                    "self": self.client.user and member.id == self.client.user.id,
                    "muted": bool(
                        voice
                        and (
                            getattr(voice, "mute", False)
                            or getattr(voice, "self_mute", False)
                        )
                    ),
                    "deafened": bool(
                        voice
                        and (
                            getattr(voice, "deaf", False)
                            or getattr(voice, "self_deaf", False)
                        )
                    ),
                }
            )
        return entries

    def speaking_names(self):
        return [
            member["name"]
            for member in self.members()
            if member["speaking"]
        ]

    def toolbar(self):
        current = self.current()
        if not current:
            return []
        text = "VC #{} | {} members".format(
            current.channel.name,
            len(current.channel.members),
        )
        speakers = self.speaking_names()
        if speakers:
            text += " | speaking: {}".format(", ".join(speakers))
        if not self.audio.receive_enabled:
            text += " | transmit only"
        return [("class:voice", text)]
