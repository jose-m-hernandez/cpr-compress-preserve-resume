import unittest

from plugins.registry import PluginNotFound, Registry


class RegistryTests(unittest.TestCase):
    def test_get_builds_the_plugin(self):
        registry = Registry()
        registry.register("a", lambda: 42)
        self.assertEqual(registry.get("a"), 42)

    def test_get_raises_plugin_not_found_for_a_missing_plugin(self):
        with self.assertRaises(PluginNotFound) as caught:
            Registry().get("csv-export")
        self.assertIn("csv-export", str(caught.exception))

    def test_kebab_case_name_is_accepted(self):
        registry = Registry()
        registry.register("csv-export", lambda: 1)
        self.assertEqual(registry.get("csv-export"), 1)

    def test_name_must_be_lowercase_kebab_case(self):
        registry = Registry()
        for name in ["CSV-export", "csv_export", "csv export", "-csv", "csv-", "csv--export", ""]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    registry.register(name, object)

    def test_repeated_name_is_an_error(self):
        registry = Registry()
        registry.register("a", object)
        with self.assertRaises(ValueError):
            registry.register("a", object)

    def test_names_are_sorted(self):
        registry = Registry()
        registry.register("b", object)
        registry.register("a", object)
        self.assertEqual(registry.names(), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
