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

# Set up a logger for matchy
logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

# Create the discord commands bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$', description="Matchy matches matchees", intents=intents)

guilds = []
def cache_guilds():
    """Sync current bot guilds to a list to use"""
    guilds = list(g for g in bot.guilds if g.id in config.SERVERS)
    logger.info(f"Cached {len(guilds)} guild(s)")

@bot.event
async def on_ready():
    """Cache some info once ready"""
    cache_guilds()
    logger.info("Bot is up and ready!")

@bot.command()
@commands.check(lambda ctx:  ctx.message.author.id in config.OWNERS)
@commands.dm_only()
async def sync(ctx: discord.ext.commands.context.Context):
    """Handle sync command"""
    # Reload the config first
    importlib.reload(config)
    logger.info(f"Reloaded config")
    # Sync the commands with the discord API
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s)")
    # Cache the guild information
    cache_guilds()
    await ctx.reply("Done!", ephemeral=True)


@bot.tree.command(description = "Match matchees into groups", guilds = list(g for g in guilds if g.id in config.SERVERS))
@app_commands.describe(per_group = "Matchees per group (default 3+)", post = "Post to channel")
@commands.guild_only()
async def match(interaction: discord.Interaction, per_group: int = None, post: bool = None):
    """Match groups of channel members"""
    if not per_group:
        per_group = 3

    logger.info(f"User {interaction.user} requested /match {per_group}")

    # Grab the roles
    matchee_role = next(r for r in interaction.guild.roles if r.name == "Matchee")
    matcher_role = next(r for r in interaction.guild.roles if r.name == "Matcher")
    if not matchee_role or not matcher_role:
        await interaction.response.send_message("Server has missing matchy roles :(", ephemeral=True)
        return

    # Validate that the user has the scope we need
    if matcher_role not in interaction.user.roles:
        await interaction.response.send_message(f"You'll need the {matcher_role.mention} role to do this, sorry!", ephemeral=True)
        return

    # Let the channel know the matching is starting
    if post:
        await interaction.channel.send(f"{interaction.user.display_name} asked me to match groups of {per_group}! :partying_face:")

    # Find all the members in the role
    matchees = list( m for m in interaction.channel.members if not m.bot and matchee_role in m.roles)
    logger.info(f"{len(matchees)} matchees found")

    # Shuffle the people for randomness
    random.shuffle(matchees)

    # Calculate the number of groups to generate
    total_num = len(matchees)
    num_groups = max(total_num//per_group, 1)

    logger.info(f"Creating {num_groups} groups")

    # Split members into groups and share them
    groups = [matchees[i::num_groups] for i in range(num_groups)]
    group_msgs = []
    for idx, group in enumerate(groups):
        mentions = ", ".join([m.mention for m in group])
        logger.info(f"Sending group: {list(m.name for m in group)}")
        group_msgs.append(f"Matched up {mentions}!")

    # Send the messages
    if post:
        for msg in group_msgs:
            await interaction.channel.send(msg)
    else:
        await interaction.response.send_message("\n".join(group_msgs), ephemeral=True, silent=True)

    logger.info(f"Done")
    if post:
        await interaction.response.send_message("Done :)", ephemeral=True, silent=True)

# Kick off the bot run cycle
handler = logging.StreamHandler()
bot.run(config.TOKEN, log_handler=handler, root_logger=True)
