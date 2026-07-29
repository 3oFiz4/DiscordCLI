from prompt_toolkit.document import Document
from rich.markup import escape


class HistoryRenderer:
    def __init__(self, client, config, ui, clock):
        self.client = client
        self.config = config
        self.ui = ui
        self.clock = clock

    async def render(self, live=False):
        current_input = ""
        if self.client.input_session:
            current_input = self.client.input_session.default_buffer.text

        total = len(self.client.history_buffer)
        window_size = self.config.get(
            "events",
            "history_render",
            "message_total",
            default=30,
        )
        end_index = total - self.client.history_offset * window_size
        end_index = max(0, min(total, end_index))
        start_index = max(0, end_index - window_size)

        self.ui.clear()
        self._render_header(start_index, end_index, total)

        for global_index in range(start_index, end_index):
            message = self.client.history_buffer[global_index]
            display_index = total - global_index
            if self._render_hidden(message, display_index):
                continue
            self._render_message(message, display_index, total)

        if self.client.input_session:
            self.client.input_session.default_buffer.set_document(
                Document(current_input, cursor_position=len(current_input)),
                bypass_readonly=True,
            )

    def _render_header(self, start_index, end_index, total):
        guild = self.client.current_guild or "DM"
        channel = self.client.current_channel or "None"
        template = self.config.get(
            "events",
            "history_render",
            "header",
            default="[@{current_guild} #{current_channel} | {start_index}-{end_index}/{total}]",
        )
        self.ui.print(
            template.format(
                current_guild=escape(str(guild)),
                current_channel=escape(str(channel)),
                start_index=start_index + 1 if total else 0,
                end_index=end_index,
                total=total,
            )
        )

    def _render_hidden(self, message, display_index):
        blocked = message.author.id in getattr(self.client, "blocked_users", set())
        ignored = message.author.id in getattr(self.client, "ignored_users", set())
        if not blocked and not ignored:
            return False
        status = "Blocked" if blocked else "Ignored"
        author = escape(self.client.format_author(message.author))
        self.ui.print(
            "<{}> --- {} User: {} (message hidden)".format(
                display_index,
                status,
                author,
            )
        )
        return True

    def _render_message(self, message, display_index, total):
        timestamp = "[time]{}[/time]".format(self.clock.display(message.created_at))
        author = self._formatted_author(message.author)
        reply_index, reply_to_self = self._reply_data(message, total)
        history_config = self.config.get("events", "history_render", default={})

        if reply_index is None:
            template = history_config.get(
                "message_header",
                "<{index} {timestamp} {author}>",
            )
            header = template.format(
                index=display_index,
                timestamp=timestamp,
                author=author,
            )
        else:
            key = "message_header_reply_to_self" if reply_to_self else "message_header_reply"
            template = history_config.get(
                key,
                "<{index}@{replied_index} {timestamp} {author}>",
            )
            indicator = history_config.get("reply_to_self_indicator", "REPLY TO YOU")
            header = template.format(
                index=display_index,
                replied_index=reply_index,
                timestamp=timestamp,
                author=author,
                indicator=indicator,
            )

        content = escape(message.content or "")
        if "\n" in message.content:
            self.ui.print(header)
            self.ui.rule()
            self.ui.print(content)
            self.ui.rule()
        else:
            self.ui.print("{} {}".format(header, content))

        if message.attachments:
            attachments = " ".join(
                "[{}] {}".format(index + 1, escape(attachment.filename))
                for index, attachment in enumerate(message.attachments)
            )
            template = history_config.get("attachment", "[attachment]| {attaches}[/attachment]")
            self.ui.print(template.format(attaches=attachments))

        if message.reactions:
            reactions = " ".join(
                "{}×{}".format(reaction.emoji, reaction.count)
                for reaction in message.reactions
            )
            self.ui.print("     {}".format(escape(reactions)))

    def _formatted_author(self, member):
        name = escape(self.client.format_author(member))
        if self.config.get(
            "settings",
            "role_based_username_color",
            default=False,
        ):
            role_color = self._role_color(member)
            if role_color:
                return "[{}]{}[/]".format(role_color, name)
        style = "self" if member.id == self.client.user.id else "other"
        return "[{}]{}[/{}]".format(style, name, style)

    def _role_color(self, member):
        color = getattr(member, "color", None)
        value = getattr(color, "value", 0)
        if not value:
            roles = getattr(member, "roles", [])
            for role in reversed(roles):
                role_color = getattr(role, "color", None)
                value = getattr(role_color, "value", 0)
                if value:
                    break
        if not value:
            return None
        return "#{:06x}".format(value)

    def _reply_data(self, message, total):
        reference = getattr(message, "reference", None)
        message_id = getattr(reference, "message_id", None)
        if not message_id:
            return None, False

        target = getattr(reference, "resolved", None)
        reply_index = "?"
        for index, buffered in enumerate(self.client.history_buffer):
            if buffered.id == message_id:
                reply_index = total - index
                target = buffered
                break

        reply_to_self = bool(
            target
            and getattr(target, "author", None)
            and target.author.id == self.client.user.id
            and message.author.id != self.client.user.id
        )
        return reply_index, reply_to_self
