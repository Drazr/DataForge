"""A local voice worker owns an AgentSession and a scoped LiveKit participant."""
from __future__ import annotations

import asyncio
import os
import time
import subprocess
from importlib.metadata import version
from urllib.parse import urlsplit
from datetime import timedelta

import aiohttp
from livekit import api, rtc
from livekit.agents import Agent, AgentSession, APIConnectOptions, StopResponse, inference, room_io
from livekit.agents.voice.agent_session import SessionConnectOptions
from livekit.plugins import silero

from .audio import LivePlayback, RimeAudio
from .cache import AudioCache
from .config import ROOT, SpeechConfig, validate_catalog
from .core import Controller, make_interpreter
from .runtime import Runtime, FALLBACK_TEXT


def token(room: str, identity: str):
    return (api.AccessToken(os.environ['LIVEKIT_API_KEY'], os.environ['LIVEKIT_API_SECRET'])
            .with_identity(identity).with_ttl(timedelta(minutes=25))
            .with_grants(api.VideoGrants(room_join=True, room=room, can_publish=True,
                                        can_subscribe=True, can_publish_data=False))
            .to_jwt())


class GuidedAgent(Agent):
    def __init__(self, worker):
        super().__init__(instructions='A deterministic appointment flow. No LLM is configured.')
        self.worker = worker

    async def on_user_turn_completed(self, turn_ctx, new_message):
        self.worker.runtime.transcript(new_message.text_content or '')
        raise StopResponse()


class VoiceWorker:
    def __init__(self, session_id: str, *, bypass_cache=False):
        self.id = session_id
        self.room_name = 'dataforge-' + session_id
        self.identity = 'caller-' + session_id
        self.created_at = time.monotonic()
        self.config = SpeechConfig.from_env()
        self.controller = Controller(interpreter=make_interpreter(os.getenv('DATAFORGE_INTERPRETER', 'guided')))
        self.room = rtc.Room()
        self.http = None
        self.session = None
        self.audio = None
        self.runtime = None
        self.catalog = None
        self.closed = False
        self.tasks: set[asyncio.Task] = set()
        self.bypass_cache = bypass_cache
        self._recognition = None
        self.start_requested = False

    def schedule(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return task

    async def connect(self):
        self.catalog = await validate_catalog(self.config)
        self.http = aiohttp.ClientSession()
        self.audio = RimeAudio(self.config, AudioCache(ROOT / '.product-cache'), self.http, self.controller.emit)
        self.audio.bypass = self.bypass_cache
        self._recognition = inference.STT(model='deepgram/nova-3', language='en',
                                          http_session=self.http,
                                          api_key=os.environ['LIVEKIT_API_KEY'],
                                          api_secret=os.environ['LIVEKIT_API_SECRET'])
        self.session = AgentSession(
            stt=self._recognition, vad=silero.VAD.load(), llm=None, tts=None,
            user_away_timeout=None,
            turn_handling={'turn_detection': 'vad',
                           'endpointing': {'min_delay': .5, 'max_delay': 3},
                           'interruption': {'mode': 'vad', 'enabled': True, 'min_duration': .2,
                                            'resume_false_interruption': False},
                           'preemptive_generation': {'enabled': False}},
            conn_options=SessionConnectOptions(stt_conn_options=APIConnectOptions(max_retry=0, timeout=15)))
        self.runtime = Runtime(self.controller, LivePlayback(self.session, self.audio))

        @self.session.on('user_state_changed')
        def state(event):
            if event.new_state == 'speaking':
                self.runtime.speech_started()

        @self.session.on('error')
        def error(event):
            if not self.closed:
                self.schedule(self.runtime.failure('recognition'))

        @self.session.on('agent_state_changed')
        def agent_state(event):
            self.controller.emit('agent_state', state=event.new_state)

        @self.room.on('participant_disconnected')
        def disconnected(participant):
            if participant.identity == self.identity and not self.closed:
                self.schedule(self.runtime.failure('connection'))

        @self.room.on('reconnecting')
        def reconnecting():
            if not self.closed:
                self.schedule(self.runtime.failure('connection'))

        await self.room.connect(os.environ['LIVEKIT_URL'], token(self.room_name, 'worker-' + self.id))
        await self.session.start(agent=GuidedAgent(self), room=self.room, session_host=False, record=False,
                                 room_options=room_io.RoomOptions(participant_identity=self.identity,
                                                                 text_input=False, text_output=False,
                                                                 close_on_disconnect=False))
        self.controller.emit('provider_config', **self.config.public(), transport='LiveKit WebRTC/Opus', stt='deepgram/nova-3')

    async def start(self):
        if self.start_requested:
            return
        if self.identity not in {p.identity for p in self.room.remote_participants.values()}:
            raise ValueError('The browser audio participant has not connected yet.')
        self.start_requested = True
        # Prewarm the disclosed fallback once, before normal speech. Failures are
        # visible and never converted into a mock voice session.
        if self.controller.status == 'ready':
            try:
                await self.audio.render(FALLBACK_TEXT)
            except Exception:
                await self.runtime.failure('speech_provider')
                return
        self.runtime.start()

    async def recover(self):
        if self.identity not in {p.identity for p in self.room.remote_participants.values()}:
            raise ValueError('Reconnect browser audio before retrying.')
        if self.controller.failure == 'recognition':
            # A failed STT stream cannot be revived by merely changing UI state.
            raise ValueError('Speech recognition stopped. End this session and start a new one.')
        self.runtime.recover()

    def evidence(self):
        try:
            revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=5)
            commit = revision.stdout.strip() if revision.returncode == 0 else 'unavailable'
        except (OSError, subprocess.TimeoutExpired):
            commit = 'unavailable'
        endpoint = urlsplit(os.environ.get('LIVEKIT_URL', ''))
        return {'schema': 1, 'session_id': self.id, 'snapshot': self.controller.snapshot(),
                'git_commit': commit,
                'dependencies': {name: version(name) for name in ('livekit-agents','livekit-plugins-rime','livekit-plugins-silero','livekit')},
                'livekit_endpoint': f'{endpoint.scheme}://{endpoint.hostname or ""}',
                'livekit_region': os.environ.get('LIVEKIT_REGION_LABEL') or 'not verified',
                'configuration': self.config.public(), 'catalog': self.catalog,
                'transport': 'LiveKit WebRTC/Opus', 'stt': 'deepgram/nova-3',
                'events': list(self.controller.events),
                'limitations': ['Sender-side playout completion is not proof of human comprehension.',
                                'Browser transport is not a telephone codec experiment.',
                                'Synthetic appointment only; no real booking is updated.']}

    async def close(self):
        if self.closed:
            return
        self.closed = True
        if self.runtime:
            await self.runtime.close()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        if self.session:
            await self.session.aclose()
        if self._recognition:
            await self._recognition.aclose()
        if self.audio:
            await self.audio.close()
        await self.room.disconnect()
        if self.http:
            await self.http.close()
