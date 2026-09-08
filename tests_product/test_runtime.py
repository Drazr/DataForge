import asyncio
import pytest
from product.core import Controller
from product.runtime import Runtime
from test_core import play


class Playback:
    def __init__(self):
        self.spoken = []
        self.gate = asyncio.Event()
        self.fail = False
        self.cancels = 0
        self.fallbacks = 0

    async def speak(self, segment):
        self.spoken.append(segment.id)
        if self.fail:
            raise OSError('Provider failed')
        await self.gate.wait()
        return True

    def cancel(self):
        self.cancels += 1

    async def fallback(self):
        self.fallbacks += 1
        return False


async def test_interrupt_cancels_queue_and_restarts_requested_fact():
    c, p = Controller(), Playback()
    r = Runtime(c, p)
    r.start()
    await asyncio.sleep(0)
    r.speech_started()
    await asyncio.sleep(0)
    assert p.spoken == ['welcome']
    assert c.current is None
    r.transcript('repeat the time')
    p.gate.set()
    await r.task
    assert p.spoken[1:] == ['time', 'location', 'reference', 'question']
    r.speech_started()
    r.transcript('yes')
    await r.task
    assert c.confirmed
    await r.close()


async def test_no_speech_onset_cannot_confirm():
    c, p = Controller(), Playback()
    play(c, c.start())
    r = Runtime(c, p)
    r.transcript('yes')
    assert not c.confirmed
    await r.close()


async def test_provider_failure_does_not_complete_segment():
    c, p = Controller(), Playback()
    p.fail = True
    r = Runtime(c, p)
    r.start()
    task = r.task
    await task
    assert c.status == 'recovery' and c.failure == 'speech_provider'
    assert not c.confirmed and p.fallbacks == 1
    await r.close()


async def test_silence_closes_after_two_prompts():
    c, p = Controller(), Playback()
    p.gate.set()
    r = Runtime(c, p, silence_seconds=.001)
    r.start()
    for _ in range(100):
        await asyncio.sleep(.002)
        if c.terminal:
            break
    assert c.status == 'ended' and c.unanswered == 2
    await r.close()
