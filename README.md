# Matchy
Matchy matches matchees.

![Tests](https://github.com/mdiluz/matchy/actions/workflows/test.yml/badge.svg)

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696).

## Commands
### /match [group_min: int(3)]
Matches groups of users in a channel and offers a button to pose those groups to the channel to users with `matcher` auth scope. Tracks historical matches and attempts to match users to make new connections with people with divergent roles, in an attempt to maximise diversity.

### /join and /leave
Allows users to sign up and leave the group matching in the channel the command is used

### /pause [days: int(7)]
Allows users to pause their matching in a channel for a given number of days

### $sync and $close
Only usable by `OWNER` users, reloads the config and syncs commands, or closes down the bot. Only usable in DMs with the bot user.

## Dependencies
* `python3` - Obviously
* `venv` - Used for the python virtual env, specs in `requirements.txt`

## Config
Matchy is configured by a `config.json` file that takes this format:
```
{
    "version": 1,
    "token": "<<github bot token>>",
}
```

## TODO
* Write bot tests with [dpytest](https://dpytest.readthedocs.io/en/latest/tutorials/getting_started.html)
* Move more constants to the config
* Add scheduling functionality
* Fix logging in some sub files (doesn't seem to actually be output?)
* Improve the weirdo