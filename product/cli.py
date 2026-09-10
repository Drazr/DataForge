"""Reproducible commands; no synthetic success when credentials are absent."""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
import wave
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from .config import ROOT, SpeechConfig, missing_credentials, validate_catalog


async def preflight():
    from .worker import VoiceWorker
    from livekit.plugins import silero
    silero.VAD.load()
    missing = missing_credentials()
    report = {'schema':1, 'sdk':'ready', 'credentials':'missing' if missing else 'configured',
              'missing':missing, 'speech':SpeechConfig.from_env().public(), 'live_verification':'not_run'}
    if missing:
        return report, 2
    report['catalog'] = await validate_catalog(SpeechConfig.from_env())
    return report, 0


async def fixtures():
    import aiohttp
    from .audio import RimeAudio
    from .cache import AudioCache
    directory=ROOT / 'evidence' / 'caller-fixtures'
    directory.mkdir(parents=True,exist_ok=True)
    config=SpeechConfig.from_env()
    await validate_catalog(config)
    phrases={'yes':'Yes, I confirm.', 'repeat':'Repeat the time.', 'no':'No thank you.', 'stop':'Stop.',
             'reference':'D F four eight two one.', 'time':'Nine twenty A M.',
             'wrong_reference':'D F four eight two two.'}
    hashes={}
    async with aiohttp.ClientSession() as http:
        audio=RimeAudio(config,AudioCache(ROOT/'.product-cache'/'caller-fixtures'),http)
        try:
            for name,text in phrases.items():
                pcm=await audio.render(text)
                with wave.open(str(directory/f'{name}.wav'),'wb') as output:
                    output.setparams((1,2,config.sample_rate,0,'NONE','not compressed'))
                    output.writeframes(pcm)
                hashes[name+'.wav']=hashlib.sha256((directory/f'{name}.wav').read_bytes()).hexdigest()
        finally:
            await audio.close()
    (directory/'manifest.json').write_text(json.dumps({'synthetic_caller':True,'provider':config.public(),'phrases':phrases,'sha256':hashes},indent=2))


def main():
    load_dotenv(ROOT/'.env')
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['preflight','test','live','export'])
    parser.add_argument('--session')
    parser.add_argument('--capability', help='Prefer DATAFORGE_SESSION_CAPABILITY environment variable.')
    parser.add_argument('--output',default=str(ROOT/'evidence'/'session.json'))
    parser.add_argument('--focus', choices=['all', 'speech-facts'], default='all')
    args=parser.parse_args()
    if args.command=='test':
        raise SystemExit(subprocess.call([sys.executable,'-m','pytest','tests_product','-q'],cwd=ROOT))
    if args.command=='export':
        import os
        import httpx
        capability=args.capability or os.getenv('DATAFORGE_SESSION_CAPABILITY')
        if not args.session or not capability: parser.error('Export requires --session and a session capability.')
        response=httpx.get(f'http://127.0.0.1:8000/api/sessions/{args.session}/evidence',headers={'Authorization':f'Bearer {capability}'})
        response.raise_for_status()
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(response.json(),indent=2),encoding='utf-8')
        print(f'Evidence exported to {output}')
        return
    if args.command=='live':
        evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
        status={'status':'running','run_id':uuid.uuid4().hex,
                'started_at':datetime.now(timezone.utc).isoformat(), 'stage':'preflight'}
        status_path=evidence/'live-status.json'
        def save_status():
            temporary=status_path.with_suffix('.tmp')
            temporary.write_text(json.dumps(status,indent=2),encoding='utf-8')
            temporary.replace(status_path)
        save_status()  # invalidate earlier success before any fallible live work
    try:
        report,code=asyncio.run(preflight())
    except KeyboardInterrupt:
        report,code={'status':'interrupted','live_verification':'not_run'},130
    except Exception as error:
        report,code={'status':'preflight_failed','error_type':type(error).__name__,'live_verification':'not_run'},1
    print(json.dumps(report,indent=2))
    if args.command=='preflight': raise SystemExit(code)
    if code:
        status.update(configuration=report, status='interrupted' if code==130 else 'unverified',
                      finished_at=datetime.now(timezone.utc).isoformat())
        save_status()
        raise SystemExit(code)
    status.update(configuration=report,stage='caller_fixtures')
    save_status()
    try:
        asyncio.run(fixtures())
        status['stage']='browser_verification'
        save_status()
        from shutil import which
        pnpm=which('pnpm') or str(Path(sys.base_prefix).parent/'bin'/'fallback'/'pnpm.cmd')
        command=[pnpm,'exec','playwright','test','--config','playwright.live.config.ts']
        if args.focus == 'speech-facts':
            command += ['--grep', 'normal confirmation|reported hearing difficulty|wrong critical']
        result=subprocess.call(command,cwd=ROOT/'web')
        status['status']='passed' if result==0 else 'failed'
    except KeyboardInterrupt:
        result=130
        status['status']='interrupted'
    except Exception as error:
        result=1
        status.update(status='failed',error_type=type(error).__name__)
    status['finished_at']=datetime.now(timezone.utc).isoformat()
    save_status()
    print(json.dumps(status,indent=2))
    raise SystemExit(result)


if __name__=='__main__':
    main()
