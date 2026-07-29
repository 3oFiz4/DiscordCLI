from discord_terminal.commands.base import CommandHandler


class VoiceCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "voice_join"):
            await self._join(text)
            return True
        if self.matches(text, "voice_leave", exact=True):
            await self._leave()
            return True
        if self.matches(text, "voice_status", exact=True):
            self._status()
            return True
        return False

    async def _join(self, text):
        if not self.client.current_guild:
            self.log("voice_join", "no_server")
            return
        query = self.arguments(text, "voice_join").strip()
        if not query:
            channels = self.client.voice.channels()
            if not channels:
                self.log("voice_join", "none")
                return
            self.log("voice_join", "available")
            for channel in channels:
                self.ui.print("[i]{}[/i]".format(channel.name))
            self.log("voice_join", "usage")
            return
        channel = self.client.voice.find(query)
        if not channel:
            self.log("voice_join", "not_found", name=query)
            return
        try:
            voice_client = await self.client.voice.join(channel)
            self.log(
                "voice_join",
                "joined",
                name=voice_client.channel.name,
            )
        except Exception as error:
            self.log("voice_join", "error", error_msg=str(error))

    async def _leave(self):
        try:
            if await self.client.voice.leave():
                self.log("voice_leave", "left")
            else:
                self.log("voice_leave", "not_connected")
        except Exception as error:
            self.log("voice_leave", "error", error_msg=str(error))

    def _status(self):
        voice_client = self.client.voice.current()
        if voice_client:
            self.log(
                "voice_status",
                "connected",
                name=voice_client.channel.name,
            )
        else:
            self.log("voice_status", "disconnected")
