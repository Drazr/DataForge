"""Audit supplied grid artifacts and preserve a disclosed offline policy session.

Run: python -m product.evidence_audit
No model calls, live transport, or human-comprehension measurements are made.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--product-root', required=True, help='Path to the final-product checkout')
args = parser.parse_args()
sys.path.insert(0, str(Path(args.product_root).resolve()))
from product.core import Controller

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def audit():
    directory = ROOT / 'evidence/noise-grid-v2'
    imported = directory / 'imported'
    record = json.loads((imported / 'results/analysis_record.json').read_text())
    with (imported / 'results/selected_observations.csv').open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == record['selected_rows'] == record['expected_rows'] == 294
    assert record['missing_rows'] == record['supported_metric_intervals'] == 0
    assert len({row['clip_id'] for row in rows}) == 294
    assert all(row['run_id'] == record['run_id'] and row['split'] == 'dev' for row in rows)
    clips = []
    for path in sorted((imported / 'audio').glob('*.wav')):
        row = next(row for row in rows if row['clip_id'] == path.stem)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == row['audio_sha256'], f'Audio hash mismatch: {path.name}'
        clips.append({'path': path.relative_to(directory).as_posix(), 'sha256': digest,
                      **{key: row[key] for key in ('text_id', 'replicate', 'condition', 'transcript',
                         'reference_text', 'noise_sha256', 'noise_file', 'noise_offset_s',
                         'model_id', 'speaker', 'transport', 'noise_placement')},
                      'fact_recovery': float(row['fact_recovery']), 'wer': float(row['wer'])})
    assert len(clips) == 3
    write(directory / 'stress_case.json', {
        'schema': 1, 'producer_run_id': record['run_id'],
        'scope': 'Selected offline listening stress case; not a live product detector session',
        'selection': 'Post-hoc illustrative clean/5 dB/-5 dB pair for critical_01 replicate 0; not representative alone',
        'clips': clips,
        'disclosure': 'Noise was mixed after the simulated phone codec. Scores are saved ASR proxies. Product uses a different voice and WebRTC/Opus.',
        'source_attribution': 'Rime Coda/Celeste target speech; MUSAN speech_2 background source path/hash in each noisy clip record. Original corpus attribution/license must accompany redistribution.',
    })
    manifest = json.loads((directory / 'provenance.json').read_text())
    manifest['full_exports_supplied'] = True
    manifest['missing_from_package'] = ['Original producer manifest.json (hash supplied)',
                                        'Full producer audio set and synthesis cache (only three selected WAVs supplied)']
    manifest['imported_artifacts'] = [
        {'path': p.relative_to(directory).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted(imported.rglob('*')) if p.is_file()]
    manifest['limitations'] = ['Full analysis CSVs and confidence fields are supplied; original pastes remain unchanged.',
                               'Selected WAV hashes match saved observations; scores have not been recomputed.',
                               'No live product performance or human-comprehension result is inferred.']
    write(directory / 'provenance.json', manifest)

    # Scripted text inputs verify the policy independently of ASR or audio quality.
    sessions = []
    for name, replies in [('correct_readback', ['D F four eight two one', 'nine twenty am', 'yes']),
                          ('incorrect_readback', ['D F four eight two two', 'yes'])]:
        controller = Controller(clock=lambda: 10.0)
        def play(segments):
            for segment in segments:
                assert controller.begin(segment, controller.generation)
                assert controller.complete(segment, controller.generation)
        play(controller.start())
        play(controller.report_difficulty('demo_injected'))
        for index, reply in enumerate(replies):
            play(controller.receive(reply, str(index), 10.0))
        assert controller.confirmed == (name == 'correct_readback')
        sessions.append({'name': name, 'snapshot': controller.snapshot(), 'events': controller.events})
    write(ROOT / 'evidence/product-policy/offline_sessions.json', {
        'scope': 'Offline software verification with scripted text and simulated playback completion',
        'live_transport': False, 'received_audio': None, 'detector_installed': False,
        'performance_claim': None, 'sessions': sessions})
    print('Audited 294 observations and 3 audio hashes; preserved 2 disclosed offline policy sessions.')


if __name__ == '__main__':
    audit()
