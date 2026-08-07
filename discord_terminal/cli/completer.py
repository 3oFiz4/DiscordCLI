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

        words = text.split(" ")
        if words:
            last_word = words[-1]
            if last_word.startswith(":") and not (len(last_word) > 1 and last_word.endswith(":") and last_word.count(":") >= 2):
                prefix = last_word[1:]
                for emoji_code in self.emoji_aliases:
                    core = emoji_code.strip(":")
                    if core.lower().startswith(prefix.lower()):
                        try:
                            character = emoji.emojize(
                                emoji_code,
                                language="alias",
                            )
                        except Exception:
                            character = ""
                        display = "{} {}".format(character, emoji_code).strip()
                        yield Completion(
                            emoji_code,
                            display=display,
                            start_position=-len(prefix) - 1,
                        )

                if hasattr(self.client, "get_available_custom_emojis"):
                    is_v_command = self._matches_prefix(text, "image_preview")
                    custom_emojis = self.client.get_available_custom_emojis()
                    for c_emoji in custom_emojis:
                        c_name = getattr(c_emoji, "name", "")
                        if c_name.lower().startswith(prefix.lower()):
                            if is_v_command:
                                plain_code = f":{c_name}:"
                                yield Completion(
                                    plain_code,
                                    display=plain_code,
                                    start_position=-len(prefix) - 1,
                                )
                            else:
                                tag = "a" if getattr(c_emoji, "animated", False) else ""
                                template = f"<{tag}:{c_name}:{c_emoji.id}>"
                                display = f":{c_name}: ({template})"
                                yield Completion(
                                    template,
                                    display=display,
                                    start_position=-len(prefix) - 1,
                                )
                return




        last_word = text.split(" ")[-1]
        if "@" in last_word:
            partial = last_word.split("@")[-1]
            members = self._get_mentionable_members()
            for user in members:
                name = getattr(user, "name", "")
                display_name = getattr(user, "display_name", name)
                nick = getattr(user, "nick", None)
                matches_name = name.lower().startswith(partial.lower())
                matches_display = display_name.lower().startswith(partial.lower())
                matches_nick = nick and nick.lower().startswith(partial.lower())
                if matches_name or matches_display or matches_nick:
                    display = f"{display_name} (@{name})" if display_name != name else f"@{name}"
                    yield Completion(
                        f"<@{user.id}>",
                        display=display,
                        start_position=-len(partial) - 1,
                    )
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
        for alias in self.config.aliases(command_name):
            prefixes = [self.config.command_key]
            if self.config.command_key != "/":
                prefixes.append("/")
            for prefix in prefixes:
                pfx = "{}{} ".format(prefix, alias)
                if text.startswith(pfx):
                    return True
        return False


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

    def _get_mentionable_members(self):
        if self.client.current_guild:
            return self.client.current_guild.members
        channel = self.client.current_channel
        if not channel:
            return []
        members = []
        if hasattr(channel, "recipients") and channel.recipients:
            members.extend(channel.recipients)
        elif hasattr(channel, "recipient") and channel.recipient:
            members.append(channel.recipient)
        return [m for m in members if m]

