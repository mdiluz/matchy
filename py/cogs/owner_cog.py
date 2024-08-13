"""
Owner bot cog
"""
import logging
from discord.ext import commands

logger = logging.getLogger("owner")
logger.setLevel(logging.INFO)


class OwnerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        """Handle sync command"""
        msg = await ctx.reply(content="Syncing commands...", ephemeral=True)
        synced = await self.bot.tree.sync()
        logger.info("Synced %s command(s)", len(synced))
        await msg.edit(content="Done!")

    @commands.command()
    @commands.dm_only()
    @commands.is_owner()
    async def close(self, ctx: commands.Context):
        """Handle restart command"""
        await ctx.reply("Closing bot...", ephemeral=True)
        logger.info("Closing down the bot")
        await self.bot.close()
