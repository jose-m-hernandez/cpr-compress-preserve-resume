import unittest

from router.events import parse_event


class ParseEventTests(unittest.TestCase):
    def test_reads_a_valid_event(self):
        self.assertEqual(parse_event('{"id": "a", "type": "t", "sent": 1}')["type"], "t")

    def test_legacy_kind_becomes_type(self):
        event = parse_event('{"id": "a", "kind": "t", "sent": 1}')
        self.assertEqual(event, {"id": "a", "type": "t", "sent": 1})

    def test_type_wins_over_legacy_kind(self):
        event = parse_event('{"id": "a", "type": "t", "kind": "old", "sent": 1}')
        self.assertEqual(event["type"], "t")

    def test_missing_field_is_named(self):
        with self.assertRaises(ValueError) as caught:
            parse_event('{"id": "a", "sent": 1}')
        self.assertIn("type", str(caught.exception))

    def test_bad_json_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_event("{")


if __name__ == "__main__":
    unittest.main()
