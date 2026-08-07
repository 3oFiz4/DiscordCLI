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
            self._setup_compat()
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

    def _setup_compat(self):
        import math
        import struct
        import socket
        import sys
        import types
        import importlib.machinery
        import discord.gateway


        if not hasattr(discord.gateway.DiscordVoiceWebSocket, "MEDIA_SINK_WANTS"):
            discord.gateway.DiscordVoiceWebSocket.MEDIA_SINK_WANTS = 15

        if not hasattr(discord.gateway.DiscordVoiceWebSocket, "video_state"):
            async def video_state(self, *, video_ssrc=0, rtx_ssrc=0, streams=None, audio_ssrc=None):
                if audio_ssrc is None:
                    audio_ssrc = getattr(self._connection, "ssrc", 0)
                formatted_streams = []
                for s in (streams or []):
                    if isinstance(s, dict):
                        formatted_streams.append(s)
                    else:
                        st = {
                            "type": getattr(s, "type", "video"),
                            "rid": getattr(s, "rid", "100"),
                            "quality": getattr(s, "quality", 100),
                            "active": getattr(s, "active", True),
                        }
                        formatted_streams.append(st)
                payload = {
                    "op": self.VIDEO,
                    "d": {
                        "audio_ssrc": audio_ssrc,
                        "video_ssrc": video_ssrc,
                        "rtx_ssrc": rtx_ssrc,
                        "streams": formatted_streams,
                    },
                }
                await self.send_as_json(payload)

            discord.gateway.DiscordVoiceWebSocket.video_state = video_state


        if not hasattr(discord.gateway.DiscordVoiceWebSocket, "_original_speak"):
            discord.gateway.DiscordVoiceWebSocket._original_speak = discord.gateway.DiscordVoiceWebSocket.speak
            async def patched_speak(self, state=None):
                if state is None:
                    state = discord.enums.SpeakingState.voice
                # Convert SpeakingFlags or anything to int safely
                val = int(getattr(state, "value", state))
                payload = {
                    'op': self.SPEAKING,
                    'd': {
                        'speaking': val,
                        'delay': 0,
                        'ssrc': self._connection.ssrc,
                    },
                }
                await self.send_as_json(payload)
            discord.gateway.DiscordVoiceWebSocket.speak = patched_speak

        if not hasattr(discord.flags, "SpeakingFlags"):



            @discord.flags.fill_with_flags()
            class SpeakingFlags(discord.flags.BaseFlags):
                __slots__ = ()

                @classmethod
                def none(cls):
                    return cls._from_value(0)

                @discord.flags.flag_value
                def voice(self):
                    return 1

                @discord.flags.flag_value
                def soundshare(self):
                    return 2

                @discord.flags.flag_value
                def priority(self):
                    return 4

            discord.flags.SpeakingFlags = SpeakingFlags


        if "discord.voice_media" not in sys.modules:
            vm = types.ModuleType("discord.voice_media")
            vm.RTP_AUDIO_LEVEL_SILENCE = 127

            def _audio_level_from_pcm(pcm_bytes):
                if not pcm_bytes:
                    return 127
                count = len(pcm_bytes) // 2
                if count == 0:
                    return 127
                samples = struct.unpack(f"<{count}h", pcm_bytes[:count * 2])
                rms = math.sqrt(sum(s * s for s in samples) / count)
                if rms <= 0:
                    return 127
                db = 20 * math.log10(rms / 32767.0)
                return max(0, min(127, int(-db)))

            def _audio_rtp_extension_payload(level, vad=True):
                b0 = (1 << 7) if vad else 0
                b0 |= (level & 0x7F)
                return bytes([b0])

            def _rtp_header_with_one_byte_extensions(header, extensions):
                ext_bytes = bytearray()
                for ext_id, payload in extensions:
                    length = len(payload) - 1
                    if 0 <= length <= 15:
                        header_byte = ((ext_id & 0x0F) << 4) | (length & 0x0F)
                        ext_bytes.append(header_byte)
                        ext_bytes.extend(payload)
                padding = (4 - (len(ext_bytes) % 4)) % 4
                ext_bytes.extend(b"\x00" * padding)
                words = len(ext_bytes) // 4
                ext_header = struct.pack(">HH", 0xBEDE, words)
                return header + ext_header + ext_bytes

            class VoiceCodec:
                def __init__(self, name, payload_type=0):
                    self.name = name
                    self.payload_type = payload_type

                @classmethod
                def opus(cls, payload_type=120, **kwargs):
                    return cls("opus", payload_type)

                @classmethod
                def pcm(cls, payload_type=120, **kwargs):
                    return cls("pcm", payload_type)

                @classmethod
                def video(cls, name="h264", payload_type=101, **kwargs):
                    return cls(name, payload_type)

            class VoiceStreamResolution:
                def __init__(self, width=1280, height=720, fps=30):
                    self.width = width
                    self.height = height
                    self.fps = fps

            class VoiceStream:
                def __init__(self, type="audio", codec="opus", quality=100):
                    self.type = type
                    self.codec = codec
                    self.quality = quality

                @classmethod
                def video(cls, quality=100, **kwargs):
                    return cls(type="video", codec="h264", quality=quality)

                @classmethod
                def screen(cls, quality=100, **kwargs):
                    return cls(type="video", codec="h264", quality=quality)

                @classmethod
                def audio(cls, **kwargs):
                    return cls(type="audio", codec="opus")

            vm._audio_level_from_pcm = _audio_level_from_pcm
            vm._audio_rtp_extension_payload = _audio_rtp_extension_payload
            vm._rtp_header_with_one_byte_extensions = _rtp_header_with_one_byte_extensions
            vm.VoiceCodec = VoiceCodec
            vm.VoiceStreamResolution = VoiceStreamResolution
            vm.VoiceStream = VoiceStream
            sys.modules["discord.voice_media"] = vm

        if "discord.stream" not in sys.modules:
            ds = types.ModuleType("discord.stream")
            class Stream:
                pass
            class StreamProtocol:
                pass
            ds.Stream = Stream
            ds.StreamProtocol = StreamProtocol
            sys.modules["discord.stream"] = ds

        try:
            import discord.ext.native_voice._native_voice as nv_c
            if hasattr(nv_c, "NativeUDPTransport"):
                setattr(nv_c.NativeUDPTransport, "type", socket.SOCK_DGRAM)
                setattr(nv_c.NativeUDPTransport, "family", socket.AF_INET)
                setattr(nv_c.NativeUDPTransport, "proto", 0)
        except Exception:
            pass

        try:
            import discord.ext.native_voice as nv
            if not hasattr(nv.VoiceClient, "stream_clients"):
                nv.VoiceClient.stream_clients = property(
                    lambda self: getattr(self, "_stream_clients", ())
                )
        except Exception:
            pass

        try:
            import discord.voice_state
            if not hasattr(discord.voice_state.VoiceConnectionState, "video_ssrcs"):
                discord.voice_state.VoiceConnectionState.video_ssrcs = property(
                    lambda self: getattr(self, "_video_ssrcs", ())
                )
        except Exception:
            pass





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
