from datetime import datetime, timedelta
from functools import reduce


def get_day_with_suffix(day):
    """Get the suffix for a day of the month"""
    if 11 <= day <= 13:
        return str(day) + 'th'
    else:
        return str(day) + {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


def format_list(list: list) -> str:
    """Format a list into a human readable format of foo, bar and bob"""
    if len(list) > 1:
        return f"{', '.join(list[:-1])} and {list[-1]}"
    return list[0] if list else ''


def get_next_datetime(weekday, hour) -> datetime:
    """Get the next datetime for the given weekday and hour"""
    now = datetime.now()
    days_until_next_week = (weekday - now.weekday() + 7) % 7

    # Account for when we're already beyond the time now
    if days_until_next_week == 0 and now.hour >= hour:
        days_until_next_week = 7

    # Calculate the next datetime
    next_date = now + timedelta(days=days_until_next_week)
    next_date = next_date.replace(hour=hour, minute=0, second=0, microsecond=0)

    return next_date


def datetime_as_discord_time(time: datetime) -> str:
    return f"<t:{int(time.timestamp())}>"


def iterate_all_shifts(list: list):
    """Yields each shifted variation of the input list"""
    yield list
    for _ in range(len(list)-1):
        list = list[1:] + [list[0]]
        yield list


def get_nested_value(d, *keys, default=None):
    """Helper method for walking down an optional set of nested dicts to get a value"""
    return reduce(lambda d, key: d.get(key, {}), keys, d) or default


def set_nested_value(d, *keys, value=None):
    """Helper method for walking down an optional set of nested dicts to set a value"""
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    leaf = keys[-1]
    if value is not None:
        d[leaf] = value
    elif leaf in d:
        del d[leaf]
