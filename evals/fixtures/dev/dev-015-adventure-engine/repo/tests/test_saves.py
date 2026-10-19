import json
import os
import tempfile
import unittest
from unittest import mock

from adventure import saves
from helpers import play

WORLD = {"start": "a", "rooms": {
    "a": {"description": "Room A.", "exits": {"north": "b"}, "items": ["lamp", "key"]},
    "b": {"description": "Room B.", "exits": {"south": "a"}},
}}
OTHER = {"start": "z", "rooms": {"z": {"description": "Room Z."}}}


class SaveTestCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.dir = os.path.join(folder.name, "saves")
        patcher = mock.patch.object(saves, "SAVE_DIR", self.dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_save(self, name, text):
        os.makedirs(self.dir, exist_ok=True)
        with open(os.path.join(self.dir, name + ".json"), "w") as handle:
            handle.write(text)


class SaveTests(SaveTestCase):
    def test_save_writes_a_json_file(self):
        self.assertEqual(play(WORLD, ["go north", "save one"])[1], "Game saved: one.")
        with open(os.path.join(self.dir, "one.json")) as handle:
            self.assertEqual(json.load(handle)["room"], "b")

    def test_load_restores_room_inventory_and_items(self):
        play(WORLD, ["take lamp", "go north", "save one"])
        messages = play(WORLD, ["load one", "look", "go south", "take lamp", "take key"])
        self.assertEqual(messages, ["Game loaded: one.", "Room B.", "Room A.",
                                    "There is no lamp here.", "You take the key."])

    def test_load_replaces_progress_made_since_saving(self):
        messages = play(WORLD, ["save one", "take lamp", "go north", "load one", "look"])
        self.assertEqual(messages[3:], ["Game loaded: one.", "Room A."])

    def test_quit_is_immediate_after_saving(self):
        messages = play(WORLD, ["go north", "save one", "quit", "look"])
        self.assertEqual(messages[2:], ["Goodbye.", "The game has ended."])

    def test_quit_is_immediate_after_loading(self):
        play(WORLD, ["go north", "save one"])
        messages = play(WORLD, ["load one", "quit"])
        self.assertEqual(messages[1], "Goodbye.")

    def test_unsafe_names_are_rejected(self):
        for name in ("../evil", "a/b", "x.y"):
            message = play(WORLD, ["save " + name])[0]
            self.assertIn("letters", message)
        self.assertFalse(os.path.exists(self.dir))

    def test_load_missing_save(self):
        self.assertEqual(play(WORLD, ["load nope"]), ["No save called nope."])

    def test_load_damaged_save_changes_nothing(self):
        self.write_save("bad", "{not json")
        messages = play(WORLD, ["go north", "load bad", "look"])
        self.assertEqual(messages[1:], ["The save bad is damaged.", "Room B."])

    def test_load_save_missing_keys(self):
        self.write_save("thin", json.dumps({"room": "a"}))
        self.assertEqual(play(WORLD, ["load thin"]), ["The save thin is damaged."])

    def test_load_save_from_another_world(self):
        play(WORLD, ["save one"])
        messages = play(OTHER, ["load one", "look"])
        self.assertEqual(messages, ["The save one does not fit this world.", "Room Z."])


if __name__ == "__main__":
    unittest.main()
