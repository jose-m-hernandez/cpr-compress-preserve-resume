import unittest

from metrics.registry import Registry


class RegistryTests(unittest.TestCase):
    def test_counter_counts(self):
        registry = Registry()
        registry.counter("a_total").add(1)
        registry.counter("a_total").add(1)
        self.assertEqual(registry.counter("a_total").value, 2)

    def test_add_adds_n(self):
        counter = Registry().counter("a_total")
        counter.add(5)
        self.assertEqual(counter.value, 5)

    def test_add_rejects_negative(self):
        with self.assertRaises(ValueError):
            Registry().counter("a_total").add(-1)

    def test_counters_are_sorted(self):
        registry = Registry()
        registry.counter("b_total")
        registry.counter("a_total")
        self.assertEqual([c.name for c in registry.counters()], ["a_total", "b_total"])

    def test_name_with_brace_is_rejected(self):
        registry = Registry()
        with self.assertRaises(ValueError):
            registry.counter('hits_total{path="/"}')
        self.assertEqual(registry.counters(), [])

    def test_dimension_joined_with_underscores_is_accepted(self):
        Registry().counter("hits_get_total")


if __name__ == "__main__":
    unittest.main()
