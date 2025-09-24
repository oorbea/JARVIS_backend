import asyncio
import base64
import json
from typing import AsyncGenerator, AsyncIterable, Iterable, Literal, Optional, Tuple, Union
from urllib.parse import urlencode

import websockets
from websockets.legacy.client import WebSocketClientProtocol
from controllers.BaseController import BaseController
from enums.AudioFormat import AudioFormat
from enums.ChannelType import ChannelType
from enums.VoiceID import VoiceID
from flask import current_app


class TTSController(BaseController):
    __sample_rate: Literal[8000, 24000, 44100, 48000]
    __format: AudioFormat
    __channel_type: ChannelType
    __voice_id: VoiceID
    __multi_native_locale: str
    __style: str
    __ws: Optional[WebSocketClientProtocol]
    __connected: bool

    def __init__(self, sample_rate:Literal[8000, 24000, 44100, 48000] = 44100, format:AudioFormat = AudioFormat.MP3, channel_type:ChannelType = ChannelType.STEREO, voice_id:VoiceID = VoiceID.JACEK, multi_native_locale: str = "es-ES", style:str = "Conversational"):
        self.__sample_rate = sample_rate
        self.__format = format
        self.__channel_type = channel_type
        self.__voice_id = voice_id
        self.__multi_native_locale = multi_native_locale
        self.__style = style
        self.__ws = None
        self.__connected = False

    async def connect(self):
        """
        Opens a WebSocket connection to the Murf TTS API.
        Requires MURF_API_KEY to be set in the Flask app config.
        """
        qs = urlencode({
            "api_key": current_app.config["MURF_API_KEY"],
            "sample_rate": self.__sample_rate,
            "format": self.__format.value,
            "channel_type": self.__channel_type.value,
        })
        self.__ws = await websockets.connect(f"wss://api.murf.ai/v1/speech/stream-input?{qs}")
        self.__connected = True
        await self.set_voice()

    async def close(self) -> None:
        """
        Closes the WebSocket connection if it is open.
        """
        if self.__ws:
            try:
                await self.__ws.close()
            finally:
                self.__ws = None
                self.__connected = False

    async def set_voice(self) -> None:
        """
        Sends setVoiceConfigurationOrInitializeContext.
        - voice_id: e.g. 'en-US-carter'
        - style/locale: optional (when the model/voice supports it).
        """
        self.__require_ws()
        payload = {
            "setVoiceConfigurationOrInitializeContext": {
                "voiceId": self.__voice_id.value
            }
        }
        cfg = payload["setVoiceConfigurationOrInitializeContext"]
        if self.__style is not None:
            cfg["style"] = self.__style
        if self.__multi_native_locale is not None:
            cfg["multiNativeLocale"] = self.__multi_native_locale

        await self.__ws.send(json.dumps(payload))

    async def set_advanced_settings(
        self,
        min_buffer_size: Optional[int] = None,
        max_buffer_delay_ms: Optional[int] = None,
    ) -> None:
        """
        Adjusts input buffering to balance TTFB/quality.
        Recommended range from docs:
          - min_buffer_size: 40-160 characters
          - max_buffer_delay_ms: 0-1000 ms
        """
        self.__require_ws()
        data = {}
        if min_buffer_size is not None:
            data["min_buffer_size"] = int(min_buffer_size)
        if max_buffer_delay_ms is not None:
            data["max_buffer_delay_ms"] = int(max_buffer_delay_ms)
        if not data:
            return
        await self.__ws.send(json.dumps({"setAdvancedSettings": data}))

    async def send_text(
        self,
        text: str,
        context_id: Optional[str] = None,
        end: bool = False,
        clear: bool = False,
    ) -> None:
        """
        Sends 'sendText' with support for:
          - context_id: turn id (recommended for multi-turn)
          - end: marks the end of the turn to emit 'finalOutput'
          - clear: cancels/clears a previous context (useful for interruptions)
        """
        self.__require_ws()
        msg = {"sendText": {"text": text}}
        if context_id is not None:
            msg["sendText"]["context_id"] = context_id
        if end:
            msg["sendText"]["end"] = True
        if clear:
            msg["sendText"]["clear"] = True
        await self.__ws.send(json.dumps(msg))

    async def clear_context(self, context_id: Optional[str] = None) -> None:
        """Shortcut to send explicit 'clearContext'."""
        self.__require_ws()
        payload = {"clearContext": {}}
        if context_id:
            payload["clearContext"]["context_id"] = context_id
        await self.__ws.send(json.dumps(payload))

    async def audio_stream(
        self,
    ) -> AsyncGenerator[Tuple[Optional[str], bytes, bool], None]:
        """
        Async generator that yields (context_id, chunk_bytes, is_final).

        - Returns binary frames as they arrive (MP3/WAV/PCM).
        - Ignores JSON messages except to:
            * extract context_id and mark 'finalOutput' (is_final=True)
        """
        self.__require_ws()
        pending_final_for: set[str] = set()

        assert self.__ws is not None
        async for frame in self.__ws:
            if isinstance(frame, (bytes, bytearray)):
                yield (None, bytes(frame), False)
            else:
                try:
                    evt = json.loads(frame)
                except Exception:
                    continue

                if "audioOutput" in evt:
                    ctx = evt["audioOutput"].get("context_id")

                if "finalOutput" in evt:
                    ctx = evt["finalOutput"].get("context_id")
                    if ctx is None:
                        yield (None, b"", True)
                    else:
                        if ctx not in pending_final_for:
                            pending_final_for.add(ctx)
                            yield (ctx, b"", True)

    @property
    def format(self) -> AudioFormat:
        return self.__format

    def set_output_format(self, fmt: AudioFormat) -> None:
        if fmt not in (AudioFormat.MP3, AudioFormat.WAV, AudioFormat.PCM):
            raise ValueError("Only MP3, WAV, or PCM are allowed for WebSocket output.")
        self.__format = fmt

    def __require_ws(self) -> None:
        if not self.__connected or self.__ws is None:
            raise RuntimeError("WebSocket not initialized. Call connect() first.")
        
    async def run(
        self,
        text_stream: Union[Iterable[str], AsyncIterable[str]],
        *,
        context_id: Optional[str] = None,
        min_buffer_size: Optional[int] = 60,
        max_buffer_delay_ms: Optional[int] = 500,
        base64_chunks: bool = True,
        include_meta_first: bool = True,
    ) -> AsyncGenerator[dict, None]:
        """
        Orchestrates end-to-end streaming:
        - Applies advanced settings (if provided).
        - Consumes 'text_stream' (sync or async) and sends sendText() for each chunk.
        - Marks 'end=True' when input is finished.
        - Emits audio as events for your transport layer.

        Returns an async generator of "socket-friendly" dicts:
            {"type": "meta", "mime": "audio/mpeg" | "audio/wav" | "audio/L16"}
            {"type": "chunk", "data": <base64 str | bytes>}
            {"type": "done"}

        Params:
          - text_stream: Iterable[str] or AsyncIterable[str] with text chunks.
          - context_id: optional; if used, the WS groups outputs by turn.
          - min_buffer_size, max_buffer_delay_ms: latency/quality tuning.
          - base64_chunks: True -> base64 strings; False -> raw bytes.
          - include_meta_first: emits a 'meta' event at the start with the MIME.
        """
        self.__require_ws()

        if include_meta_first:
            mime = (
                "audio/mpeg" if self.__format == AudioFormat.MP3
                else "audio/wav" if self.__format == AudioFormat.WAV
                else "audio/L16"
            )
            yield {"type": "meta", "mime": mime, "sample_rate": self.__sample_rate}

        await self.set_advanced_settings(min_buffer_size, max_buffer_delay_ms)

        audio_q: asyncio.Queue = asyncio.Queue(maxsize=32)
        finished_audio = asyncio.Event()

        async def pump_audio():
            try:
                async for ctx, chunk, is_final in self.audio_stream():
                    if chunk:
                        if base64_chunks:
                            payload = base64.b64encode(chunk).decode("ascii")
                        else:
                            payload = chunk
                        await audio_q.put({"type": "chunk", "data": payload})
                    if is_final:
                        await audio_q.put({"type": "done"})
                        return
            finally:
                finished_audio.set()

        pump_task = asyncio.create_task(pump_audio())

        async for piece in _aiter(text_stream):
            if not isinstance(piece, str):
                continue
            await self.send_text(piece, context_id=context_id)

        await self.send_text("", context_id=context_id, end=True)

        done = False
        while not done:
            evt = await audio_q.get()
            yield evt
            done = evt.get("type") == "done"

        await finished_audio.wait()
        try:
            await asyncio.wait_for(pump_task, timeout=1.0)
        except asyncio.TimeoutError:
            pump_task.cancel()


async def _aiter(stream: Union[Iterable[str], AsyncIterable[str]]) -> AsyncGenerator[str, None]:
    if hasattr(stream, "__aiter__"):
        async for x in stream:
            yield x
    else:
        for x in stream:
            yield x
            await asyncio.sleep(0)