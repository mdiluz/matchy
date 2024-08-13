"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord.ext import commands
import config
import state
from cogs.matchy_cog import MatchyCog
from cogs.owner_cog import OwnerCog
import cogs.match_button as match_button

State = state.load_from_file()


logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$',
                   description="Matchy matches matchees", intents=intents)


@bot.event
async def setup_hook():
    await bot.add_cog(MatchyCog(bot, State))
    await bot.add_cog(OwnerCog(bot))


@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user.name)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(config.Config.token, log_handler=handler, root_logger=True)
