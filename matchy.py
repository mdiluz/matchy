import discord
import random
import logging
import importlib
from discord import app_commands
from discord.ext import commands
# Config contains
# TOKEN : str - Discord bot token
# SERVERS : list[int] - ids of the servers to have commands active
# OWNERS : list[int] - ids of owners able to use the owner commands
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
    logger.info(f"Reloaded config")

    await msg.edit(content="Syncing commands...")
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s)")

    await msg.edit(content="Done!")


@bot.tree.command(description="Match up matchees")
@commands.guild_only()
@app_commands.describe(group_min="Minimum matchees per match (defaults to 3)", matchee_role="Role for matchees (defaults to @Matchee)")
async def match(interaction: discord.Interaction, group_min: int = None, matchee_role: str = None):
    """Match groups of channel members"""

    logger.info(f"User {interaction.user} from {interaction.guild.name} in #{interaction.channel.name} requested "
                + f"'/match group_min={group_min} matchee_role={matchee_role}'")

    # Sort out the defaults, if not specified they'll come in as None
    if not group_min:
        group_min = 3
    if not matchee_role:
        matchee_role = "Matchee"

    # Grab the roles and verify the given role
    matcher_role = next(
        (r for r in interaction.guild.roles if r.name == "Matcher"), None)
    matchee_role = next(
        (r for r in interaction.guild.roles if r.name == matchee_role), None)
    if not matchee_role:
        await interaction.response.send_message(f"Server is missing '{matchee_role}' role :(", ephemeral=True)
        return
    matcher = matcher_role and matcher_role in interaction.user.roles

    # Create our groups!
    matchees = list(
        m for m in interaction.channel.members if matchee_role in m.roles)
    groups = matchees_to_groups(matchees, group_min)

    # Post about all the groups with a button to send to the channel
    msg = f"{'\n'.join(group_to_message(g) for g in groups)}"
    if not matcher:  # Let a non-matcher know why they don't have the button
        msg += f"\nYou'll need the {
            matcher_role.mention if matcher_role else 'Matcher'} role to send this to the channel, sorry!"
    await interaction.response.send_message(msg, ephemeral=True, silent=True, view=(GroupMessageButton(groups) if matcher else discord.utils.MISSING))

    logger.info(f"Done. Matched {len(matchees)} matchees into {
                len(groups)} groups.")


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
    async def send_to_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await send_groups_to_channel(interaction.channel, self.groups)
        await interaction.response.edit_message(content=f"Groups sent to channel!", view=None)


def matchees_to_groups(matchees: list[discord.Member], per_group: int) -> list[list[discord.Member]]:
    """Generate the groups from the set of matchees"""
    random.shuffle(matchees)
    num_groups = max(len(matchees)//per_group, 1)
    return [matchees[i::num_groups] for i in range(num_groups)]


def group_to_message(group: list[discord.Member]) -> str:
    """Get the message to send for each group"""
    mentions = [m.mention for m in group]
    if len(group) > 1:
        mentions = "{} and {}".format(', '.join(mentions[:-1]), mentions[-1])
    else:
        mentions = mentions[0]
    return f"Matched up {mentions}!"


handler = logging.StreamHandler()
bot.run(config.TOKEN, log_handler=handler, root_logger=True)
