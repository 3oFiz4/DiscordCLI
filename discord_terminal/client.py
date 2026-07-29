import discord

from discord_terminal.services.audio import AudioService
from discord_terminal.services.bookmarks import BookmarkService
from discord_terminal.services.images import ImagePreviewService
from discord_terminal.services.notifications import NotificationService
from discord_terminal.services.uploads import UploadService
from discord_terminal.storage import RecordStore
from discord_terminal.ui.file_picker import FilePicker
from discord_terminal.ui.renderer import HistoryRenderer


class DiscordTerminalClient(discord.Client):
    def __init__(self, config, paths, ui, clock, session):
        super().__init__()
        self.config = config
        self.paths = paths
        self.ui = ui
        self.clock = clock
        self.session = session
        self.current_channel = None
        self.current_guild = None
        self.history_buffer = []
        self.history_offset = 0
        self.input_session = None
        self.blocked_users = set()
        self.ignored_users = set()
        self.snippets = {
            "whoami": lambda: self.format_author(self.user) if self.user else "unknown"
        }
        self.uploads = UploadService(paths.upload, FilePicker())
        self.audio = AudioService(paths.ringtone, config, ui)
        self.image_previewer = ImagePreviewService(paths.preview, ui)
        self.bookmarks = BookmarkService(
            RecordStore(paths.bookmarks, "bookmarks")
        )
        self.notifications = NotificationService(
            self,
            config,
            RecordStore(paths.notifications, "notifications"),
            session,
            self.audio,
            ui,
        )
        self.renderer = HistoryRenderer(self, config, ui, clock)

    async def on_ready(self):
        self.ui.print(
            self.config.get("events", "onReady", default="{user}").format(
                user=self.user
            )
        )
        self.notifications.start_scan()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if self.notifications.record_live(message):
            self.ui.print(
                self.config.get("events", "onMessage", default="PING").format(
                    author=message.author,
                    channel=message.channel,
                )
            )
        if (
            self.current_channel
            and message.channel.id == self.current_channel.id
        ):
            await self.refresh_history(live=True)

    def format_author(self, member):
        user_id = getattr(member, "id", "?")
        username = getattr(member, "name", None) or "[id:{}]".format(user_id)
        nickname = None
        guild = getattr(member, "guild", None)
        if guild:
            guild_member = guild.get_member(user_id)
            if guild_member:
                nickname = getattr(guild_member, "nick", None)
        global_name = getattr(member, "global_name", None)
        display_name = nickname or global_name or username
        show_displayname = self.config.get(
            "settings",
            "show_displayname",
            default=True,
        )
        show_username = self.config.get(
            "settings",
            "show_username",
            default=True,
        )
        if not show_displayname:
            return username
        if not show_username:
            return display_name
        if display_name != username:
            return self.config.get(
                "events",
                "format",
                "author",
                default="{display_name} ({name})",
            ).format(display_name=display_name, name=username)
        return username

    def message_at(self, display_index):
        if display_index < 1 or display_index > len(self.history_buffer):
            raise IndexError
        return self.history_buffer[len(self.history_buffer) - display_index]

    def scroll_older(self):
        window_size = self.config.get(
            "events",
            "history_render",
            "message_total",
            default=30,
        )
        maximum = max(0, (len(self.history_buffer) - 1) // window_size)
        self.history_offset = min(maximum, self.history_offset + 1)

    def scroll_newer(self):
        self.history_offset = max(0, self.history_offset - 1)

    async def refresh_history(self, live=False, around_id=None):
        if not self.current_channel:
            return
        if around_id:
            messages = [
                message
                async for message in self.current_channel.history(
                    limit=100,
                    around=discord.Object(id=int(around_id)),
                )
            ]
        else:
            messages = [
                message
                async for message in self.current_channel.history(limit=100)
            ]
        self.history_buffer = sorted(
            messages,
            key=lambda message: message.created_at,
        )
        self.history_offset = 0
        await self.render_history(live=live)

    async def render_history(self, live=False):
        await self.renderer.render(live=live)

    async def send_message(self, content):
        if not self.current_channel:
            self.ui.print(
                self.config.log("message_send", "no_channel_selected")
            )
            return
        try:
            await self.current_channel.send(
                content,
                files=self.uploads.discord_files(),
            )
            self.uploads.consume()
            await self.refresh_history()
        except Exception as error:
            self.ui.print(
                self.config.log("message_send", "fail").format(
                    error_msg=str(error)
                )
            )

    async def go_to_record(self, record):
        channel_id = int(record["channel_id"])
        channel = self.get_channel(channel_id)
        if channel is None:
            channel = next(
                (
                    item
                    for item in self.private_channels
                    if item.id == channel_id
                ),
                None,
            )
        if channel is None:
            try:
                channel = await self.fetch_channel(channel_id)
            except Exception:
                channel = None
        if channel is None:
            self.ui.print("[e]Channel is unavailable.[/e]")
            return
        self.current_channel = channel
        self.current_guild = getattr(channel, "guild", None)
        await self.refresh_history(around_id=record["message_id"])
