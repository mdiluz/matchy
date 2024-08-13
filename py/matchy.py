"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord.ext import commands
import config
import state
import cog
import match_button

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
    await bot.add_cog(cog.MatchyCog(bot, State))
    # TODO: This line feels like it should be in the cog?
    bot.add_dynamic_items(match_button.DynamicGroupButton)


@bot.event
async def on_ready():
    logger.info("Logged in as %s", bot.user.name)


def owner_only(ctx: commands.Context) -> bool:
    """Checks the author is an owner"""
    return State.get_user_has_scope(ctx.message.author.id, state.AuthScope.OWNER)


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def sync(ctx: commands.Context):
    """Handle sync command"""
    msg = await ctx.reply("Reloading state...", ephemeral=True)
    global State
    State = state.load_from_file()
    logger.info("Reloaded state")

    await msg.edit(content="Syncing commands...")
    synced = await bot.tree.sync()
    logger.info("Synced %s command(s)", len(synced))

    await msg.edit(content="Done!")


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def close(ctx: commands.Context):
    """Handle restart command"""
    await ctx.reply("Closing bot...", ephemeral=True)
    logger.info("Closing down the bot")
    await bot.close()


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(config.Config.token, log_handler=handler, root_logger=True)
