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
    f"Sure thing {m}!",
    f"o7 {m}!",
    f"Yessir {m}!",
    f"Bork {m}!",
]


@randomised
def user_added(c): return [
    f"Added you to {c}!",
    f"You've joined the matchee list on {c}!",
    f"Awesome, great to have you on board in {c}!",
    f"Bark bork bork arf {c} bork!",
]


@randomised
def user_leave(m): return [
    f"No worries {m}. Come back soon :)",
    f"That's cool {m}. Home you'll be back some day",
    f"Cool cool {m}. Be well!",
    f"Byeeee {m}!",
]


@randomised
def paused(t): return [
    f"Paused you until {datetime_as_discord_time(t)}!",
    f"You've been paused until {datetime_as_discord_time(t)}! Bork!",
    f"Okie dokie you'll be unpaused at {datetime_as_discord_time(t)}!",
    f"Bork bork bork arf {datetime_as_discord_time(t)}! Arf bork arf arf.",
]


@randomised
def active_matchees(ms): return [
    f"There are {len(ms)} active matchees:\n{format_list(ms)}",
    f"We've got {len(ms)} matchees here!\n{format_list(ms)}",
]


@randomised
def paused_matchees(ms): return [
    f"There are {len(ms)} paused matchees:\n{format_list(ms)}",
    f"Only {len(ms)} matchees are paused:\n{format_list(ms)}",
]


@randomised
def scheduled(next, n): return [
    f"""A match is scheduled at {datetime_as_discord_time(next)} \
with {n} members per group""",
    f"""There'll be a match at {datetime_as_discord_time(next)} \
with min {n} per group""",
    f"""At {datetime_as_discord_time(next)} I'll match \
groups of minimum {n}""",
]


@randomised
def no_scheduled(): return [
    "There are no matchees in this channel and no scheduled matches :(",
    "This channel's got nothing, bork!",
    "Arf bork no matchees or schedules here bark bork",
]


@randomised
def need_matcher_scope(): return [
    f"You'll need the '{AuthScope.MATCHER}' scope to do this",
    f"Only folks with the '{AuthScope.MATCHER}' scope can do this",
]


@randomised
def scheduled_success(d): return [
    f"Done :) Next run will be at {datetime_as_discord_time(d)}",
    f"Woohoo! Scheduled for {datetime_as_discord_time(d)}",
    f"Yessir, will do a matcho at {datetime_as_discord_time(d)}",
    f"Arf Arf! Bork bork bark {datetime_as_discord_time(d)}",
]


@randomised
def cancelled(): return [
    "Done, all scheduled matches cleared in this channel!",
    "See ya later schedulaters",
    "Okie dokey, schedule cleared",
]


@randomised
def nobody_to_match(): return [
    "Nobody to match up :(",
    "Arf orf... no matchees found...",
    "Couldn't find any matchees in this channel, sorry!",
]


@randomised
def generated_groups(g): return [
    f"Roger! I've generated example groups for ya:\n\n{g}",
    f"Sure thing! Some example groups:\n\n{g}",
    f"Yessir! The groups might look like:\n\n{g}",
]


@randomised
def click_to_match(): return [
    "Click the button to match up groups and send them to the channel.",
    "Bonk the button to do a match.",
    "Arf borf bork button bark press bork",
]


@randomised
def need_matcher_to_post(): return [
    f"""You'll need the '{AuthScope.MATCHER}' \
scope to post this to the channel, sorry!""",
    f"""You can't send this to the channel without \
the '{AuthScope.MATCHER}' scope.""",
]


@randomised
def reminder(): return [
    """Arf arf! just a reminder I'll be doin a matcherino in here in T-24hrs!
Use /join if you haven't already, or /pause if you want to skip a week :)""",
    """Bork! In T-24hrs there'll be a matchy match in this channel
Use /join to get in on the fun, or /pause need to take a break!""",
    """Woof! Your friendly neighbourhood matchy reminder here for tomorrow!
Make sure you're /pause'd if you need to be, or /join in ASAP!""",
]


@randomised
def matching(): return [
    "Matchy is matching matchees...",
    "Matchy is matching matchees!",
    "Matchy is doin a match!",
    "Matchy Match!",
]


@randomised
def matching_done(): return [
    "That's all folks, happy matching and remember - DFTBA!",
    "Aaand that's it, enjoy and vibe, you've earned it!",
    "Until next time frendos.",
]


@randomised
def matched_up(ms): return [
    f"Matched up {format_list(ms)}!",
    f"Hey {format_list(ms)}, have a good match!",
    f"Ahoy {format_list(ms)}, y'all be good :)",
    f"Sweet! {format_list(ms)} are a group!",
    f"Arf arf {format_list(ms)} bork bork arf!",
    f"{format_list(ms)}, y'all are the best!",
    f"{format_list(ms)}, DFTBA!",
]


@randomised
def thread_title(ms): return [
    f"{format_list(ms)}",
]
