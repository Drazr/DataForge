"""Verify real SDK interfaces offline, without API calls or placeholder modules."""
import asyncio
import pytest
from product import worker  # exercises Windows native runtime loading
from livekit.agents import AgentSession, APIConnectOptions, StopResponse, llm
from livekit.agents.voice.agent_session import SessionConnectOptions
from livekit.plugins import silero
from product.core import Controller
from product.runtime import Runtime


async def test_vad_and_sdk_options_construct():
    vad = silero.VAD.load()
    session = AgentSession(stt=None, llm=None, tts=None, vad=vad,
                           turn_handling={'turn_detection':'vad','interruption':{'mode':'vad','resume_false_interruption':False},'preemptive_generation':{'enabled':False}},
                           conn_options=SessionConnectOptions(stt_conn_options=APIConnectOptions(max_retry=0)))
    assert session is not None


async def test_agent_routes_finalized_turn_to_interpreter_and_suppresses_llm():
    received=[]
    class RuntimeStub:
        def transcript(self,text): received.append(text)
    class WorkerStub:
        runtime=RuntimeStub()
    agent=worker.GuidedAgent(WorkerStub())
    with pytest.raises(StopResponse):
        await agent.on_user_turn_completed(llm.ChatContext(),llm.ChatMessage(role='user',content=['repeat the time']))
    assert received == ['repeat the time']


async def test_actual_agent_session_plays_supplied_pcm_without_tts_or_llm():
    from livekit.agents import Agent
    from livekit.agents.voice import io
    from product.audio import LivePlayback
    from product.config import SpeechConfig
    from product.core import Segment
    class Sink(io.AudioOutput):
        def __init__(self):
            super().__init__(label='offline-verification', capabilities=io.AudioOutputCapabilities(pause=False),sample_rate=24000)
            self.samples=0
        async def capture_frame(self,frame):
            await super().capture_frame(frame)
            self.samples+=frame.samples_per_channel
        def flush(self):
            super().flush()
            self.on_playback_finished(playback_position=self.samples/24000,interrupted=False)
        def clear_buffer(self):
            self.on_playback_finished(playback_position=self.samples/24000,interrupted=True)
    class Audio:
        config=SpeechConfig()
        emit=staticmethod(lambda *args,**kwargs:None)
        async def render(self,text):return b'\x01\x00'*2400
    sink=Sink()
    session=AgentSession(vad=None,stt=None,llm=None,tts=None,turn_handling={'turn_detection':'manual'},user_away_timeout=None)
    session.output.audio=sink
    try:
        await session.start(Agent(instructions='Offline SDK compatibility test.'),session_host=False,record=False)
        playback=LivePlayback(session,Audio())
        assert await asyncio.wait_for(playback.speak(Segment('test','Test speech')),timeout=10)
        assert sink.samples==2400
    finally:
        await session.aclose()


async def test_evidence_export_survives_missing_git_permission(monkeypatch):
    def unavailable(*args,**kwargs):raise PermissionError('Git cannot be launched')
    monkeypatch.setattr(worker.subprocess,'run',unavailable)
    voice=worker.VoiceWorker('offline-evidence')
    report=voice.evidence()
    assert report['git_commit']=='unavailable'
    assert report['snapshot']['confirmed'] is False
    assert report['configuration']['provider']=='Rime'
