# Matchy
Matchy matches matchees.

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696).

## Commands
### /match
Matches groups of users with a given role and posts those groups to the channel.

### $sync
Only usable by `OWNER` users, reloads the config and syncs commands. Only usable in DMs with the bot user. 

## Dependencies
* `python3` obviously
* `discord.py` python module
* `pytest` for testing

## Config
Matchy is configured by a `config.py` file that takes this format:
```
TOKEN = "<<TOKEN>>"
OWNERS = [
    <<USER ID>>,
]
```
User IDs can be grabbed by turning on Discord's developer mode and right clicking on a user.

## TODO
* Write bot tests with [dpytest](https://dpytest.readthedocs.io/en/latest/tutorials/getting_started.html)
* Add matching based on unique rolls?
* Add scheduling functionality
* Improve the weirdo