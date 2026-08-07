import asyncio
import shutil
import subprocess
from pathlib import Path


class ImagePreviewService:
    def __init__(self, preview_dir, ui):
        self.preview_dir = preview_dir
        self.ui = ui

    async def preview(self, attachment):
        if not self._is_image(attachment):
            raise ValueError("The selected attachment is not an image.")
        filename = "{}_{}".format(attachment.id, Path(attachment.filename).name)
        path = self.preview_dir / filename
        await attachment.save(path)
        return await asyncio.to_thread(self._view, path)

    async def preview_sticker(self, sticker):
        sticker_format = getattr(sticker, "format", None)
        extension = getattr(sticker_format, "file_extension", "png")
        if extension == "json":
            raise ValueError(
                "This is a Lottie sticker. Chafa cannot render Lottie JSON."
            )
        filename = "{}_{}.{}".format(
            sticker.id,
            Path(sticker.name).name,
            extension,
        )
        path = self.preview_dir / filename
        path.write_bytes(await sticker.read())
        return await asyncio.to_thread(self._view, path)

    async def preview_emoji(self, emoji):
        is_animated = getattr(emoji, "animated", False)
        extension = "gif" if is_animated else "png"
        filename = f"emoji_{emoji.id}_{emoji.name}.{extension}"
        path = self.preview_dir / filename

        if not path.exists():
            if hasattr(emoji, "save"):
                await emoji.save(path)
            elif hasattr(emoji, "read"):
                path.write_bytes(await emoji.read())
            elif hasattr(emoji, "url"):
                import urllib.request
                await asyncio.to_thread(urllib.request.urlretrieve, str(emoji.url), path)

        return await asyncio.to_thread(self._view, path)


    def _view(self, path):
        executable = shutil.which("chafa")
        if not executable:
            raise RuntimeError("chafa was not found in PATH.")
        while True:
            self.ui.clear_buffer()
            subprocess.run(
                [
                    executable,
                    str(path),
                    "--format=iterm",
                    "--align=center",
                ],
                check=False,
            )
            action = input(
                "\nEnter/r: redraw after resizing | -<: older | ->: newer | q: close\n> "
            ).strip()
            if action in ("", "r"):
                continue
            if action in ("-<", "->", "q"):
                return action

    def _is_image(self, attachment):
        content_type = getattr(attachment, "content_type", "") or ""
        if content_type.startswith("image/"):
            return True
        return attachment.filename.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".tiff")
        )
