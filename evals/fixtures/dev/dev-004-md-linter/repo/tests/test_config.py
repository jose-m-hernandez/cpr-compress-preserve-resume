import os
import tempfile
import unittest

from mdcheck.errors import ConfigError
from mdcheck.runner import load_config


class LoadConfigTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def write(self, text, name=".mdcheck.json"):
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_reads_rule_names(self):
        path = self.write('{"rules": ["no-tabs", "line-length"]}')
        self.assertEqual(load_config(path), ["no-tabs", "line-length"])

    def test_empty_rule_list(self):
        self.assertEqual(load_config(self.write('{"rules": []}')), [])

    def test_missing_file(self):
        missing = os.path.join(self.directory.name, ".mdcheck.json")
        with self.assertRaisesRegex(ConfigError, "cannot read config"):
            load_config(missing)

    def test_invalid_json(self):
        with self.assertRaisesRegex(ConfigError, "invalid JSON"):
            load_config(self.write("{not json"))

    def test_wrong_shape(self):
        for text in ("[]", "{}", '{"rules": "no-tabs"}', '{"rules": [1]}', '{"rules": null}'):
            with self.subTest(text=text), self.assertRaisesRegex(ConfigError, "must look like"):
                load_config(self.write(text))


if __name__ == "__main__":
    unittest.main()
