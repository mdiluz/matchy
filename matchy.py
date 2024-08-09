"""
    matchy.py - Discord bot that matches people into groups
"""
import random
import logging
import importlib
import discord
from discord import app_commands
from discord.ext import commands
# Config contains
# TOKEN : str - Discord bot token
# OWNERS : list[int] - ids of owners able to use the owner commands
if importlib.util.find_spec("config"):
    import config

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


@bot.command()
@commands.dm_only()
@commands.check(lambda ctx:  ctx.message.author.id in config.OWNERS)
async def sync(ctx: commands.Context):
    """Handle sync command"""
    msg = await ctx.reply("Reloading config...", ephemeral=True)
    importlib.reload(config)
    logger.info("Reloaded config")

    await msg.edit(content="Syncing commands...")
    synced = await bot.tree.sync()
    logger.info("Synced %s command(s)", len(synced))

    await msg.edit(content="Done!")


@bot.command()
@commands.dm_only()
@commands.check(lambda ctx:  ctx.message.author.id in config.OWNERS)
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
    matcher = get_role_from_guild(interaction.guild, "Matcher")
    matcher = matcher and matcher in interaction.user.roles
    matchee = get_role_from_guild(interaction.guild, matchee_role)
    if not matchee:
        await interaction.response.send_message(f"Server is missing '{matchee_role}' role :(", ephemeral=True)
        return

    # Create our groups!
    matchees = list(
        m for m in interaction.channel.members if matchee in m.roles)
    groups = matchees_to_groups(matchees, group_min)

    # Post about all the groups with a button to send to the channel
    msg = '\n'.join(group_to_message(g) for g in groups)
    if not matcher:  # Let a non-matcher know why they don't have the button
        msg += f"\nYou'll need the {matcher.mention if matcher else 'Matcher'}"
        msg += " role to send this to the channel, sorry!"
    await interaction.response.send_message(msg, ephemeral=True, silent=True,
                                            view=(GroupMessageButton(groups) if matcher else discord.utils.MISSING))

    logger.info("Done. Matched %s matchees into %s groups.",
                len(matchees), len(groups))


def get_role_from_guild(guild: discord.guild, role: str) -> discord.role:
    """Find a role in a guild"""
    return next((r for r in guild.roles if r.name == role), None)


async def send_groups_to_channel(channel: discord.channel, groups: list[list[discord.Member]]):
    """Send the group messages to a channel"""
    for msg in (group_to_message(g) for g in groups):
        await channel.send(msg)
    await channel.send("That's all folks, happy matching and remember - DFTBA!")


class GroupMessageButton(discord.ui.View):
    """A button to press to send the groups to the channel"""

    def __init__(self, groups: list[list[discord.Member]], timeout: int = 180):
        self.groups = groups
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Send groups to channel", style=discord.ButtonStyle.green, emoji="📮")
    async def send_to_channel(self, interaction: discord.Interaction, _button: discord.ui.Button):
        """Send the groups to the channel with the button is pressed"""
        await send_groups_to_channel(interaction.channel, self.groups)
        await interaction.response.edit_message(content="Groups sent to channel!", view=None)


def matchees_to_groups(matchees: list[discord.Member],
                       per_group: int) -> list[list[discord.Member]]:
    """Generate the groups from the set of matchees"""
    random.shuffle(matchees)
    num_groups = max(len(matchees)//per_group, 1)
    return [matchees[i::num_groups] for i in range(num_groups)]


def group_to_message(group: list[discord.Member]) -> str:
    """Get the message to send for each group"""
    mentions = [m.mention for m in group]
    if len(group) > 1:
        mentions = f"{', '.join(mentions[:-1])} and {mentions[-1]}"
    else:
        mentions = mentions[0]
    return f"Matched up {mentions}!"


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(config.TOKEN, log_handler=handler, root_logger=True)
