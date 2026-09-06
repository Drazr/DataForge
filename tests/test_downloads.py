import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from dataforge.downloads import prepare_models


class ModelLockTests(unittest.TestCase):
    def test_resolved_configuration_can_be_prepared_again(self):
        api = MagicMock()
        api.model_info.return_value.sha = "immutable-asr-sha"
        hub = SimpleNamespace(HfApi=MagicMock(return_value=api),
                              snapshot_download=MagicMock(return_value="/cached/asr"))
        response = MagicMock()
        response.json.return_value = {"sha": "immutable-dnsmos-sha"}
        config = {"asr_repo": "example/asr", "asr_revision": "main", "dnsmos_enabled": False}
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict("sys.modules", {"huggingface_hub": hub}), \
             patch("dataforge.downloads.requests.get", return_value=response):
            first = prepare_models(config, directory)
            second = prepare_models(first, directory)
            self.assertEqual(first, second)
            self.assertEqual(config["asr_revision"], "main")
            api.model_info.assert_called_once()
            self.assertTrue((Path(directory) / "model_lock.json").exists())
            for changed in (config | {"asr_revision": "other"}, first | {"asr_repo": "other/repo"}):
                with self.assertRaisesRegex(ValueError, "lock differs"):
                    prepare_models(changed, directory)


if __name__ == "__main__":
    unittest.main()
