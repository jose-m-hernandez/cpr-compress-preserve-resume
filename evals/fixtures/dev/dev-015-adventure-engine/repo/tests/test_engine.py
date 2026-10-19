import unittest

from adventure.engine import step
from adventure.state import GameState
from helpers import play

ITEMS = ["lamp", "key", "rope", "map", "coin", "flask", "bell"]
FULL = {"start": "a", "rooms": {"a": {"description": "Room A.", "items": ITEMS}}}
TAKE_SIX = [f"take {item}" for item in ITEMS[:6]]

WORLD = {"start": "a", "rooms": {
    "a": {"description": "Room A.", "exits": {"north": "b"}, "items": ["lamp"]},
    "b": {"description": "Room B.", "exits": {"south": "a"}},
}}


class EngineTests(unittest.TestCase):
    def test_go_moves_the_player(self):
        state = GameState("a")
        step(WORLD, state, "go north")
        self.assertEqual(state.room, "b")

    def test_take_adds_to_inventory(self):
        state = GameState("a")
        step({"rooms": {"a": {"description": "x", "items": ["lamp"]}}}, state, "take lamp")
        self.assertEqual(state.inventory, ["lamp"])

    def test_sixth_item_is_allowed(self):
        self.assertEqual(play(FULL, TAKE_SIX)[5], "You take the flask.")

    def test_seventh_item_is_refused_and_stays_in_the_room(self):
        messages = play(FULL, TAKE_SIX + ["take bell", "take bell"])
        self.assertEqual(messages[6:], ["Your hands are full."] * 2)

    def test_drop_leaves_the_item_in_the_current_room(self):
        messages = play(WORLD, ["take lamp", "go north", "drop lamp",
                                "take lamp", "go south", "take lamp"])
        self.assertEqual(messages[2:4], ["You drop the lamp.", "You take the lamp."])
        self.assertEqual(messages[5], "There is no lamp here.")

    def test_drop_something_not_carried(self):
        self.assertEqual(play(WORLD, ["drop lamp"]), ["You aren't carrying a lamp."])

    def test_drop_makes_room_when_hands_are_full(self):
        messages = play(FULL, TAKE_SIX + ["take bell", "drop map", "take bell"])
        self.assertEqual(messages[6], "Your hands are full.")
        self.assertEqual(messages[8], "You take the bell.")

    def test_quit_with_nothing_done_quits_straight_away(self):
        self.assertEqual(play(WORLD, ["quit", "look"]),
                         ["Goodbye.", "The game has ended."])

    def test_quit_after_looking_only_quits_straight_away(self):
        self.assertEqual(play(WORLD, ["look", "quit"])[1], "Goodbye.")

    def test_quit_with_unsaved_moves_asks_first(self):
        for move in ("go north", "take lamp"):
            self.assertIn("Really quit?", play(WORLD, [move, "quit"])[1])

    def test_yes_confirms_the_quit(self):
        messages = play(WORLD, ["go north", "quit", "yes", "look"])
        self.assertEqual(messages[2:], ["Goodbye.", "The game has ended."])

    def test_no_cancels_the_quit(self):
        messages = play(WORLD, ["go north", "quit", "no", "look", "yes"])
        self.assertEqual(messages[2:], ["Quit cancelled.", "Room B.",
                                        "I don't understand."])

    def test_other_command_cancels_the_quit_and_runs(self):
        messages = play(WORLD, ["go north", "quit", "look", "yes"])
        self.assertEqual(messages[2:], ["Room B.", "I don't understand."])

    def test_deprecated_inspect_acts_like_look(self):
        self.assertEqual(play(WORLD, ["inspect"]), play(WORLD, ["look"]))
        self.assertEqual(play(WORLD, ["inspect"]), ["Room A."])

    def test_unknown_command(self):
        self.assertEqual(step(WORLD, GameState("a"), "dance"), "I don't understand.")


if __name__ == "__main__":
    unittest.main()
