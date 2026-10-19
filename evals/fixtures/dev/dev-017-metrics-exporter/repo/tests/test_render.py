import unittest

from metrics.registry import Registry
from metrics.render import render


def exact(*lines):
    """Return the expected text: each line followed by one newline, nothing else."""
    return "".join(f"{line}\n" for line in lines)


class RenderTests(unittest.TestCase):
    def test_empty_registry_renders_nothing(self):
        self.assertEqual(render(Registry()), "")

    def test_single_counter_is_one_exact_line(self):
        registry = Registry()
        registry.counter("a_total").add(3)
        self.assertEqual(render(registry), exact("a_total 3"))

    def test_lines_are_sorted_name_and_value(self):
        registry = Registry()
        registry.counter("b_total").add(1)
        registry.counter("a_total")
        registry.counter("b_total").add(1)
        self.assertEqual(render(registry), exact("a_total 0", "b_total 2"))

    def test_sorting_is_by_name_not_creation_or_value(self):
        registry = Registry()
        registry.counter("c_total").add(1)
        registry.counter("a_total").add(9)
        registry.counter("b_total").add(5)
        expected = exact("a_total 9", "b_total 5", "c_total 1")
        self.assertEqual(render(registry), expected)

    def test_multi_digit_value_is_not_padded(self):
        registry = Registry()
        registry.counter("a_total").add(1234)
        self.assertEqual(render(registry), exact("a_total 1234"))

    def test_no_stray_whitespace(self):
        registry = Registry()
        registry.counter("a_total").add(1)
        registry.counter("b_total").add(2)
        text = render(registry)
        self.assertTrue(text.endswith("a_total 1\nb_total 2\n"))
        self.assertEqual(text.split("\n")[-1], "")
        for line in text.splitlines():
            self.assertEqual(line, line.strip())
            self.assertEqual(len(line.split(" ")), 2)
        self.assertNotIn("\r", text)
        self.assertNotIn("\t", text)
        self.assertNotIn("\n\n", text)


if __name__ == "__main__":
    unittest.main()
