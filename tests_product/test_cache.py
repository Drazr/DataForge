import json
import pytest
from product.cache import AudioCache
from product.config import SpeechConfig


def test_exact_content_and_settings_required(tmp_path):
    cache = AudioCache(tmp_path)
    config = SpeechConfig().public()
    cache.put('time', config, b'\x01\x00' * 100)
    assert cache.get('time', config) is not None
    assert cache.get('changed time', config) is None
    for key, value in [('speaker', 'other'), ('sample_rate', 16000), ('time_scale_factor', 1.1), ('revision', 'other')]:
        assert cache.get('time', {**config, key: value}) is None


def test_incomplete_corrupt_and_tampered_audio_rejected(tmp_path):
    cache, config = AudioCache(tmp_path), SpeechConfig().public()
    for data in (b'', b'x'):
        with pytest.raises(ValueError):
            cache.put('text', config, data)
    cache.put('text', config, b'\x01\x00')
    path = tmp_path / (cache.key('text', config) + '.json')
    original = json.loads(path.read_text())
    for field, value in [('complete', False), ('sha256', 'incorrect'), ('audio', 'garbage')]:
        path.write_text(json.dumps({**original, field: value}))
        assert cache.get('text', config) is None
    path.write_text('{unfinished')
    assert cache.get('text', config) is None
