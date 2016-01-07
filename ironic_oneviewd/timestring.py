import re


def to_seconds(time_str):
    pattern = ("((?P<hours>[0-9]+)h)?((?P<minutes>[0-9]+)m)?"
               "((?P<seconds>[0-9]+)s)?")

    m = re.search(pattern, time_str)
    hours = m.group("hours")
    minutes = m.group("minutes")
    seconds = m.group("seconds")

    hours_in_secs = (int(hours or 0) * 60 * 60)
    minutes_in_secs = (int(minutes or 0) * 60)
    secs = int(seconds or 0)
    return hours_in_secs + minutes_in_secs + secs

