# Matchy
Matchy matches matchees.

![Tests](https://github.com/mdiluz/matchy/actions/workflows/test.yml/badge.svg)

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed on your server by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696).

## Commands
Matchy is mostly managed with commands in server channels. These are all listed below.

### User commands
#### /join and /leave
Allows users to sign up and leave the group matching in the channel the command is used.

#### /pause [days: int(7)]
Allows users to pause their matching in a channel for a given number of days. Users can use `/join` to re-join before the end of that time.

#### /list
List the current matchees in the channel as well as any current scheduled match runs.

### Matcher commands
Only usable by users with the `matcher` scope.

#### /match [group_min: int(3)]
Matches groups of users in a channel and offers a button to pose those groups to the channel to users with `matcher` auth scope. Tracks historical matches and attempts to match users to make new connections with people with divergent roles, in an attempt to maximise diversity.

#### /schedule [group_min: int(3)] [weekday: int(0)] [hour: int(9)] [cancel: bool(False)]
Allows a matcher to set a weekly schedule for matches in the channel, cancel can be used to remove a scheduled run

### Admin commands
Only usable by users with the `owner` scope. Only usable in a DM with the bot user.

#### $sync and $close
Syncs bot commands and reloads the state file, or closes down the bot. 

## Development
Current development is on Linux, though running on Mac or Windows should work fine.

### Dependencies
* `python3` - Obviously, ideally 3.11
* `venv` - Used for the python virtual env, specs in `requirements.txt`

### Getting Started
```
git clone git@github.com:mdiluz/matchy.git
cd matchy
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
VSCode can then be configured to use this new `.venv` and is the recommended way to develop.

### Tests
Python tests are written to use `pytest` and cover most internal functionality. Tests can be run in the same way as in the Github Actions with [`scripts/test.py`](`scripts/test.py`), which lints all python code and runs any tests with `pytest`.

#### Coverage
A helper script [`scripts/test-cov.py`](scripts/test-cov.py) is available to generate a html view on current code coverage.

## Hosting

### Config
Matchy is configured by a required `config.json` file that takes this format:
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
Only token and version are required. To generate bot token for development see [this discord.py guide](https://discordpy.readthedocs.io/en/stable/discord.html).

See [`py/config.py`](py/config.py) for explanations for any extra settings here.

### Running
It is recommended to only ever run the `release` branch in production, as this branch has passed the tests.

Running the bot can be as simple as `python3 scripts/matchy.py`, but a [`scripts/run.py`](scripts/run.py) script is provided to update to the latest release, install any new `pip` dependencies and run the bot. 

The following command can be used to execute `run.py` on a loop, allowing the bot to be updated with a simple `$close` command from an `owner` user, but will still exit the loop if the bot throws a fatal error.
```
while ./scripts/run.py; end
```

### State
State is stored locally in a `state.json` file. This will be created by the bot. This stores historical information on users, maching schedules, user auth scopes and more. See [`py/state.py`](py/state.py) for schema information if you need to inspect it.

## TODO
* Rethink the matcher scope, seems like maybe this could be simpler or removed
* Implement a .json file upgrade test
* Track if matches were successful
* Improve the weirdo
