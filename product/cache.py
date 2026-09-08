"""Atomic content-addressed PCM cache; no experiment cache imports."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import uuid
from pathlib import Path


class AudioCache:
    def __init__(self, root: Path):
        self.root = root

    @staticmethod
    def key(text: str, config: dict):
        payload = json.dumps({'text': text, 'config': config}, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, text: str, config: dict) -> bytes | None:
        key = self.key(text, config)
        try:
            record = json.loads((self.root / f'{key}.json').read_text())
            data = base64.b64decode(record['audio'], validate=True)
            if (record['key'] != key or record['complete'] is not True or not data or len(data) % 2
                    or hashlib.sha256(data).hexdigest() != record['sha256']):
                return None
            return data
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def put(self, text: str, config: dict, data: bytes):
        if not data or len(data) % 2:
            raise ValueError('A complete, nonempty 16-bit PCM buffer is required.')
        key = self.key(text, config)
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.root / f'{key}.{uuid.uuid4().hex}.tmp'
        record = {'schema': 1, 'key': key, 'complete': True,
                  'sha256': hashlib.sha256(data).hexdigest(),
                  'audio': base64.b64encode(data).decode()}
        try:
            temporary.write_text(json.dumps(record), encoding='utf-8')
            os.replace(temporary, self.root / f'{key}.json')
        finally:
            temporary.unlink(missing_ok=True)
