import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from discord_terminal.commands.base import CommandHandler


class MediaCommands(CommandHandler):
    async def handle(self, text):
        if self.matches(text, "voice_note"):
            await self._voice_note(text)
            return True
        if self.matches(text, "image_preview"):
            await self._preview(text)
            return True
        if self.matches(text, "download_attachment"):
            await self._download(text)
            return True
        if self.matches(text, "open_attachment"):
            await self._open(text)
            return True
        if self.matches(text, "upload_stage", exact=True):
            self._stage()
            return True
        if self.matches(text, "deupload_stage", exact=True):
            self.client.uploads.reset()
            self.log("deupload_stage", "reset")
            return True
        return False

    async def _preview(self, text):
        parts = self.arguments(text, "image_preview").split()
        if (
            len(parts) != 2
            or not parts[0].isdigit()
            or not (
                parts[1].isdigit()
                or (
                    parts[1].lower().startswith("s")
                    and parts[1][1:].isdigit()
                )
            )
        ):
            self.log("image_preview", "usage")
            return
        try:
            message = self.client.message_at(int(parts[0]))
            if parts[1].lower().startswith("s"):
                sticker_index = int(parts[1][1:])
                stickers = getattr(message, "stickers", [])
                if sticker_index < 1 or sticker_index > len(stickers):
                    raise IndexError
                action = await self.client.image_previewer.preview_sticker(
                    stickers[sticker_index - 1]
                )
            else:
                image_index = int(parts[1])
                if image_index < 1 or image_index > len(message.attachments):
                    raise IndexError
                action = await self.client.image_previewer.preview(
                    message.attachments[image_index - 1]
                )
            if action == "-<":
                self.client.scroll_older()
            elif action == "->":
                self.client.scroll_newer()
            await self.client.render_history()
        except IndexError:
            self.log("image_preview", "out_of_range")
        except Exception as error:
            self.log("image_preview", "error", error_msg=str(error))

    async def _voice_note(self, text):
        if not self.client.current_channel:
            self.log("voice_note", "no_channel")
            return
        source = self.arguments(text, "voice_note").strip()
        try:
            await self.client.voice_notes.send(
                self.client.current_channel,
                source,
            )
            self.log("voice_note", "sent")
            await self.client.refresh_history()
        except Exception as error:
            self.log("voice_note", "error", error_msg=str(error))

    async def _download(self, text):
        parts = self.arguments(text, "download_attachment").split()
        if not parts or not parts[0].isdigit():
            self.log("download_attachment", "usage")
            return
        try:
            message = self.client.message_at(int(parts[0]))
        except Exception:
            self.log("download_attachment", "message_out_of_range")
            return
        if not message.attachments:
            self.log("download_attachment", "no_attachments")
            return
        indices = [
            int(value)
            for value in parts[1:]
            if value.isdigit()
        ] or list(range(1, len(message.attachments) + 1))
        for index in indices:
            if index < 1 or index > len(message.attachments):
                self.log(
                    "download_attachment",
                    "attachment_out_of_range",
                    index=index,
                )
                continue
            try:
                path = await self.client.downloads.save(
                    message.attachments[index - 1]
                )
                self.log(
                    "download_attachment",
                    "saved",
                    path=str(path),
                )
            except Exception as error:
                self.log(
                    "download_attachment",
                    "error",
                    error_msg=str(error),
                )

    async def _open(self, text):
        parts = self.arguments(text, "open_attachment").split()
        if not parts:
            self.log(
                "open_attachment",
                "usage",
                cmdK=self.config.command_key,
            )
            return
        if not parts[0].isdigit():
            self.log("open_attachment", "invalid_msg_index")
            return
        try:
            message = self.client.message_at(int(parts[0]))
        except Exception:
            self.log("open_attachment", "msg_index_out_of_range")
            return
        if not message.attachments:
            self.log("open_attachment", "no_attachments")
            return
        indices = [
            int(value)
            for value in parts[1:]
            if value.isdigit()
        ] or list(range(1, len(message.attachments) + 1))
        for index in indices:
            if index < 1 or index > len(message.attachments):
                self.log(
                    "open_attachment",
                    "attachment_index_out_of_range",
                    index=index,
                )
                continue
            await self._open_attachment(message.attachments[index - 1])

    async def _open_attachment(self, attachment):
        path = self.client.paths.upload / Path(attachment.filename).name
        try:
            await attachment.save(path)
        except Exception as error:
            self.log(
                "open_attachment",
                "error_saving",
                error_msg=str(error),
            )
            return
        lower = attachment.filename.lower()
        if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            webbrowser.open(path.as_uri())
            self.log(
                "open_attachment",
                "opened_image",
                filename=attachment.filename,
            )
            return
        if lower.endswith((".txt", ".md", ".py", ".js", ".json")):
            try:
                if os.name == "nt":
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(path)])
                else:
                    subprocess.Popen(["xdg-open", str(path)])
                self.log(
                    "open_attachment",
                    "opened_text",
                    filename=attachment.filename,
                )
            except Exception as error:
                self.log(
                    "open_attachment",
                    "error_opening_file",
                    error_msg=str(error),
                )
            return
        self.log(
            "open_attachment",
            "no_open_command",
            filename=attachment.filename,
        )

    def _stage(self):
        paths = self.client.uploads.stage()
        if not paths:
            self.log("upload_stage", "null")
            return
        for path in paths:
            self.log("upload_stage", "staged", filename=path.name)
