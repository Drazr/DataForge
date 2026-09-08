import asyncio

from product.core import Controller
from product.runtime import Runtime


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


async def test_sequential_flow_confirms_after_complete_question():
    c, p = Controller(), Playback()
    p.gate.set()
    r = Runtime(c, p)
    r.start()
    await r.task
    assert c.status == 'awaiting_confirmation'
    r.transcript('yes', 'fresh', c.clock())
    await r.task
    assert c.confirmed
    await r.close()


async def test_reply_during_playback_is_ignored():
    c, p = Controller(), Playback()
    r = Runtime(c, p)
    r.start()
    await asyncio.sleep(0)
    r.transcript('yes', 'early', c.clock())
    assert not c.confirmed
    assert p.spoken == ['welcome']
    p.gate.set()
    await r.task
    assert c.status == 'awaiting_confirmation'
    await r.close()


async def test_provider_failure_enters_recovery_and_uses_fallback():
    c, p = Controller(), Playback()
    p.fail = True
    r = Runtime(c, p)
    r.start()
    await r.task
    assert c.status == 'recovery' and c.failure == 'speech_provider'
    assert not c.confirmed and p.fallbacks == 1
    await r.close()


async def test_close_cancels_pending_playback():
    c, p = Controller(), Playback()
    r = Runtime(c, p)
    r.start()
    await asyncio.sleep(0)
    await r.close()
    assert c.status == 'ended'
    assert p.cancels >= 1
