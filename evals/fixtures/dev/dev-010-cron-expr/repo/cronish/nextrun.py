"""Finding the next time a schedule fires."""
from datetime import timedelta


def cron_weekday(moment):
    """Return the weekday of a datetime using the cron numbering (Sunday is 0)."""
    return (moment.weekday() + 1) % 7


def next_run(schedule, after):
    """Return the first matching minute strictly after `after`.

    The result has no seconds or microseconds and keeps the tzinfo of `after`.
    """
    if not (schedule.minutes and schedule.hours and schedule.weekdays):
        raise ValueError("schedule has an empty field and never fires")
    moment = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    while True:
        if cron_weekday(moment) not in schedule.weekdays:
            moment = moment.replace(hour=0, minute=0) + timedelta(days=1)
        elif moment.hour not in schedule.hours:
            moment = moment.replace(minute=0) + timedelta(hours=1)
        elif moment.minute not in schedule.minutes:
            moment += timedelta(minutes=1)
        else:
            return moment
