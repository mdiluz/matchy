import discord
import random
import logging
from discord import app_commands
from discord.ext import commands

# Config contains
# TOKEN : str - Discord bot token
# SERVERS : list[int] - ids of the servers to have commands active
# OWNERS : list[int] - ids of owners able to use the owner commands
import config

handler = logging.StreamHandler()
logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$', description="Matchy matches matchees", intents=intents)

# Find a role by name
def find_role_by_name(roles: list[discord.Role], name: str) -> discord.Role:
    for r in roles:
        if r.name == name:
            return r
    return None

# Get the ordinal for an int
def get_ordinal(num : int):
    if num > 9:
        secondToLastDigit = str(num)[-2]
        if secondToLastDigit == '1':
            return str(num)+'th'
    lastDigit = num % 10
    if (lastDigit == 1):
        return str(num)+'st'
    elif (lastDigit == 2):
        return str(num)+'nd'
    elif (lastDigit == 3):
        return str(num)+'rd'
    else:
        return str(num)+'th'

guilds = []
def sync_guilds():
    # Cache the guild info
    for guild in bot.guilds:
        if guild.id in config.SERVERS:
            guilds.append(guild)
    logger.info(f"Synced {len(guilds)} guild(s)")

@bot.event
async def on_ready():
    sync_guilds()
    logger.info("Bot is up and ready!")

@bot.command()
async def sync(ctx):
    if ctx.author.id not in config.OWNERS:
        logger.warning(f"User {ctx.author} unauthorised for sync")
        return
    
    # Sync the commands
    synced = await bot.tree.sync()
    logger.info(f"Synced {len(synced)} command(s)")
    
    sync_guilds()
        

@bot.tree.command(description = "Match matchees into groups", guilds = list(g for g in guilds if g.id in config.SERVERS))
@app_commands.describe(per_group = "Matchees per group")
async def match(interaction: discord.Interaction, per_group: int):
    logger.info(f"User {interaction.user} requested /match {per_group}")

    # Grab the roles
    matchee_role = find_role_by_name(interaction.guild.roles, "Matchee")
    matcher_role = find_role_by_name(interaction.guild.roles, "Matcher") 
    if not matchee_role or not matcher_role:
        await interaction.response.send_message("Server has missing matchy roles :(", ephemeral=True)
        return

    # Validate that the user has the scope we need
    if matcher_role not in interaction.user.roles:
        await interaction.response.send_message(f"You'll need the {matcher_role.mention} role to do this, sorry!", ephemeral=True)
        return
    
    # Let the channel know the matching is starting
    await interaction.channel.send(f"{interaction.user.display_name} asked me to match groups of {per_group}! :partying_face:")

    # Find all the members in the role
    matchees = []
    for member in interaction.channel.members:
        if not member.bot and matchee_role in member.roles:
            matchees.append(member)
    logger.info(f"{len(matchees)} matchees found")

    # Shuffle the people for randomness
    random.shuffle(matchees)

    # Calculate the number of groups to generate
    total_num = len(matchees)
    num_groups = total_num//per_group
    if not num_groups: # Account for when it rounds down to 0
        num_groups = 1

    logger.info(f"Creating {num_groups} groups")

    # Split members into groups and share them
    groups = [matchees[i::num_groups] for i in range(num_groups)]
    for idx, group in enumerate(groups):
        mentions = [m.mention for m in group]
        logger.info(f"Sending group: {list(m.name for m in group)}")
        await interaction.channel.send(f"{get_ordinal(idx+1)} group: " + ", ".join(mentions))
    
    logger.info(f"Done")
    await interaction.response.send_message("Done :)", ephemeral=True, silent=True)

bot.run(config.TOKEN, log_handler=handler, root_logger=True)
