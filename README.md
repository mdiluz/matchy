# Matchy
<img src="img/matchy_alpha.png" width="255">

Matchy matches matchees.

Matchy is a Discord bot that groups up users for fun and vibes. Matchy can be installed on your server by clicking [here](https://discord.com/oauth2/authorize?client_id=1270849346987884696). Matchy only allows authorised users to trigger posts in channels.

![Tests](https://github.com/mdiluz/matchy/actions/workflows/test.yml/badge.svg)

## Commands
Matchy supports a bunch of user, `matcher` and bot owner commands. `/` commands are available in any channel the bot has access to, and `$` commands are only available in DMs.

| Command   | Permissions | Description                                            |
|-----------|-------------|--------------------------------------------------------|
| /join     | user        | Joins the matchee list                                 |
| /leave    | user        | Leaves the matchee list                                |
| /pause    | user        | Pauses the user for `days: int` days                   |
| /list     | user        | Lists the current matchees and scheduled matches       |
| /match    | user        | Shares a preview of the matchee groups of size `group_min: int` with the user, offers a button to post the match to `matcher` users                 |
| /schedule | `matcher`   | Shedules a match every week with `group_min: int` users on `weekday: int` day and at `hour: int` hour. Can pass `cancel: True` to stop the schedule |
| $sync     | bot owner   | Syncs bot command data with the discord servers        |
| $close    | bot owner   | Closes the bot connection so the bot quits safely      |
| $grant    | bot owner   | Grants matcher to a given user (ID)                    |

## Development
Development has been on on Linux so far, but running on Mac or Windows _should_ work fine. Please report any issues found.

### Dependencies
* `python3` - Obviously, ideally 3.11
* `venv` - Used for the python virtual env, specs in `requirements.txt`
* `docker` - Optional, for deployment

### Getting Started
```bash
git clone git@github.com:mdiluz/matchy.git
cd matchy
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
git checkout -b [feature-branch-name]
```
VSCode can be configured to use this new `.venv` and is the recommended way to develop.

### Tests
Python tests are written to use `pytest` and cover most internal functionality. Tests can be run in the same way as in the Github Actions with [`scripts/test.py`](`scripts/test.py`), which lints all python code and runs any tests with `pytest`. A helper script [`scripts/test-cov.py`](scripts/test-cov.py) is available to generate a html view on current code coverage.

## Hosting

### Config and State
Matchy is configured by an optional `$MATCHY_CONFIG` envar or a `.matchy/config.json` file that takes this format:
```json
{
    "version" : 2,
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
Only the version is required.

See [`py/config.py`](py/config.py) for explanations for any extra settings here.

_State_ is stored locally in a `.matchy/state.json` file. This will be created by the bot. This stores historical information on users, maching schedules, user auth scopes and more. See [`py/state.py`](py/state.py) for schema information if you need to inspect it.

### Secrets
The `TOKEN` envar is required run the bot. It's recommended this is placed in a local `.env` file. To generate bot token for development see [this discord.py guide](https://discordpy.readthedocs.io/en/stable/discord.html).

### Docker
Docker and Compose configs are provided, with the latest release tagged as  `ghcr.io/mdiluz/matchy:latest`. A location for persistent data is stil required so some persistent volume will need to be mapped into the container as `/usr/share/app/.matchy`.

An example for how to do this may look like this:
```bash
docker run -v --env-file=.env ./.matchy:/usr/src/app/.matchy ghcr.io/mdiluz/matchy:latest
```
A [`docker-compose.yml`](docker-compose.yml) file is also provided that essentially performs the above when used with `docker compose up --exit-code-from matchy`. A `MATCHY_DATA` envar can be used in conjunction with compose to set a custom local path for the location of the data file. 

## TODO
* Implement better tests to the discordy parts of the codebase
* Implement a .json file upgrade test
* Track if matches were successful
* Improve the weirdo
