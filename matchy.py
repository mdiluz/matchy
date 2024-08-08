import discord
import os
import random
from discord import app_commands
from discord.ext import commands
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', description="Matchy matches matchees", intents=intents)

# Find a role by name
def find_role_by_name(roles: list[discord.Role], name: str) -> discord.Role:
    role = None
    for r in roles:
        if r.name == name:
            role = r
            break
    return role

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


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    print("Bot is Up and Ready!")

@bot.tree.command()
@app_commands.describe(per_group = "People per group")
async def match(interaction: discord.Interaction, per_group: int):

    # Grab the roles
    matchee = find_role_by_name(interaction.guild.roles, "Matchee")
    matcher = find_role_by_name(interaction.guild.roles, "Matcher")
    if not matchee or not matcher:
        await interaction.response.send_message("Server has missing matchy roles :(", ephemeral=True)
        return

    # Validate that the user has the scope we need
    if matcher not in interaction.user.roles:
        await interaction.response.send_message(f"You'll need the {matcher.mention} role to do this, sorry!", ephemeral=True)
        return
    

    await interaction.channel.send(f"{interaction.user.display_name} asked me to match groups of {per_group}! :partying_face:")

    # Find all the members in the role
    matchies = []
    for member in interaction.channel.members:
        if not member.bot and matchee in member.roles:
            matchies.append(member)
            break

    # Shuffle the people for randomness
    random.shuffle(matchies)

    # Calculate the number of groups to generate
    total_num = len(matchies)
    num_groups = total_num//per_group
    if not num_groups: # Account for when it rounds down to 0
        num_groups = 1

    # Split members into groups and share them
    groups = [matchies[i::num_groups] for i in range(num_groups)]
    for idx, group in enumerate(groups):
        mentions = [m.mention for m in group]
        await interaction.channel.send(f"{get_ordinal(idx+1)} group: " + ", ".join(mentions))

    await interaction.response.send_message("Done :)", ephemeral=True, silent=True)

bot.run(TOKEN)
