import asyncio
from pathlib import Path

from discord_terminal.cli.runner import CliRunner
from discord_terminal.client import DiscordTerminalClient
from discord_terminal.commands.bookmarks import BookmarkCommands
from discord_terminal.commands.general import GeneralCommands
from discord_terminal.commands.media import MediaCommands
from discord_terminal.commands.messages import MessageCommands
from discord_terminal.commands.navigation import NavigationCommands
from discord_terminal.commands.notifications import NotificationCommands
from discord_terminal.commands.quick_go import QuickGoCommands
from discord_terminal.commands.voice import VoiceCommands
from discord_terminal.config import Configuration
from discord_terminal.paths import ApplicationPaths
from discord_terminal.services.credentials import ArgumentParser, CredentialStore
from discord_terminal.storage import JsonStore
from discord_terminal.time import Clock, SessionTracker
from discord_terminal.ui.console import TerminalUI


class Application:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.config = Configuration(self.base_dir / "conf.json")
        self.paths = ApplicationPaths(self.base_dir, self.config)
        self.paths.create()
        self.ui = TerminalUI(self.config.theme)
        self.clock = Clock(
            self.config.get(
                "settings",
                "timezone",
                default="Asia/Makassar",
            ),
            self.config.get(
                "events",
                "format",
                "timestamp_time",
                default="%H:%M",
            ),
            self.config.get(
                "events",
                "format",
                "timestamp_date",
                default="%d/%m/%y",
            ),
        )
        self.session = SessionTracker(
            JsonStore(self.paths.session, {}),
            self.clock,
        )
        self.credentials = CredentialStore(self.paths.account)

    def run(self, argv):
        arguments = ArgumentParser(self.paths.account.name).parse(argv)
        token = arguments.token
        if not token:
            token = self.credentials.select(arguments.select)
        if not token:
            self.ui.print(
                "[e]No token found in {}.[/e]".format(self.paths.account.name)
            )
            return
        asyncio.run(self._run_client(token))

    async def _run_client(self, token):
        client = DiscordTerminalClient(
            self.config,
            self.paths,
            self.ui,
            self.clock,
            self.session,
        )
        handlers = [
            GeneralCommands(client, self.config, self.ui),
            QuickGoCommands(client, self.config, self.ui),
            NavigationCommands(client, self.config, self.ui),
            VoiceCommands(client, self.config, self.ui),
            MediaCommands(client, self.config, self.ui),
            BookmarkCommands(client, self.config, self.ui),
            NotificationCommands(client, self.config, self.ui),
            MessageCommands(client, self.config, self.ui),
        ]
        runner = CliRunner(client, self.config, self.ui, handlers)
        try:
            await asyncio.gather(
                client.start(token),
                runner.run(),
            )
        except ValueError as error:
            self.ui.print(
                "[e]ERROR: {}\nHave you set up your {} properly?[/e]".format(
                    error,
                    self.paths.account.name,
                )
            )
