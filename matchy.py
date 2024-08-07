import discord
import os
import random
from discord import app_commands
from discord.ext import commands
from config import TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', description="Matchy matches matchies", intents=intents)

@bot.event
async def on_ready():
    print("Bot is Up and Ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command()
@app_commands.describe(per_group = "People per group")
async def matchy(interaction: discord.Interaction, per_group: int):
    # Find the role
    role = None
    for r in interaction.guild.roles:
        if r.name == "matchy":
            role = r
            break
    if not role:
        await interaction.response.send_message("Server has no @matchy role :(", ephemeral=True)
        return

    # Find all the members in the role
    matchies = []
    for member in interaction.channel.members:
        if not member.bot and role in member.roles:
            matchies.append(member)
            break

    # Shuffle the people for randomness
    random.shuffle(matchies)

    # Calculate the number of groups to generate
    total_num = len(matchies)
    num_groups = total_num//per_group
    if not num_groups:
        num_groups = 1
    
    # Split members into groups and share them
    groups = [matchies[i::num_groups] for i in range(num_groups)]
    for group in groups:
        mentions = [m.mention for m in group]
        await interaction.channel.send("Group : " + ", ".join(mentions))

    await interaction.response.send_message("Done :)", ephemeral=True, silent=True)

bot.run(os.getenv(config.TOKEN))