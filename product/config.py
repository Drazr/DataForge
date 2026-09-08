from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_URL = 'https://users.rime.ai/data/voices/all-v2.json'


@dataclass(frozen=True)
class SpeechConfig:
    model: str = 'coda'
    speaker: str = 'astra'
    language: str = 'eng'
    endpoint: str = 'https://users.rime.ai/v1/rime-tts'
    sample_rate: int = 24000
    time_scale_factor: float = 1.0
    format: str = 'pcm_s16le_mono'
    provider: str = 'Rime'
    revision: str = 'plain-v1'

    @classmethod
    def from_env(cls):
        return cls(speaker=os.getenv('RIME_SPEAKER', 'astra'))

    def public(self):
        return asdict(self)


def missing_credentials():
    return [k for k in ('RIME_API_KEY', 'LIVEKIT_URL', 'LIVEKIT_API_KEY', 'LIVEKIT_API_SECRET')
            if not os.getenv(k) or os.getenv(k, '').startswith(('your-', 'replace-'))]


async def validate_catalog(config: SpeechConfig):
    import hashlib
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(CATALOG_URL)
        response.raise_for_status()
    catalog = response.json()
    if config.speaker not in catalog.get(config.model, {}).get(config.language, []):
        raise ValueError('Configured Rime model/voice/language is absent from the live catalog.')
    return {'url': CATALOG_URL, 'sha256': hashlib.sha256(response.content).hexdigest(),
            'configuration': config.public()}
