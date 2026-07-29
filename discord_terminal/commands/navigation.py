import discord

from discord_terminal.commands.base import CommandHandler


class NavigationCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "server_nav"):
            await self._server(text)
            return True
        if self.matches(text, "channel_nav"):
            await self._channel(text)
            return True
        if self.matches(text, "dm_nav"):
            await self._dm(text)
            return True
        if self.matches(text, "scroll_old"):
            self.client.scroll_older()
            await self.client.render_history()
            return True
        if self.matches(text, "scroll_new"):
            self.client.scroll_newer()
            await self.client.render_history()
            return True
        return False

    async def _server(self, text):
        name = self.arguments(text, "server_nav")
        guild = discord.utils.find(lambda item: item.name == name, self.client.guilds)
        if guild:
            self.client.current_guild = guild
            self.log("server_nav", "success", name=guild.name)
        else:
            self.log("server_nav", "not_exist", name=name)

    async def _channel(self, text):
        if not self.client.current_guild:
            self.log("channel_nav", "no_server_selected")
            return
        name = self.arguments(text, "channel_nav")
        channel = discord.utils.find(
            lambda item: item.name == name,
            self.client.current_guild.text_channels,
        )
        if not channel:
            self.log("channel_nav", "not_exist", name=name)
            return
        try:
            self.client.current_channel = channel
            self.client.history_offset = 0
            self.log("channel_nav", "success", name=channel.name)
            await self.client.refresh_history()
        except Exception:
            self.log("channel_nav", "no_access")

    async def _dm(self, text):
        name = self.arguments(text, "dm_nav")
        user = discord.utils.find(
            lambda item: item.name == name,
            self.client.users,
        )
        if not user:
            self.log("dm_nav", "not_found", name=name)
            return
        self.client.current_guild = None
        self.client.current_channel = await user.create_dm()
        self.client.history_offset = 0
        self.log("dm_nav", "success", name=user.name)
        await self.client.refresh_history()
