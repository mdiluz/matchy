# Matchy
Matchy matches matchees.

![Tests](https://github.com/mdiluz/matchy/actions/workflows/test.yml/badge.svg)

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed on your server by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696).

## Commands
Unless otherwise specified all commands are only usable in channels.

### Usable by anyone
#### /join and /leave
Allows users to sign up and leave the group matching in the channel the command is used

#### /pause [days: int(7)]
Allows users to pause their matching in a channel for a given number of days. Users can use `/join` to re-join before the end of that time.

#### /list
List the current matchees in the channel as well as any current scheduled runes.

### Usable by "matchers"
#### /match [group_min: int(3)]
Matches groups of users in a channel and offers a button to pose those groups to the channel to users with `matcher` auth scope. Tracks historical matches and attempts to match users to make new connections with people with divergent roles, in an attempt to maximise diversity.

#### /schedule [group_min: int(3)] [weekday: int(0)] [hour: int(9)] [cancel: bool(False)]
Allows a matcher to set a weekly schedule for matches in the channel, cancel can be used to remove a scheduled run

### Usable by "owners"
#### $sync and $close
Reloads the config and syncs commands, or closes down the bot. Unlike all other commands these are usable in DMs with the bot user.

## Dependencies
* `python3` - Obviously, ideally 3.11
* `venv` - Used for the python virtual env, specs in `requirements.txt`

## Config
Matchy is configured by a `config.json` file that takes this format:
```json
{
    "version" : 1,
    "token" : "<<github bot token>>",

    "match" : {
        "score_factors": {
            "repeat_role" : 4,
            "repeat_match" : 8,
            "extra_member" : 32,
            "upper_threshold" : 64
        }
    }
}
```
Only token and version are required. See [`py/config.py`](py/config.py) for explanations for any of these.

## TODO
* Write integration tests (maybe with [dpytest](https://dpytest.readthedocs.io/en/latest/tutorials/getting_started.html)?)
* Implement a .json file upgrade test
* Track if meets were sucessful
* Improve the weirdo
