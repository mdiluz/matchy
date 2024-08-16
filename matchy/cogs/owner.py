"""
Owner bot cog
"""
import logging
from discord.ext import commands
from matchy.files.state import State, AuthScope

logger = logging.getLogger("owner")
logger.setLevel(logging.INFO)


class OwnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot, state: State):
        self._bot = bot
        self._state = state

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """
        Sync the bot commands
        You get rate limited if you do this too often so it's better to keep it on command
        """
        msg = await ctx.reply(content="Syncing commands...", ephemeral=True)
        synced = await self._bot.tree.sync()
        logger.info("Synced %s command(s)", len(synced))
        await msg.edit(content="Done!")

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def close(self, ctx: commands.Context):
        """
        Handle close command
        Shuts down the bot when needed
        """
        await ctx.reply("Closing bot...", ephemeral=True)
        logger.info("Closing down the bot")
        await self._bot.close()

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def grant(self, ctx: commands.Context, user: str):
        """
        Handle grant command
        Grant the matcher scope to a given user
        """
        if user.isdigit():
            self._state.set_user_scope(str(user), AuthScope.MATCHER)
            logger.info("Granting user %s matcher scope", user)
            await ctx.reply("Done!", ephemeral=True)
        else:
            await ctx.reply("Likely not a user...", ephemeral=True)
