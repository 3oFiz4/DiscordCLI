import shutil
import subprocess
import wave
from datetime import datetime


class VoiceRecorder:
    def __init__(self, voice_dir, ui):
        self.voice_dir = voice_dir
        self.ui = ui

    def record(self):
        try:
            import sounddevice
        except ImportError:
            raise RuntimeError(
                "sounddevice is required. Run: py -3 -m pip install sounddevice"
            )
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg must be available in PATH.")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        wave_path = self.voice_dir / "voice-note-{}.wav".format(stamp)
        mp3_path = self.voice_dir / "voice-note-{}.mp3".format(stamp)
        frames = []

        def capture(indata, frame_count, time_info, status):
            frames.append(bytes(indata))

        self.ui.print("[i]Recording voice note. Press Enter to stop.[/i]")
        try:
            with sounddevice.RawInputStream(
                samplerate=48000,
                channels=1,
                dtype="int16",
                blocksize=960,
                callback=capture,
            ):
                input()
            if not frames:
                raise RuntimeError("The microphone did not capture any audio.")
            with wave.open(str(wave_path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(48000)
                output.writeframes(b"".join(frames))
            result = subprocess.run(
                [
                    ffmpeg,
                    "-y",
                    "-i",
                    str(wave_path),
                    "-vn",
                    "-c:a",
                    "libmp3lame",
                    "-b:a",
                    "128k",
                    str(mp3_path),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise RuntimeError(
                    result.stderr.strip() or "MP3 conversion failed."
                )
            return mp3_path
        finally:
            wave_path.unlink(missing_ok=True)
