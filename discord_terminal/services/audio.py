import os
import threading

from playsound3 import playsound


class AudioService:
    def __init__(self, ringtone_dir, config, ui):
        self.ringtone_dir = ringtone_dir
        self.config = config
        self.ui = ui

    def play_for_message(self, message):
        if not self.config.get(
            "settings",
            "notification_sounds",
            "enabled",
            default=True,
        ):
            return
        ringtone = self._ringtone_for(message)
        if ringtone:
            self.play(ringtone)

    def play(self, ringtone_name=None):
        threading.Thread(
            target=self._play,
            args=(ringtone_name,),
            daemon=True,
        ).start()

    def _ringtone_for(self, message):
        sounds = self.config.get(
            "settings",
            "notification_sounds",
            default={},
        )
        channels = sounds.get("channels", {})
        channel = message.channel
        keys = [
            str(getattr(channel, "id", "")),
            getattr(channel, "name", ""),
        ]
        recipient = getattr(channel, "recipient", None)
        if recipient:
            keys.append("dm:{}".format(recipient.id))
            keys.append("dm:{}".format(recipient.name))
        for key in keys:
            if key and key in channels:
                return channels[key]
        if getattr(message, "guild", None) is None:
            return sounds.get("dm", sounds.get("default", "notification"))
        return sounds.get("default", "notification")

    def _play(self, ringtone_name):
        if not self.ringtone_dir.exists():
            self.ui.print("[e]Ringtone folder not found.[/e]")
            return
        files = [
            name
            for name in os.listdir(self.ringtone_dir)
            if name.lower().endswith((".mp3", ".wav"))
        ]
        if not files:
            return
        if ringtone_name:
            candidates = [
                name
                for name in files
                if name == ringtone_name
                or name.startswith(ringtone_name + ".")
                or name.startswith(ringtone_name)
            ]
            sound_file = candidates[0] if candidates else None
        else:
            sound_file = files[0]
        if sound_file:
            playsound(str(self.ringtone_dir / sound_file))
