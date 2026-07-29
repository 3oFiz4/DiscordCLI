import array
import sys
import threading
import time


class VoiceMixer:
    def __init__(self):
        self.buffers = {}
        self.ssrc_users = {}
        self.speakers = {}
        self.muted_users = set()
        self.volumes = {}
        self.lock = threading.Lock()

    def push(self, packet):
        user_id = getattr(packet, "user_id", None)
        ssrc = getattr(packet, "ssrc", None)
        payload = bytes(getattr(packet, "payload", b""))
        if not payload:
            return
        now = time.monotonic()
        with self.lock:
            key = self._key(user_id, ssrc)
            if user_id is not None and ssrc is not None:
                self._promote(ssrc, user_id)
                key = int(user_id)
            if key not in self.muted_users:
                pending = self.buffers.setdefault(key, bytearray())
                pending.extend(payload)
                maximum = 3840 * 50
                if len(pending) > maximum:
                    del pending[:-maximum]
            if self._active(packet):
                self.speakers[key] = now

    def mix(self, size):
        chunks = []
        with self.lock:
            for key, pending in list(self.buffers.items()):
                if key in self.muted_users:
                    pending.clear()
                if pending:
                    chunk = bytes(pending[:size])
                    del pending[:size]
                    chunks.append(
                        self._scale(chunk, self.volumes.get(key, 1.0))
                    )
                if not pending:
                    self.buffers.pop(key, None)
        if not chunks:
            return bytes(size)
        output = array.array("h", [0] * (size // 2))
        for chunk in chunks:
            samples = self._samples(chunk)
            for index, sample in enumerate(samples):
                output[index] = max(
                    -32768,
                    min(32767, output[index] + sample),
                )
        return self._bytes(output)

    def scale(self, payload, volume):
        return self._scale(payload, volume)

    def set_muted(self, user_id, muted):
        with self.lock:
            if muted:
                self.muted_users.add(user_id)
                pending = self.buffers.get(user_id)
                if pending:
                    pending.clear()
            else:
                self.muted_users.discard(user_id)

    def is_muted(self, user_id):
        with self.lock:
            return user_id in self.muted_users

    def set_volume(self, user_id, volume):
        value = max(0.0, min(2.0, float(volume)))
        with self.lock:
            if value == 1.0:
                self.volumes.pop(user_id, None)
            else:
                self.volumes[user_id] = value
        return value

    def volume(self, user_id):
        with self.lock:
            return self.volumes.get(user_id, 1.0)

    def speaking_ids(self):
        now = time.monotonic()
        with self.lock:
            expired = [
                key
                for key, seen in self.speakers.items()
                if now - seen > 0.8
            ]
            for key in expired:
                self.speakers.pop(key, None)
            return {
                key
                for key in self.speakers
                if isinstance(key, int)
            }

    def clear_streams(self):
        with self.lock:
            self.buffers.clear()
            self.ssrc_users.clear()
            self.speakers.clear()

    def _key(self, user_id, ssrc):
        if user_id is not None:
            return int(user_id)
        if ssrc in self.ssrc_users:
            return self.ssrc_users[ssrc]
        return ("ssrc", ssrc)

    def _promote(self, ssrc, user_id):
        user_id = int(user_id)
        self.ssrc_users[ssrc] = user_id
        unknown = ("ssrc", ssrc)
        pending = self.buffers.pop(unknown, None)
        if pending:
            self.buffers.setdefault(user_id, bytearray()).extend(pending)
        seen = self.speakers.pop(unknown, None)
        if seen is not None:
            self.speakers[user_id] = seen

    def _active(self, packet):
        activity = getattr(packet, "audio_voice_activity", None)
        level = getattr(packet, "audio_level", None)
        return activity is not False and level != 127

    def _scale(self, payload, volume):
        if not payload:
            return payload
        if volume == 1.0:
            return payload
        samples = self._samples(payload)
        for index, sample in enumerate(samples):
            samples[index] = max(
                -32768,
                min(32767, round(sample * volume)),
            )
        return self._bytes(samples)

    def _samples(self, payload):
        samples = array.array("h")
        samples.frombytes(payload[:len(payload) - len(payload) % 2])
        if sys.byteorder != "little":
            samples.byteswap()
        return samples

    def _bytes(self, samples):
        if sys.byteorder != "little":
            samples.byteswap()
        return samples.tobytes()
