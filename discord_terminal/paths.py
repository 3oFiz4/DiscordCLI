from pathlib import Path


class ApplicationPaths:
    def __init__(self, base_dir, config):
        self.base = Path(base_dir)
        self.upload = self.base / config.get("folders", "upload", default="upload")
        self.ringtone = self.base / config.get("folders", "ringtone", default="ringtone")
        self.data = self.base / config.get("folders", "data", default="data")
        self.preview = self.data / "preview"
        self.account = self.base / config.get("file", "account", default="token.txt")
        self.session = self.data / "session.json"
        self.notifications = self.data / "notifications.json"
        self.bookmarks = self.data / "bookmarks.json"

    def create(self):
        self.upload.mkdir(parents=True, exist_ok=True)
        self.ringtone.mkdir(parents=True, exist_ok=True)
        self.data.mkdir(parents=True, exist_ok=True)
        self.preview.mkdir(parents=True, exist_ok=True)
