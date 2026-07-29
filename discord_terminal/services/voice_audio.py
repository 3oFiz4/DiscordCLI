import array
import queue
import sys
import threading
import time

import discord

from discord_terminal.services.voice_mixer import VoiceMixer


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
        self.mixer = VoiceMixer()
        self.active = False
        self.last_invalidate = 0
        self.speaker_timer = None
        self.mode = "disconnected"
        self.receive_enabled = False
        self.diagnostic = ""
        self.last_error = ""
        self.received_packets = 0
        self.received_bytes = 0
        self.played_bytes = 0
        self.input_device = ""
        self.output_device = ""

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
        self.last_error = ""
        self.received_packets = 0
        self.received_bytes = 0
        self.played_bytes = 0
        try:
            self.input_stream = sounddevice.RawInputStream(
                samplerate=48000,
                channels=1,
                dtype="int16",
                blocksize=960,
                callback=self._input,
                device=self._configured_device("input_device"),
            )
            self.input_stream.start()
            self.input_device = self._device_name(
                sounddevice,
                self.input_stream.device,
            )
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
            device=self._configured_device("output_device"),
        )
        self.output_stream.start()
        self.output_device = self._device_name(
            sounddevice,
            self.output_stream.device,
        )
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
        self.mixer.clear_streams()
        if self.speaker_timer:
            self.speaker_timer.cancel()
            self.speaker_timer = None
        self._invalidate()

    def _input(self, indata, frame_count, time_info, status):
        try:
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
            payload = stereo.tobytes()
            user_id = getattr(self.client.user, "id", None)
            if user_id is not None:
                if self.mixer.is_muted(user_id):
                    payload = bytes(len(payload))
                else:
                    payload = self.mixer.scale(
                        payload,
                        self.mixer.volume(user_id),
                    )
            if self.microphone:
                self.microphone.put(payload)
        except Exception as error:
            self.last_error = "{}: {}".format(
                type(error).__name__,
                error,
            )

    def _receive(self, packet):
        if (
            str(getattr(packet, "media_type", "")).lower() != "audio"
            or str(getattr(packet, "codec", "")).lower() != "pcm"
        ):
            return
        user_id = getattr(packet, "user_id", None)
        if self.client.user and user_id == self.client.user.id:
            return
        now = time.monotonic()
        try:
            self.mixer.push(packet)
            self.received_packets += 1
            self.received_bytes += len(packet.payload)
        except Exception as error:
            self.last_error = "{}: {}".format(
                type(error).__name__,
                error,
            )
            return
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
        try:
            payload = self.mixer.mix(size)
            outdata[:] = payload
            if any(payload):
                self.played_bytes += len(payload)
        except Exception as error:
            outdata[:] = bytes(size)
            self.last_error = "{}: {}".format(
                type(error).__name__,
                error,
            )

    def speaking_ids(self):
        return self.mixer.speaking_ids()

    def set_muted(self, user_id, muted):
        self.mixer.set_muted(user_id, muted)
        self._invalidate()

    def is_muted(self, user_id):
        return self.mixer.is_muted(user_id)

    def set_volume(self, user_id, percent):
        value = self.mixer.set_volume(user_id, float(percent) / 100)
        self._invalidate()
        return round(value * 100)

    def volume(self, user_id):
        return round(self.mixer.volume(user_id) * 100)

    def statistics(self):
        return {
            "received_packets": self.received_packets,
            "received_bytes": self.received_bytes,
            "played_bytes": self.played_bytes,
            "input_device": self.input_device or "default",
            "output_device": self.output_device or "default",
            "last_error": self.last_error or "none",
        }

    def _configured_device(self, name):
        return self.client.config.get(
            "settings",
            "voice_audio",
            name,
            default=None,
        )

    def _device_name(self, sounddevice, device):
        try:
            return sounddevice.query_devices(device)["name"]
        except Exception:
            return str(device)

    def _invalidate(self):
        try:
            self.client.loop.call_soon_threadsafe(self.client.typing.invalidate)
        except Exception:
            pass

    def _speaker_expired(self):
        self.speaking_ids()
        self.speaker_timer = None
        self._invalidate()
