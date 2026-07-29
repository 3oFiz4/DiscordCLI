import importlib
from importlib import metadata


class NativeVoiceLoader:
    def __init__(self):
        self.module = None
        self.error = ""
        self.versions = {}

    def load(self):
        self.versions = {
            "discord-native-voice": self._version("discord-native-voice"),
            "discord.py-self": self._version("discord.py-self"),
        }
        try:
            module = importlib.import_module("discord.ext.native_voice")
            required = (
                "AudioFrameSource",
                "BasicSink",
                "PCMDecodeSink",
                "VoiceClient",
            )
            missing = [
                name
                for name in required
                if not hasattr(module, name)
            ]
            if missing:
                raise AttributeError(
                    "missing API: {}".format(", ".join(missing))
                )
            self.module = module
            self.error = ""
        except Exception as error:
            self.module = None
            self.error = "{}: {}".format(type(error).__name__, error)
        return self.module

    def diagnostic(self):
        packages = ", ".join(
            "{} {}".format(name, version)
            for name, version in self.versions.items()
        )
        if self.error:
            return "{}; {}".format(self.error, packages)
        return packages

    def _version(self, distribution):
        try:
            return metadata.version(distribution)
        except metadata.PackageNotFoundError:
            return "not installed"
