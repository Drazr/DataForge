"""Rime is the only synthesis provider. Buffered PCM enables verified reuse."""
from __future__ import annotations

import asyncio
import time

from .cache import AudioCache
from .config import SpeechConfig
from .runtime import FALLBACK_TEXT


class RimeAudio:
    def __init__(self, config: SpeechConfig, cache: AudioCache, http_session, emit=lambda *a, **k: None):
        from livekit.plugins import rime
        self.config, self.cache, self.emit = config, cache, emit
        self.provider = rime.TTS(model=config.model, speaker=config.speaker,
                                 lang=config.language, sample_rate=config.sample_rate,
                                 time_scale_factor=config.time_scale_factor,
                                 base_url=config.endpoint, use_websocket=False,
                                 http_session=http_session)
        self.fail_next = False
        self.bypass = False

    async def render(self, text):
        from livekit.agents import APIConnectOptions
        started = time.monotonic()
        config = self.config.public()
        # Fault injection intentionally runs before cache lookup.
        if self.fail_next:
            self.fail_next = False
            raise RuntimeError('Injected speech provider failure')
        data = None if self.bypass else self.cache.get(text, config)
        if data is not None:
            self.emit('audio_ready', cached=True, key=self.cache.key(text, config), seconds=time.monotonic()-started)
            return data
        chunks = []
        async with self.provider.synthesize(text, conn_options=APIConnectOptions(max_retry=0, timeout=15)) as stream:
            async for item in stream:
                if item.frame.sample_rate != self.config.sample_rate or item.frame.num_channels != 1:
                    raise ValueError('Unexpected Rime output format')
                chunks.append(bytes(item.frame.data))
                if sum(map(len, chunks)) > self.config.sample_rate * 2 * 60:
                    raise ValueError('Speech exceeded the one-minute segment limit')
        data = b''.join(chunks)
        # Only publish a cache entry after the provider stream completes.
        self.cache.put(text, config, data)
        self.emit('audio_ready', cached=False, key=self.cache.key(text, config), seconds=time.monotonic()-started)
        return data

    async def close(self):
        await self.provider.aclose()


async def pcm_frames(data, rate):
    from livekit import rtc
    size = rate // 50 * 2
    for offset in range(0, len(data), size):
        chunk = data[offset:offset + size]
        yield rtc.AudioFrame(data=chunk, sample_rate=rate, num_channels=1, samples_per_channel=len(chunk)//2)
        await asyncio.sleep(0)


class LivePlayback:
    def __init__(self, session, audio: RimeAudio):
        self.session, self.audio = session, audio
        self.handle = None

    async def play(self, text, data):
        handle = self.session.say(text, audio=pcm_frames(data, self.audio.config.sample_rate),
                                  allow_interruptions=False, add_to_chat_ctx=False)
        self.audio.emit('playback_submitted', bytes=len(data), duration_s=len(data)/(2*self.audio.config.sample_rate))
        self.handle = handle
        try:
            await handle.wait_for_playout()
            if handle.exception():
                raise RuntimeError('Audio playback failed') from handle.exception()
            self.audio.emit('playback_finished', complete=not handle.interrupted)
            return not handle.interrupted
        finally:
            if self.handle is handle:
                self.handle = None

    async def speak(self, segment):
        data = await self.audio.render(segment.text)
        return await self.play(segment.text, data)

    def cancel(self):
        if self.handle and not self.handle.done():
            self.handle.interrupt(force=True)
        self.handle = None

    async def fallback(self):
        data = self.audio.cache.get(FALLBACK_TEXT, self.audio.config.public())
        if data is None:
            return False
        return await self.play(FALLBACK_TEXT, data)
