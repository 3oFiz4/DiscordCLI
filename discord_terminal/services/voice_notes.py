import array
import asyncio
import base64
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import discord
from discord.http import Route

from discord_terminal.services.recorder import VoiceRecorder


class VoiceNoteService:
    def __init__(self, client, voice_dir, recorder=None):
        self.client = client
        self.voice_dir = voice_dir
        if recorder and hasattr(recorder, "record"):
            self.recorder = recorder
        else:
            self.recorder = VoiceRecorder(voice_dir, client.ui)

    async def send(self, channel, source=""):
        recorded = not source
        if source:
            source_path = self._source(source)
        else:
            source_path = await asyncio.to_thread(self.recorder.record)
        output_path = self.voice_dir / "{}.ogg".format(uuid.uuid4().hex)
        try:
            await asyncio.to_thread(self._convert, source_path, output_path)
            duration = await asyncio.to_thread(self._duration, output_path)
            waveform = await asyncio.to_thread(self._waveform, output_path)
            attachment = await self._upload(channel, output_path)
            attachment["duration_secs"] = duration
            attachment["waveform"] = waveform
            payload = {
                "tts": False,
                "flags": 8192,
                "attachments": [attachment],
                "nonce": str(time.time_ns()),
            }
            route = Route(
                "POST",
                "/channels/{channel_id}/messages",
                channel_id=channel.id,
            )
            await self.client._connection.http.request(route, json=payload)
        finally:
            output_path.unlink(missing_ok=True)
        if recorded:
            return source_path
        return None

    def _source(self, source):
        path = Path(source.strip().strip('"')).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError("Audio file does not exist: {}".format(path))
        return path

    def _tools(self):
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise RuntimeError("ffmpeg and ffprobe must be available in PATH.")
        return ffmpeg, ffprobe

    def _convert(self, source, destination):
        ffmpeg, unused = self._tools()
        result = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-i",
                str(source),
                "-vn",
                "-c:a",
                "libopus",
                "-b:a",
                "64k",
                str(destination),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Audio conversion failed.")

    def _duration(self, path):
        unused, ffprobe = self._tools()
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Duration scan failed.")
        return max(0.01, float(result.stdout.strip()))

    def _waveform(self, path):
        ffmpeg, unused = self._tools()
        result = subprocess.run(
            [
                ffmpeg,
                "-v",
                "error",
                "-i",
                str(path),
                "-f",
                "s16le",
                "-ac",
                "1",
                "-ar",
                "8000",
                "pipe:1",
            ],
            capture_output=True,
        )
        if result.returncode:
            raise RuntimeError(
                result.stderr.decode("utf-8", errors="replace").strip()
                or "Waveform scan failed."
            )
        samples = array.array("h")
        samples.frombytes(result.stdout)
        if sys.byteorder != "little":
            samples.byteswap()
        if not samples:
            values = bytes([0] * 256)
            return base64.b64encode(values).decode("ascii")
        peaks = []
        for index in range(256):
            start = index * len(samples) // 256
            end = max(start + 1, (index + 1) * len(samples) // 256)
            end = min(end, len(samples))
            segment = samples[start:end]
            peaks.append(max((abs(value) for value in segment), default=0))
        maximum = max(peaks) or 1
        values = bytes(
            min(255, round(peak * 255 / maximum))
            for peak in peaks
        )
        return base64.b64encode(values).decode("ascii")

    async def _upload(self, channel, path):
        file = discord.File(path, filename="voice-message.ogg")
        try:
            uploaded = await channel.upload_files(file)
        finally:
            file.close()
        if not uploaded:
            raise RuntimeError("Discord did not return the uploaded audio.")
        return uploaded[0].to_dict(0)
