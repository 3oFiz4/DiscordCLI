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

    def _view(self, path):
        executable = shutil.which("chafa")
        if not executable:
            raise RuntimeError("chafa was not found in PATH.")
        while True:
            self.ui.clear_buffer()
            subprocess.run(
                [
                    executable,
                    "--format=iterm",
                    "--clear",
                    "--align=center",
                    "--animate=off",
                    str(path),
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
