import os
import tempfile
import unittest

from notes_api.store import NoteStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.path = os.path.join(self.dir.name, "notes.json")

    def test_add_and_get(self):
        store = NoteStore(self.path)
        note_id = store.add("hello", "body")
        self.assertEqual(store.get(note_id)["title"], "hello")

    def test_add_rejects_title_over_max_length(self):
        store = NoteStore(self.path)
        with self.assertRaisesRegex(ValueError, "title too long"):
            store.add("x" * 100, "body")
        self.assertEqual(store.notes, {})
        self.assertFalse(os.path.exists(self.path))

    def test_find_returns_note_or_none(self):
        store = NoteStore(self.path)
        note_id = store.add("hello", "body")
        self.assertEqual(store.find(note_id)["title"], "hello")
        self.assertIsNone(store.find(note_id + 1))

    def test_delete_removes_note_and_persists(self):
        store = NoteStore(self.path)
        note_id = store.add("hello", "body")
        self.assertTrue(store.delete(note_id))
        self.assertIsNone(store.find(note_id))
        self.assertIsNone(NoteStore(self.path).find(note_id))

    def test_delete_missing_returns_false(self):
        self.assertFalse(NoteStore(self.path).delete(1))

    def test_notes_survive_a_reload(self):
        NoteStore(self.path).add("kept", "body")
        self.assertEqual(NoteStore(self.path).get(1)["title"], "kept")


if __name__ == "__main__":
    unittest.main()
