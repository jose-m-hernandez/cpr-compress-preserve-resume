import unittest

from metrics.app import handle
from metrics.registry import Registry


class AppTests(unittest.TestCase):
    def test_metrics_path_serves_text(self):
        registry = Registry()
        registry.counter("a_total").add(1)
        self.assertEqual(handle("/-/metrics", registry), (200, "a_total 1\n"))

    def test_old_metrics_path_is_404(self):
        self.assertEqual(handle("/metrics", Registry())[0], 404)

    def test_unknown_path_is_404(self):
        self.assertEqual(handle("/other", Registry())[0], 404)


if __name__ == "__main__":
    unittest.main()
