import array
import queue
import sys
import threading
import time
from collections import deque

import discord


class MicrophoneFrames:
    def __init__(self):
        self.frames = queue.Queue(maxsize=8)
        self.active = True

    def put(self, frame):
        if not self.active:
            return
        try:
            self.frames.put_nowait(frame)
        except queue.Full:
            try:
                self.frames.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frames.put_nowait(frame)
            except queue.Full:
                pass

    def close(self):
        self.active = False
        try:
            self.frames.put_nowait(None)
        except queue.Full:
            try:
                self.frames.get_nowait()
            except queue.Empty:
                pass
            try:
                self.frames.put_nowait(None)
            except queue.Full:
                pass

    def __iter__(self):
        return self

    def __next__(self):
        frame = self.frames.get()
        if frame is None:
            raise StopIteration
        return frame


class MicrophoneSource(discord.AudioSource):
    def __init__(self, frames):
        self.frames = frames

    def read(self):
        try:
            return next(self.frames)
        except StopIteration:
            return b""

    def is_opus(self):
        return False

    def cleanup(self):
        self.frames.close()


class VoiceAudioBridge:
    def __init__(self, client):
        self.client = client
        self.voice_client = None
        self.input_stream = None
        self.output_stream = None
        self.microphone = None
        self.playback = {}
        self.speakers = {}
        self.lock = threading.Lock()
        self.active = False
        self.last_invalidate = 0
        self.speaker_timer = None
        self.mode = "disconnected"
        self.receive_enabled = False
        self.diagnostic = ""

    def start(self, voice_client, native_module=None, diagnostic=""):
        try:
            import sounddevice
        except Exception as error:
            raise RuntimeError(
                "sounddevice could not start: {}: {}".format(
                    type(error).__name__,
                    error,
                )
            )
        self.stop()
        self.voice_client = voice_client
        self.microphone = MicrophoneFrames()
        self.diagnostic = diagnostic
        try:
            self.input_stream = sounddevice.RawInputStream(
                samplerate=48000,
                channels=1,
                dtype="int16",
                blocksize=960,
                callback=self._input,
            )
            self.input_stream.start()
            if native_module:
                self._start_native(sounddevice, native_module)
                self.mode = "full-duplex"
                self.receive_enabled = True
            else:
                voice_client.play(MicrophoneSource(self.microphone))
                self.mode = "transmit-only"
                self.receive_enabled = False
            self.active = True
        except Exception:
            self.stop()
            raise

    def _start_native(self, sounddevice, native_module):
        self.output_stream = sounddevice.RawOutputStream(
            samplerate=48000,
            channels=2,
            dtype="int16",
            blocksize=960,
            callback=self._output,
        )
        self.output_stream.start()
        source = native_module.AudioFrameSource(
            self.microphone,
            opus=False,
        )
        self.voice_client.play(
            source,
            application="voip",
            signal_type="voice",
        )
        destination = native_module.BasicSink(
            self._receive,
            media_types=("audio",),
            codecs=("pcm",),
        )
        self.voice_client.listen(
            native_module.PCMDecodeSink(destination)
        )

    def stop(self):
        voice_client = self.voice_client
        if self.microphone:
            self.microphone.close()
        if voice_client:
            try:
                if getattr(voice_client, "is_listening", lambda: False)():
                    voice_client.stop_listening()
            except Exception:
                pass
            try:
                if voice_client.is_playing():
                    voice_client.stop()
            except Exception:
                pass
        for stream in (self.input_stream, self.output_stream):
            if stream:
                try:
                    stream.stop()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass
        self.input_stream = None
        self.output_stream = None
        self.microphone = None
        self.voice_client = None
        self.active = False
        self.mode = "disconnected"
        self.receive_enabled = False
        with self.lock:
            self.playback.clear()
            self.speakers.clear()
        if self.speaker_timer:
            self.speaker_timer.cancel()
            self.speaker_timer = None
        self._invalidate()

    def _input(self, indata, frame_count, time_info, status):
        samples = array.array("h")
        samples.frombytes(bytes(indata))
        if sys.byteorder != "little":
            samples.byteswap()
        stereo = array.array("h")
        for sample in samples:
            stereo.append(sample)
            stereo.append(sample)
        if sys.byteorder != "little":
            stereo.byteswap()
        if self.microphone:
            self.microphone.put(stereo.tobytes())

    def _receive(self, packet):
        if packet.media_type != "audio" or packet.codec != "pcm":
            return
        user_id = packet.user_id
        if self.client.user and user_id == self.client.user.id:
            return
        now = time.monotonic()
        with self.lock:
            frames = self.playback.setdefault(user_id, deque(maxlen=8))
            frames.append(packet.payload)
            if packet.audio_voice_activity is not False and packet.audio_level != 127:
                self.speakers[user_id] = now
        if now - self.last_invalidate >= 0.2:
            self.last_invalidate = now
            self._invalidate()
            if self.speaker_timer:
                self.speaker_timer.cancel()
            self.speaker_timer = threading.Timer(0.9, self._speaker_expired)
            self.speaker_timer.daemon = True
            self.speaker_timer.start()

    def _output(self, outdata, frames, time_info, status):
        size = frames * 4
        chunks = []
        with self.lock:
            for user_id, pending in list(self.playback.items()):
                if pending:
                    chunks.append(pending.popleft())
                if not pending:
                    self.playback.pop(user_id, None)
        outdata[:] = self._mix(chunks, size)

    def _mix(self, chunks, size):
        if not chunks:
            return bytes(size)
        output = array.array("h", [0] * (size // 2))
        for chunk in chunks:
            samples = array.array("h")
            samples.frombytes(chunk[:size])
            if sys.byteorder != "little":
                samples.byteswap()
            for index, sample in enumerate(samples):
                value = output[index] + sample
                output[index] = max(-32768, min(32767, value))
        if sys.byteorder != "little":
            output.byteswap()
        return output.tobytes()

    def speaking_ids(self):
        now = time.monotonic()
        with self.lock:
            expired = [
                user_id
                for user_id, seen in self.speakers.items()
                if now - seen > 0.8
            ]
            for user_id in expired:
                self.speakers.pop(user_id, None)
            return set(self.speakers)

    def _invalidate(self):
        try:
            self.client.loop.call_soon_threadsafe(self.client.typing.invalidate)
        except Exception:
            pass

    def _speaker_expired(self):
        self.speaking_ids()
        self.speaker_timer = None
        self._invalidate()
