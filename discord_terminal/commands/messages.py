import clipboard
import discord
import emoji
from prompt_toolkit.document import Document

from discord_terminal.commands.base import CommandHandler


class MessageCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "reply"):
            await self._reply(text)
            return True
        if self.matches(text, "delete_msg"):
            await self._delete(text)
            return True
        if self.matches(text, "forward_msg"):
            await self._forward(text)
            return True
        if self.matches(text, "edit"):
            await self._edit(text)
            return True
        if self.matches(text, "copy"):
            await self._copy(text)
            return True
        if self.matches(text, "pin"):
            await self._pin(text, False)
            return True
        if self.matches(text, "unpin"):
            await self._pin(text, True)
            return True
        if self.matches(text, "react"):
            await self._react(text)
            return True
        return False

    async def _reply(self, text):
        parts = self.arguments(text, "reply").split(" ", 1)
        if len(parts) < 2 or not parts[0].isdigit():
            self.log(
                "reply",
                "error",
                error_msg="Missing message number or content",
            )
            return
        try:
            target = self.client.message_at(int(parts[0]))
            await target.reply(
                parts[1],
                files=self.client.uploads.discord_files(),
            )
            self.client.uploads.consume()
        except Exception as error:
            self.log("reply", "error", error_msg=str(error))
        await self.client.refresh_history()

    async def _delete(self, text):
        for index_text in self.arguments(text, "delete_msg").split():
            try:
                index = int(index_text)
                message = self.client.message_at(index)
                if message.author.id != self.client.user.id:
                    self.log("delete_msg", "not_own_message")
                else:
                    await message.delete()
            except ValueError:
                self.log("delete_msg", "invalid_index", index=index_text)
            except IndexError:
                self.log("delete_msg", "out_of_range", index=index_text)
            except Exception as error:
                self.log(
                    "delete_msg",
                    "generic_error",
                    index_str=index_text,
                    error_msg=str(error),
                )
        await self.client.refresh_history()

    async def _forward(self, text):
        parts = self.arguments(text, "forward_msg").split(" ", 1)
        if len(parts) < 2:
            self.log("forward_msg", "usage_error")
            return
        if not parts[0].isdigit():
            self.log("forward_msg", "invalid_msg_num")
            return
        user_name = parts[1].strip()
        if not user_name:
            self.log("forward_msg", "user_not_specified")
            return
        user = discord.utils.get(self.client.users, name=user_name)
        if not user:
            self.log("forward_msg", "no_such_user", user_arg=user_name)
            return
        try:
            message = self.client.message_at(int(parts[0]))
            dm = await user.create_dm()
            await dm.send(message.content)
        except Exception as error:
            self.log(
                "forward_msg",
                "generic_error",
                error_msg=str(error),
            )

    async def _edit(self, text):
        parts = self.arguments(text, "edit").split(" ", 1)
        if not parts or not parts[0].isdigit():
            self.log("edit", "error", error_msg="Invalid message index.")
            return
        index = int(parts[0])
        try:
            target = self.client.message_at(index)
        except Exception:
            self.log("edit", "error", error_msg="Message index not found.")
            return
        if len(parts) == 1 or not parts[1].strip():
            alias = self.config.aliases("edit")[0]
            command = "{}{} {} {}".format(
                self.config.command_key,
                alias,
                index,
                target.content,
            )
            self.client.input_session.default_buffer.set_document(
                Document(command, cursor_position=len(command)),
                bypass_readonly=True,
            )
            return
        try:
            await target.edit(content=parts[1])
        except Exception as error:
            self.log("edit", "error", error_msg=str(error))
        await self.client.refresh_history()

    async def _copy(self, text):
        value = self.arguments(text, "copy").split()
        if not value or not value[0].isdigit():
            self.log(
                "copy",
                "error",
                error_msg="Missing or invalid message index.",
            )
            return
        try:
            clipboard.copy(self.client.message_at(int(value[0])).content)
        except Exception as error:
            self.log("copy", "error", error_msg=str(error))

    async def _pin(self, text, unpin):
        command = "unpin" if unpin else "pin"
        value = self.arguments(text, command).split()
        if not value or not value[0].isdigit():
            self.log(
                command,
                "error",
                error_msg="Missing or invalid message index.",
            )
            return
        try:
            target = self.client.message_at(int(value[0]))
            if unpin:
                await target.unpin()
            else:
                await target.pin()
        except Exception as error:
            self.log(command, "error", error_msg=str(error))
        await self.client.refresh_history()

    async def _react(self, text):
        parts = self.arguments(text, "react").split(" ", 1)
        if len(parts) < 2 or not parts[0].isdigit():
            self.log("react", "invalidIndex")
            return
        value = emoji.emojize(
            parts[1].replace("::", ":"),
            language="alias",
        )
        try:
            await self.client.message_at(int(parts[0])).add_reaction(value)
            self.log("react", "success", emoji=value, idx=parts[0])
        except Exception as error:
            self.log("react", "error", e=str(error))
        await self.client.refresh_history()
