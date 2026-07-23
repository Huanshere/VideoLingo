import importlib
import os
import sys
import types
import unittest


def _install_ruamel_yaml_stub():
    yaml_module = types.ModuleType("ruamel.yaml")

    class YAML:
        preserve_quotes = False

        def load(self, *args, **kwargs):
            raise AssertionError("YAML.load should not be used in these tests")

        def dump(self, *args, **kwargs):
            raise AssertionError("YAML.dump should not be used in these tests")

    yaml_module.YAML = YAML
    ruamel_module = types.ModuleType("ruamel")
    ruamel_module.yaml = yaml_module
    sys.modules.setdefault("ruamel", ruamel_module)
    sys.modules.setdefault("ruamel.yaml", yaml_module)


class AtlasCloudConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _install_ruamel_yaml_stub()
        cls.config_utils = importlib.import_module("core.utils.config_utils")

    def tearDown(self):
        for env_key in self.config_utils.ATLAS_CLOUD_ENV_KEYS:
            os.environ.pop(env_key, None)

    def test_detects_atlascloud_base_url(self):
        self.assertTrue(
            self.config_utils.is_atlascloud_base_url("https://api.atlascloud.ai/v1")
        )
        self.assertFalse(self.config_utils.is_atlascloud_base_url("https://api.openai.com/v1"))

    def test_resolves_named_atlascloud_env_key(self):
        os.environ["ATLASCLOUD_API_KEY"] = "atlas-test-key"

        api_key = self.config_utils.resolve_api_key(
            "ATLASCLOUD_API_KEY",
            base_url=self.config_utils.ATLAS_CLOUD_API_BASE,
        )

        self.assertEqual(api_key, "atlas-test-key")

    def test_resolves_placeholder_key_for_atlascloud_base_url(self):
        os.environ["ATLAS_CLOUD_API_KEY"] = "atlas-secondary-key"

        api_key = self.config_utils.resolve_api_key(
            "YOUR_API_KEY",
            base_url=self.config_utils.ATLAS_CLOUD_API_BASE,
        )

        self.assertEqual(api_key, "atlas-secondary-key")

    def test_keeps_explicit_non_atlas_key(self):
        api_key = self.config_utils.resolve_api_key(
            "explicit-key",
            base_url="https://api.openai.com/v1",
        )

        self.assertEqual(api_key, "explicit-key")


if __name__ == "__main__":
    unittest.main()
