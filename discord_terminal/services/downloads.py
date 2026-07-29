from pathlib import Path


class DownloadService:
    def __init__(self, download_dir):
        self.download_dir = download_dir

    async def save(self, attachment):
        path = self._available_path(Path(attachment.filename).name)
        await attachment.save(path)
        return path

    def _available_path(self, filename):
        path = self.download_dir / filename
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        number = 1
        while True:
            candidate = self.download_dir / "{} ({}){}".format(
                stem,
                number,
                suffix,
            )
            if not candidate.exists():
                return candidate
            number += 1
