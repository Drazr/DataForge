import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf

from dataforge.delivery import start_delivery
from dataforge.experiment import Experiment, load_corpus
from dataforge.handoff import copy_run

ROOT = Path(__file__).resolve().parents[1]


class DeliveryImportTests(unittest.TestCase):
    def test_imported_baseline_survives_source_move_without_new_inference(self):
        try:
            import imageio_ffmpeg
            os.environ["FFMPEG_BINARY"] = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError:
            pass
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            noise = root / "noise.wav"
            sf.write(noise, np.random.default_rng(2).normal(0, 0.03, 8000), 8000)
            config = json.loads((ROOT / "experiment.json").read_text()) | {"snrs_db": [5]}
            corpus = load_corpus(ROOT / "fixtures/corpus.json")[:1]
            sources = [{"id": name, "path": str(noise), "offset_s": 0, "verified_by_listening": True}
                       for name in ("speech", "environment")]
            producer = Experiment(config, corpus, sources, root / "producer")
            audio = io.BytesIO()
            sf.write(audio, 0.1 * np.sin(np.arange(24000)), 24000, format="WAV")
            with patch("dataforge.experiment.request_audio", return_value=(audio.getvalue(), {"client_first_chunk_s": 0.1})) as post, \
                 patch.object(producer, "transcribe", return_value=corpus[0]["text"]), \
                 patch.object(producer, "quality", return_value={"dnsmos_sig": 3.5, "dnsmos_bak": 3.5, "dnsmos_ovrl": 3.5}):
                baseline = producer.run("dev", ["baseline"], "TEST_ONLY")
                from dataforge.reporting import export_baseline
                export_baseline(baseline, producer.root, 2)
                copied = copy_run(producer.root, root / "consumer-checkout/inputs", for_delivery=True)
                (root / "producer").rename(root / "archived-producer")
                imported = start_delivery(copied, root / "delivery-output")
                self.assertEqual(post.call_count, 2)
                self.assertEqual(imported.fingerprint, producer.fingerprint)
                frame = imported.all_results("dev")
                self.assertEqual(len(frame), len(baseline))
                self.assertTrue(all(Path(p).is_file() for p in frame.audio_path))
                self.assertTrue(all(Path(p).is_file() for p in frame.source_audio))
                ledger = json.loads(imported.ledger_path.read_text())
                ledger.append({"cache_id": "later-ab-request", "characters": 1})
                imported.ledger_path.write_text(json.dumps(ledger))
                resumed = start_delivery(copied, root / "delivery-output")
                self.assertEqual(len(json.loads(resumed.ledger_path.read_text())), 3)
                imported.synthesize(corpus[0], "baseline", 0, "TEST_ONLY")
                self.assertEqual(post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
