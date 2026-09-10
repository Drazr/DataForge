"""Loopback-only control API; browser receives room-scoped credentials only."""
from __future__ import annotations

import asyncio
import hmac
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import ROOT, SpeechConfig, missing_credentials
from .core import Appointment

load_dotenv(ROOT / '.env')
sessions: dict = {}
creation_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    async def reap():
        while True:
            await asyncio.sleep(30)
            for sid, entry in list(sessions.items()):
                if time.monotonic() - entry['worker'].created_at > 1200:
                    await entry['worker'].close()
                    sessions.pop(sid, None)
    task = asyncio.create_task(reap())
    yield
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    await asyncio.gather(*(entry['worker'].close() for entry in sessions.values()), return_exceptions=True)
    sessions.clear()


app = FastAPI(title='DataForge local voice worker', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])


@app.middleware('http')
async def local_origin(request: Request, call_next):
    origin = request.headers.get('origin')
    if origin and origin not in {'http://localhost:3000', 'http://127.0.0.1:3000'}:
        return JSONResponse({'detail': 'Only the local product origin is allowed.'}, status_code=403)
    if request.method == 'POST' and not request.headers.get('content-type', '').startswith('application/json'):
        return JSONResponse({'detail': 'JSON requests are required.'}, status_code=415)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    return response


def entry_for(sid, request):
    entry = sessions.get(sid)
    supplied = request.headers.get('authorization', '').removeprefix('Bearer ')
    if not entry or not hmac.compare_digest(supplied, entry['secret']):
        raise HTTPException(404, 'Session not found or expired.')
    return entry


class Create(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cache_mode: Literal['normal', 'bypass'] = 'normal'


class Action(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['start', 'end', 'recover', 'connection_lost', 'speech_failure', 'recognition_failure', 'fail_next_synthesis', 'hearing_difficulty', 'competing_speech_demo']


@app.get('/api/health')
async def health():
    from dataclasses import asdict
    missing = missing_credentials()
    return {'configured': not missing, 'missing': missing, 'speech': SpeechConfig.from_env().public(),
            'appointment': asdict(Appointment()), 'test_mode': os.getenv('DATAFORGE_TEST_MODE') == '1',
            'verification': 'not_run'}


@app.post('/api/sessions')
async def create_session(body: Create):
    missing = missing_credentials()
    if missing:
        raise HTTPException(503, 'Configure server-side credentials: ' + ', '.join(missing))
    if body.cache_mode == 'bypass' and os.getenv('DATAFORGE_TEST_MODE') != '1':
        raise HTTPException(403, 'Cache bypass requires local test mode.')
    async with creation_lock:
        if sum(not e['worker'].closed for e in sessions.values()) >= 4:
            raise HTTPException(429, 'End an active session before starting another.')
        from .worker import VoiceWorker, token
        sid = secrets.token_hex(16)
        worker = VoiceWorker(sid, bypass_cache=body.cache_mode == 'bypass')
        try:
            await asyncio.wait_for(worker.connect(), timeout=60)
        except Exception:
            await worker.close()
            raise HTTPException(503, 'Voice setup failed. Run the product preflight to check configuration and connectivity.') from None
        capability = secrets.token_urlsafe(32)
        sessions[sid] = {'worker': worker, 'secret': capability}
        return {'id': sid, 'capability': capability, 'url': os.environ['LIVEKIT_URL'],
                'token': token(worker.room_name, worker.identity), 'snapshot': worker.controller.snapshot()}


@app.get('/api/sessions/{sid}')
async def state(sid: str, request: Request):
    return entry_for(sid, request)['worker'].controller.snapshot()


@app.post('/api/sessions/{sid}/action')
async def action(sid: str, body: Action, request: Request):
    worker = entry_for(sid, request)['worker']
    if worker.closed and body.action != 'end':
        raise HTTPException(409, 'Session ended. Start a new session.')
    try:
        if body.action == 'start':
            await worker.start()
        elif body.action == 'end':
            await worker.close()
        elif body.action == 'recover':
            await worker.recover()
        elif body.action == 'connection_lost':
            await worker.runtime.failure('connection')
        elif body.action == 'hearing_difficulty':
            worker.runtime.report_difficulty('user_reported')
        else:
            if os.getenv('DATAFORGE_TEST_MODE') != '1':
                raise HTTPException(403, 'Failure injection is disabled.')
            if body.action == 'competing_speech_demo':
                worker.runtime.report_difficulty('demo_injected')
            elif body.action == 'fail_next_synthesis':
                worker.audio.fail_next = True
            else:
                category = 'speech_provider' if body.action == 'speech_failure' else 'recognition'
                await worker.runtime.failure(category)
    except ValueError as error:
        raise HTTPException(409, str(error)) from None
    return worker.controller.snapshot()


@app.get('/api/sessions/{sid}/evidence')
async def evidence(sid: str, request: Request):
    return entry_for(sid, request)['worker'].evidence()
