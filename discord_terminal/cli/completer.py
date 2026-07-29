import emoji
from prompt_toolkit.completion import Completer, Completion


class DiscordCompleter(Completer):
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.emoji_aliases = self._emoji_aliases()

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()

        if self._matches_prefix(text, "quick_go"):
            yield from self._complete_quick_go(text)
            return
        if self._matches_prefix(text, "server_nav"):
            yield from self._complete_guild(text)
            return
        if self._matches_prefix(text, "channel_nav"):
            yield from self._complete_channel(text)
            return
        if any(
            text.startswith(
                "{}{} ".format(self.config.command_key, alias)
            )
            for alias in self.config.aliases("dm_nav")
        ):
            yield from self._complete_dm(text)
            return
        if self._matches_prefix(text, "forward_msg"):
            yield from self._complete_forward(text)
            return
        if self._matches_prefix(text, "edit"):
            yield from self._complete_edit(text)
            return
        if self._matches_prefix(text, "voice_join"):
            yield from self._complete_voice(text)
            return

        if text.startswith(":"):
            prefix = text[1:]
            for emoji_code in self.emoji_aliases:
                core = emoji_code.strip(":")
                if core.lower().startswith(prefix.lower()):
                    character = emoji.emojize(
                        emoji_code,
                        language="alias",
                        variant="emoji_type",
                    )
                    yield Completion(
                        emoji_code,
                        display="{} {}".format(character, emoji_code),
                        start_position=-len(prefix) - 1,
                    )
            return

        if "@" in text.split(" ")[-1] and self.client.current_guild:
            partial = text.split(" ")[-1].split("@")[-1]
            for user in self.client.current_guild.members:
                if user.name.lower().startswith(partial.lower()):
                    yield Completion(user.name, start_position=-len(partial))
            return

        tokens = text.split()
        if tokens:
            last = tokens[-1]
            if "{" in last and "}" not in last:
                start = last.find("{") + 1
                prefix = last[start:]
                for key in self.client.snippets:
                    if key.startswith(prefix):
                        yield Completion(
                            "{}}}".format(key),
                            start_position=-len(prefix) - 1,
                        )

    def _complete_guild(self, text):
        prefix = self._prefix("server_nav")
        partial = text[len(prefix):]
        for guild in self.client.guilds:
            if guild.name.lower().startswith(partial.lower()):
                yield Completion(guild.name, start_position=-len(partial))

    def _complete_quick_go(self, text):
        prefix = self._matched_prefix(text, "quick_go")
        partial = text[len(prefix):]
        for entry in self.client.quick_go.search(partial):
            yield Completion(
                entry["label"],
                display=entry["label"],
                start_position=-len(partial),
            )

    def _complete_channel(self, text):
        prefix = self._prefix("channel_nav")
        if not self.client.current_guild:
            return
        partial = text[len(prefix):]
        for channel in self.client.current_guild.text_channels:
            if channel.name.lower().startswith(partial.lower()):
                yield Completion(channel.name, start_position=-len(partial))

    def _complete_dm(self, text):
        prefixes = [
            "{}{} ".format(self.config.command_key, alias)
            for alias in self.config.aliases("dm_nav")
        ]
        matched = next((prefix for prefix in prefixes if text.startswith(prefix)), None)
        partial = text[len(matched):]
        for user in self.client.users:
            if user.name.lower().startswith(partial.lower()):
                display_name = getattr(user, "display_name", user.name)
                yield Completion(
                    user.name,
                    display="{} ({})".format(display_name, user.name),
                    start_position=-len(partial),
                )

    def _complete_forward(self, text):
        prefix = self._prefix("forward_msg")
        parts = text.split(" ", 2)
        if len(parts) < 3:
            return
        partial = parts[-1]
        for user in self.client.users:
            if user.name.lower().startswith(partial.lower()):
                display_name = getattr(user, "display_name", user.name)
                yield Completion(
                    user.name,
                    display="{} ({})".format(display_name, user.name),
                    start_position=-len(partial),
                )

    def _complete_edit(self, text):
        prefix = self._prefix("edit")
        remaining = text[len(prefix):].lstrip()
        parts = remaining.split(" ", 1)
        if parts and parts[0].isdigit():
            try:
                message = self.client.message_at(int(parts[0]))
                original = message.content
            except Exception:
                original = ""
            if len(parts) == 1 or parts[1] == "":
                yield Completion(original, start_position=0, display=original)

    def _complete_voice(self, text):
        prefix = self._matched_prefix(text, "voice_join")
        partial = text[len(prefix):]
        for channel in self.client.voice.channels():
            if partial.lower() in channel.name.lower():
                yield Completion(
                    channel.name,
                    start_position=-len(partial),
                )

    def _prefix(self, command_name):
        aliases = self.config.aliases(command_name)
        if not aliases:
            return ""
        return "{}{} ".format(self.config.command_key, aliases[0])

    def _matches_prefix(self, text, command_name):
        return any(
            text.startswith(
                "{}{} ".format(self.config.command_key, alias)
            )
            for alias in self.config.aliases(command_name)
        )

    def _matched_prefix(self, text, command_name):
        return next(
            (
                "{}{} ".format(self.config.command_key, alias)
                for alias in self.config.aliases(command_name)
                if text.startswith(
                    "{}{} ".format(self.config.command_key, alias)
                )
            ),
            "",
        )

    def _emoji_aliases(self):
        if not hasattr(emoji, "EMOJI_DATA"):
            return sorted(emoji.EMOJI_ALIAS_UNICODE_ENGLISH.keys())
        aliases = []
        for data in emoji.EMOJI_DATA.values():
            aliases.extend(data.get("alias", []))
        return sorted(set(aliases))
