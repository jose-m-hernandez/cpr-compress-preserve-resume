"""A tiny file-backed note store."""
import json
import os

from notes_api.validation import validate_title


class NoteStore:
    def __init__(self, path):
        self.path = path
        self.notes = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                self.notes = {int(key): value for key, value in json.load(handle).items()}

    def add(self, title, body):
        validate_title(title)
        note_id = max(self.notes, default=0) + 1
        self.notes[note_id] = {"title": title, "body": body}
        self._save()
        return note_id

    def get(self, note_id):
        return self.notes[note_id]

    def find(self, note_id):
        """Return the note with this id, or None if there is none."""
        return self.notes.get(note_id)

    def delete(self, note_id):
        """Remove the note with this id. Return False if there is none."""
        if note_id not in self.notes:
            return False
        del self.notes[note_id]
        self._save()
        return True

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self.notes, handle)
