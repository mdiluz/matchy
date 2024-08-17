"""
All the possible strings for things that matchy can say
Some can be selected randomly to give the bot some flavor
"""
from matchy.util import randomised, datetime_as_discord_time, format_list
from matchy.state import AuthScope


# Acknowledge something
@randomised
def acknowledgement(m): return [
    f"Roger roger {m}!",
    f"Sure thing {m}!"
]


def user_added(c):
    return f"Added you to {c}!"


def user_leave(m):
    return f"No worries {m}. Come back soon :)"


def paused(t):
    return f"Paused you until {datetime_as_discord_time(t)}!"


def active_matchees(ms):
    return f"There are {len(ms)} active matchees:\n{format_list(ms)}"


def paused_matchees(ms):
    return f"There are {len(ms)} paused matchees:\n{format_list(ms)}"


def scheduled(next, n):
    return f"A match is scheduled at {datetime_as_discord_time(next)} with {n} members per group\n"


def no_scheduled():
    return "There are no matchees in this channel and no scheduled matches :("


def need_matcher_scope():
    return "You'll need the 'matcher' scope to do this"


def scheduled_success(d):
    return f"Done :) Next run will be at {datetime_as_discord_time(d)}"


def cancelled():
    return "Done, all scheduled matches cleared in this channel!"


def nobody_to_match():
    return "Nobody to match up :("


def generated_groups(g):
    return "Roger! I've generated example groups for ya:\n\n{g}"


def click_to_match():
    return "Click the button to match up groups and send them to the channel."


def need_matcher_to_post():
    return f"You'll need the {AuthScope.MATCHER} scope to post this to the channel, sorry!"


def reminder():
    return """Arf arf! just a reminder I'll be doin a matcherino in here in T-24hrs!
Use /join if you haven't already, or /pause if you want to skip a week :)"""


def matching():
    return "Matchy is matching matchees..."


def matching_done():
    return "That's all folks, happy matching and remember - DFTBA!"
