"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord.ext import commands
import os
from state import load_from_file
from cogs.matchy_cog import MatchyCog
from cogs.owner_cog import OwnerCog

_STATE_FILE = ".matchy/state.json"
state = load_from_file(_STATE_FILE)

logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$',
                   description="Matchy matches matchees", intents=intents)


@bot.event
async def setup_hook():
    await bot.add_cog(MatchyCog(bot, state))
    await bot.add_cog(OwnerCog(bot, state))


@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user.name)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    token = os.environ.get("TOKEN", None)
    assert token, "$TOKEN required"
    bot.run(token, log_handler=handler, root_logger=True)
