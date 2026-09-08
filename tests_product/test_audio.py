"""Exercise the real Rime adapter with a substituted provider stream only."""
from contextlib import asynccontextmanager
from types import SimpleNamespace
import pytest
from product.audio import RimeAudio
from product.cache import AudioCache
from product.config import SpeechConfig


class Provider:
    calls=0
    fail=False
    @asynccontextmanager
    async def synthesize(self,text,conn_options):
        assert conn_options.max_retry == 0
        self.calls+=1
        async def frames():
            yield SimpleNamespace(frame=SimpleNamespace(sample_rate=24000,num_channels=1,data=b'\x01\x00'*100))
            if self.fail:
                raise OSError('Truncated provider response')
        yield frames()


def adapter(tmp_path):
    audio=RimeAudio.__new__(RimeAudio)
    audio.config=SpeechConfig()
    audio.cache=AudioCache(tmp_path)
    audio.emit=lambda *a,**k:None
    audio.provider=Provider()
    audio.fail_next=False
    audio.bypass=False
    return audio


async def test_complete_synthesis_reused_without_new_provider_call(tmp_path):
    audio=adapter(tmp_path)
    first=await audio.render('hello')
    assert first == await audio.render('hello')
    assert audio.provider.calls == 1
    audio.bypass=True
    await audio.render('hello')
    assert audio.provider.calls == 2


async def test_truncated_stream_never_enters_cache_or_retries(tmp_path):
    audio=adapter(tmp_path)
    audio.provider.fail=True
    with pytest.raises(OSError):
        await audio.render('hello')
    assert audio.provider.calls == 1
    assert audio.cache.get('hello',audio.config.public()) is None


async def test_fault_injection_also_covers_cached_audio(tmp_path):
    audio=adapter(tmp_path)
    await audio.render('hello')
    audio.fail_next=True
    with pytest.raises(RuntimeError):
        await audio.render('hello')
    assert audio.provider.calls == 1
