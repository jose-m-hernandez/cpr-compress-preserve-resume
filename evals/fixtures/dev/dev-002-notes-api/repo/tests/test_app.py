import os
import tempfile
import unittest

from notes_api import app
from notes_api.store import NoteStore


class GetNoteTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        app.STORE = NoteStore(os.path.join(self.dir.name, "notes.json"))
        self.addCleanup(setattr, app, "STORE", None)

    def test_dispatch_matches_v2_note_route(self):
        func, groups = app.dispatch("GET", "/v2/notes/7")
        self.assertIs(func, app.get_note)
        self.assertEqual(groups, ("7",))

    def test_dispatch_rejects_non_numeric_id(self):
        func, _ = app.dispatch("GET", "/v2/notes/abc")
        self.assertIsNone(func)

    def test_get_note_returns_the_note(self):
        note_id = app.STORE.add("hello", "body")
        status, payload = app.get_note(str(note_id))
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"id": note_id, "title": "hello", "body": "body"})

    def test_get_note_missing_is_404(self):
        status, payload = app.get_note("99")
        self.assertEqual(status, 404)
        self.assertEqual(payload, {"error": "not found"})


class DeleteNoteTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        app.STORE = NoteStore(os.path.join(self.dir.name, "notes.json"))
        self.addCleanup(setattr, app, "STORE", None)

    def test_dispatch_matches_v2_delete_route(self):
        func, groups = app.dispatch("DELETE", "/v2/notes/3")
        self.assertIs(func, app.delete_note)
        self.assertEqual(groups, ("3",))

    def test_delete_note_removes_it(self):
        note_id = app.STORE.add("hello", "body")
        status, payload = app.delete_note(str(note_id))
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"id": note_id, "deleted": True})
        self.assertIsNone(app.STORE.find(note_id))

    def test_delete_note_missing_is_404(self):
        status, payload = app.delete_note("99")
        self.assertEqual(status, 404)
        self.assertEqual(payload, {"error": "not found"})


if __name__ == "__main__":
    unittest.main()
