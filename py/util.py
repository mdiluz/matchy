from datetime import datetime


def get_day_with_suffix(day):
    """Get the suffix for a day of the month"""
    if 11 <= day <= 13:
        return str(day) + 'th'
    else:
        return str(day) + {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


def format_today():
    """Format the current datetime"""
    now = datetime.now()
    return f"{get_day_with_suffix(now.day)} {now.strftime("%B")}"


def format_list(list) -> str:
    """Format a list into a human readable format of foo, bar and bob"""
    if len(list) > 1:
        return f"{', '.join(list[:-1])} and {list[-1]}"
    return list[0] if list else ''
