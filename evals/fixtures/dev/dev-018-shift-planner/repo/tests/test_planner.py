import unittest
from collections import Counter

from rota.availability import DAYS
from rota.planner import MAX_SHIFTS, PER_DAY, assign, can_work, pick_for_day


class PlannerTests(unittest.TestCase):
    def test_limits_people_per_day(self):
        people = {"a": {"mon"}, "b": {"mon"}, "c": {"mon"}, "d": {"mon"}}
        self.assertEqual(len(assign(people)["mon"]), 3)

    def test_empty_day_is_an_empty_list(self):
        self.assertEqual(assign({"a": {"mon"}})["tue"], [])

    def test_rotates_in_name_order(self):
        everyone = {"mon", "tue", "wed", "thu"}
        people = {n: everyone for n in ("dee", "cy", "ana", "bo")}
        rota = assign(people)
        self.assertEqual(rota["mon"], ["ana", "bo", "cy"])
        self.assertEqual(rota["tue"], ["dee", "ana", "bo"])
        self.assertEqual(rota["wed"], ["cy", "dee", "ana"])
        self.assertEqual(rota["thu"], ["bo", "cy", "dee"])

    def test_skips_unavailable_people_and_carries_on(self):
        people = {
            "ana": {"mon", "tue"},
            "bo": {"tue"},
            "cy": {"mon", "tue"},
            "dee": {"mon"},
        }
        rota = assign(people)
        self.assertEqual(rota["mon"], ["ana", "cy", "dee"])
        self.assertEqual(rota["tue"], ["ana", "bo", "cy"])

    def test_same_result_every_run(self):
        people = {n: {"mon", "tue", "wed"} for n in "edcba"}
        self.assertEqual(assign(people), assign(dict(reversed(list(people.items())))))

    def test_default_is_three_per_day(self):
        people = {n: {"mon"} for n in "abcde"}
        self.assertEqual(assign(people)["mon"], ["a", "b", "c"])
        self.assertEqual(PER_DAY, 3)

    def test_no_people_gives_empty_rota(self):
        self.assertEqual(assign({})["mon"], [])

    def test_pick_for_day_wraps_and_returns_next_start(self):
        people = {"a": {"mon"}, "b": {"mon"}, "c": {"mon"}}
        picked, next_start = pick_for_day(["a", "b", "c"], people, "mon", 2, 2, {})
        self.assertEqual(picked, ["c", "a"])
        self.assertEqual(next_start, 1)

    def test_pick_for_day_keeps_start_when_nobody_available(self):
        picked, next_start = pick_for_day(["a"], {"a": {"tue"}}, "mon", 0, 2, {})
        self.assertEqual((picked, next_start), ([], 0))

    def test_pick_for_day_skips_people_at_the_cap(self):
        people = {"a": {"mon"}, "b": {"mon"}, "c": {"mon"}}
        picked, _ = pick_for_day(["a", "b", "c"], people, "mon", 0, 2, {"a": 3}, 3)
        self.assertEqual(picked, ["b", "c"])

    def test_can_work_needs_availability_and_room_under_the_cap(self):
        people = {"a": {"mon"}}
        self.assertTrue(can_work("a", people, "mon", {"a": 2}, 3))
        self.assertFalse(can_work("a", people, "mon", {"a": 3}, 3))
        self.assertFalse(can_work("a", people, "tue", {}, 3))

    def test_contract_cap_is_three(self):
        self.assertEqual(MAX_SHIFTS, 3)

    def test_nobody_works_more_than_three_shifts(self):
        people = {"ana": set(DAYS), "bo": set(DAYS), "cy": set(DAYS)}
        counts = Counter(n for names in assign(people).values() for n in names)
        self.assertTrue(all(count <= MAX_SHIFTS for count in counts.values()))

    def test_lone_person_stops_at_three_shifts(self):
        rota = assign({"ana": set(DAYS)})
        self.assertEqual(rota["mon"], ["ana"])
        self.assertEqual(rota["wed"], ["ana"])
        self.assertEqual(rota["thu"], [])
        self.assertEqual(sum(len(names) for names in rota.values()), 3)

    def test_capped_person_is_replaced_by_the_next_in_line(self):
        people = {"ana": {"mon", "tue", "wed", "thu"}, "bo": {"thu"}}
        rota = assign(people, per_day=1, max_shifts=3)
        self.assertEqual(rota["wed"], ["ana"])
        self.assertEqual(rota["thu"], ["bo"])

    def test_max_shifts_can_be_overridden(self):
        rota = assign({"ana": set(DAYS)}, max_shifts=1)
        self.assertEqual(sum(len(names) for names in rota.values()), 1)


if __name__ == "__main__":
    unittest.main()
