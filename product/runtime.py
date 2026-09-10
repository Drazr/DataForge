"""Sequential delivery with explicit service recovery and shutdown."""
from __future__ import annotations

import asyncio
from typing import Protocol

from .core import Controller, Segment

FALLBACK_TEXT = 'The voice service is unavailable. Your appointment has not been confirmed. Please try again.'


class Playback(Protocol):
    async def speak(self, segment: Segment) -> bool: ...
    def cancel(self) -> None: ...
    async def fallback(self) -> bool: ...


class Runtime:
    def __init__(self, controller: Controller, playback: Playback, notify=lambda: None):
        self.controller = controller
        self.playback = playback
        self.notify = notify
        self.task: asyncio.Task | None = None
        self.closed = False

    def cancel_playback(self):
        if self.task and self.task is not asyncio.current_task():
            self.task.cancel()
        self.task = None
        self.playback.cancel()

    def launch(self, segments):
        if not segments or self.closed:
            return
        self.cancel_playback()
        self.task = asyncio.create_task(self._play(segments, self.controller.generation))

    async def _play(self, segments, generation):
        try:
            for segment in segments:
                if not self.controller.begin(segment, generation):
                    return
                self.notify()
                if not await self.playback.speak(segment):
                    raise RuntimeError('Playback did not complete')
                if not self.controller.complete(segment, generation):
                    return
                self.notify()
        except asyncio.CancelledError:
            raise
        except Exception:
            if generation == self.controller.generation and not self.closed:
                await self.failure('speech_provider')

    def start(self):
        self.launch(self.controller.start())

    def transcript(self, text: str, input_id: str, started_at: float):
        if self.closed or (self.task and not self.task.done()):
            return
        self.launch(self.controller.receive(text, input_id, started_at))
        self.notify()

    async def failure(self, category):
        if self.closed:
            return
        self.cancel_playback()
        self.controller.fail(category)
        self.notify()
        if category != 'connection' and not self.controller.confirmed:
            try:
                available = await self.playback.fallback()
                self.controller.emit('fallback', cached_rime=available)
            except Exception:
                self.controller.emit('fallback', cached_rime=False)
            self.notify()

    def recover(self):
        if not self.closed:
            self.launch(self.controller.recover())
            self.notify()

    def report_difficulty(self, source='user_reported'):
        if self.closed:
            raise ValueError('Session ended. Start a new session.')
        segments = self.controller.report_difficulty(source)
        self.launch(segments)
        self.notify()

    async def close(self):
        if self.closed:
            return
        self.closed = True
        task = self.task
        self.cancel_playback()
        self.controller.end()
        if task and task is not asyncio.current_task():
            await asyncio.gather(task, return_exceptions=True)
        self.notify()
