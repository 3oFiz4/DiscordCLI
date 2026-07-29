import shutil

import discord


class UploadService:
    def __init__(self, upload_dir, file_picker):
        self.upload_dir = upload_dir
        self.file_picker = file_picker
        self.staged = []

    def stage(self):
        picked = self.file_picker.pick()
        if not picked:
            return []
        self.reset()
        for path in picked:
            destination = self.upload_dir / path.name
            shutil.copy2(path, destination)
            self.staged.append(destination)
        return list(self.staged)

    def reset(self):
        self.staged.clear()
        shutil.rmtree(self.upload_dir, ignore_errors=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def discord_files(self):
        if not self.staged:
            return None
        return [discord.File(path) for path in self.staged]

    def consume(self):
        self.staged.clear()
