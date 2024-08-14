from datetime import datetime, timedelta


def get_day_with_suffix(day):
    """Get the suffix for a day of the month"""
    if 11 <= day <= 13:
        return str(day) + 'th'
    else:
        return str(day) + {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


def format_day(time: datetime) -> str:
    """Format the a given datetime"""
    num = get_day_with_suffix(time.day)
    day = time.strftime("%a")
    return f"{day} {num}"


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
    next_date.replace(hour=hour)

    return next_date