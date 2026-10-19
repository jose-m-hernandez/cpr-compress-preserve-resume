"""Assigning people to days."""
from rota.availability import DAYS

PER_DAY = 3  # people staffed on each day
MAX_SHIFTS = 3  # staff contract: no one works more than this many shifts a week


def can_work(name, people, day, shifts, max_shifts):
    """Return True if name is free on day and still under the weekly cap."""
    return day in people[name] and shifts.get(name, 0) < max_shifts


def pick_for_day(names, people, day, start, per_day, shifts, max_shifts=MAX_SHIFTS):
    """Return (picked, next_start) for one day.

    Walk `names` in order from index `start`, wrapping around, and take the
    first per_day people who are available on `day` and have fewer than
    max_shifts shifts so far in `shifts` (a {name: count} dict). next_start
    is the index just after the last person picked, or `start` if nobody
    was picked.
    """
    picked = []
    next_start = start
    for step in range(len(names)):
        if len(picked) == per_day:
            break
        index = (start + step) % len(names)
        if can_work(names[index], people, day, shifts, max_shifts):
            picked.append(names[index])
            next_start = (index + 1) % len(names)
    return picked, next_start


def assign(people, per_day=PER_DAY, max_shifts=MAX_SHIFTS):
    """Return {day: [names]} with up to per_day people on each day.

    People are taken round-robin in name order: each day carries on from
    the person after the last one picked, so the rota is the same every
    run and can be checked by hand. Nobody is given more than max_shifts
    shifts in the week; a day may be short-staffed as a result.
    """
    names = sorted(people)
    rota = {}
    shifts = {}
    start = 0
    for day in DAYS:
        rota[day], start = pick_for_day(
            names, people, day, start, per_day, shifts, max_shifts
        )
        for name in rota[day]:
            shifts[name] = shifts.get(name, 0) + 1
    return rota
