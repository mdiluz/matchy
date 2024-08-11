# Matchy
Matchy matches matchees.

![Tests](https://github.com/mdiluz/matchy/actions/workflows/test.yml/badge.svg)

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696).

## Commands
### /match [group_min: int(3)] [matchee_role: str(@Matchee)]
Matches groups of users with a given role and posts those groups to the channel. Tracks historical matches and attempts to match users to make new connections with people with divergent roles, in an attempt to maximise diversity.

### $sync and $close
Only usable by `OWNER` users, reloads the config and syncs commands, or closes down the bot. Only usable in DMs with the bot user. 

## Dependencies
* `python3` - Obviously
* `venv` - Used for the python virtual env, specs in `requirements.txt`

## Config
Matchy is configured by a `config.json` file that takes this format:
```
{
    "token": "<<github bot token>>",
    "owners": [
        <<owner id>>
    ]
}
```
User IDs can be grabbed by turning on Discord's developer mode and right clicking on a user.

## TODO
* Write bot tests with [dpytest](https://dpytest.readthedocs.io/en/latest/tutorials/getting_started.html)
* Add scheduling functionality
* Version the config and history files
* Implement /signup rather than using roles
* Implement authorisation scopes instead of just OWNER values
* Improve the weirdo