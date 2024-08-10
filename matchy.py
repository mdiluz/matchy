"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
import matching
import history
import config


Config = config.load()
History = history.load()

logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$',
                   description="Matchy matches matchees", intents=intents)


@bot.event
async def on_ready():
    """Bot is ready and connected"""
    logger.info("Bot is up and ready!")
    activity = discord.Game("/match")
    await bot.change_presence(status=discord.Status.online, activity=activity)


def owner_only(ctx: commands.Context) -> bool:
    """Checks the author is an owner"""
    return ctx.message.author.id in Config.owners


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def sync(ctx: commands.Context):
    """Handle sync command"""
    msg = await ctx.reply("Reloading config...", ephemeral=True)
    Config.reload()
    logger.info("Reloaded config")

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


@bot.tree.command(description="Match up matchees")
@commands.guild_only()
@app_commands.describe(group_min="Minimum matchees per match (defaults to 3)",
                       matchee_role="Role for matchees (defaults to @Matchee)")
async def match(interaction: discord.Interaction, group_min: int = None, matchee_role: str = None):
    """Match groups of channel members"""

    logger.info("Handling request '/match group_min=%s matchee_role=%s'",
                group_min, matchee_role)
    logger.info("User %s from %s in #%s", interaction.user,
                interaction.guild.name, interaction.channel.name)

    # Sort out the defaults, if not specified they'll come in as None
    if not group_min:
        group_min = 3
    if not matchee_role:
        matchee_role = "Matchee"

    # Grab the roles and verify the given role
    matcher = matching.get_role_from_guild(interaction.guild, "Matcher")
    matcher = matcher and matcher in interaction.user.roles
    matchee = matching.get_role_from_guild(interaction.guild, matchee_role)
    if not matchee:
        await interaction.response.send_message(f"Server is missing '{matchee_role}' role :(", ephemeral=True)
        return

    # Create our groups!
    matchees = list(
        m for m in interaction.channel.members if matchee in m.roles)
    groups = matching.members_to_groups(matchees, History, group_min)

    # Post about all the groups with a button to send to the channel
    msg = '\n'.join(matching.group_to_message(g) for g in groups)
    if not matcher:  # Let a non-matcher know why they don't have the button
        msg += f"\nYou'll need the {matcher.mention if matcher else 'Matcher'}"
        msg += " role to send this to the channel, sorry!"
    await interaction.response.send_message(msg, ephemeral=True, silent=True,
                                            view=(GroupMessageButton(groups) if matcher else discord.utils.MISSING))

    logger.info("Done. Matched %s matchees into %s groups.",
                len(matchees), len(groups))


class GroupMessageButton(discord.ui.View):
    """A button to press to send the groups to the channel"""

    def __init__(self, groups: list[list[discord.Member]], timeout: int = 180):
        self.groups = groups
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Send groups to channel", style=discord.ButtonStyle.green, emoji="📮")
    async def send_to_channel(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        """Send the groups to the channel with the button is pressed"""
        for msg in (matching.group_to_message(g) for g in self.groups):
            await interaction.channel.send(msg)
        await interaction.channel.send("That's all folks, happy matching and remember - DFTBA!")
        await interaction.response.edit_message(content="Groups sent to channel!", view=None)
        History.save_groups_to_history(self.groups)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(Config.token, log_handler=handler, root_logger=True)
