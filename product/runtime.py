"""Cancelable playback orchestration, testable without network access."""
from __future__ import annotations

import asyncio
import uuid
from typing import Protocol

from .core import Controller, Segment

FALLBACK_TEXT = 'The voice service is unavailable. Your appointment has not been confirmed. Please try again.'


class Playback(Protocol):
    async def speak(self, segment: Segment) -> bool: ...
    def cancel(self) -> None: ...
    async def fallback(self) -> bool: ...


class Runtime:
    def __init__(self, controller: Controller, playback: Playback, notify=lambda: None, silence_seconds=15):
        self.controller = controller
        self.playback = playback
        self.notify = notify
        self.silence_seconds = silence_seconds
        self.task: asyncio.Task | None = None
        self.timer: asyncio.Task | None = None
        self.input_started = 0.0
        self.input_id = ''
        self.input_active = False
        self.closed = False

    def cancel_timer(self):
        if self.timer and self.timer is not asyncio.current_task():
            self.timer.cancel()
        self.timer = None

    def cancel_playback(self):
        if self.task and self.task is not asyncio.current_task():
            self.task.cancel()
        self.task = None
        self.playback.cancel()

    def launch(self, segments):
        if not segments or self.closed:
            return
        self.cancel_timer()
        self.cancel_playback()
        generation = self.controller.generation
        self.task = asyncio.create_task(self._play(segments, generation))

    async def _play(self, segments, generation):
        try:
            for segment in segments:
                if not self.controller.begin(segment, generation):
                    return
                self.notify()
                complete = await self.playback.speak(segment)
                if not complete:
                    if generation == self.controller.generation:
                        self.controller.interrupt()
                        self.notify()
                        self.arm_silence()
                    return
                if not self.controller.complete(segment, generation):
                    return
                self.notify()
            if not self.controller.terminal:
                self.arm_silence()
        except asyncio.CancelledError:
            raise
        except Exception:
            if generation == self.controller.generation and not self.closed:
                await self.failure('speech_provider')

    def start(self):
        self.launch(self.controller.start())

    def speech_started(self):
        if self.controller.terminal or self.closed:
            return
        self.input_started = self.controller.clock()
        self.input_id = uuid.uuid4().hex
        self.input_active = True
        self.cancel_timer()
        # Preserve the confirmation gate when merely listening. Invalidate it
        # immediately when a speech segment or a synthesis is in flight.
        if self.controller.current:
            self.controller.interrupt()
            self.cancel_playback()
        self.controller.emit('input_started', input_id=self.input_id)
        self.notify()

    def speech_stopped(self):
        if not self.input_active:
            return
        self.input_active = False
        # Give ASR time to finalize; VAD-only turns still need a timeout.
        self.arm_silence()

    def transcript(self, text: str):
        if self.input_id and self.input_id in self.controller.seen_inputs:
            return
        self.input_active = False
        self.cancel_timer()
        if not self.input_id:
            # Without observed speech onset, never accept a confirmation.
            self.input_started = 0
            self.input_id = uuid.uuid4().hex
        segments = self.controller.receive(text, self.input_id, self.input_started)
        self.notify()
        self.launch(segments)

    def arm_silence(self):
        self.cancel_timer()
        if (self.closed or self.input_active or self.controller.terminal
                or self.controller.status in {'ready', 'recovery'} or self.controller.current):
            return
        self.timer = asyncio.create_task(self._silence())

    async def _silence(self):
        await asyncio.sleep(self.silence_seconds)
        if self.closed or self.input_active or self.controller.terminal:
            return
        segments = self.controller.receive('', uuid.uuid4().hex, self.controller.clock())
        self.notify()
        self.launch(segments)

    async def failure(self, category):
        if self.closed:
            return
        self.input_active = False
        self.cancel_timer()
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
        if self.closed:
            return
        self.input_id = ''
        self.input_active = False
        self.launch(self.controller.recover())
        self.notify()

    async def close(self):
        if self.closed:
            return
        self.closed = True
        self.input_active = False
        task, timer = self.task, self.timer
        self.cancel_timer()
        self.cancel_playback()
        self.controller.end()
        await asyncio.gather(*(t for t in (task, timer) if t and t is not asyncio.current_task()), return_exceptions=True)
        self.notify()
