# This example requires the 'message_content' intent.

import discord
import os
import logging
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', description="test", intents=intents)

@bot.command()
async def hello(ctx, *args):
    """Just say hello back"""
    await ctx.send(f"Hi {ctx.author.mention}")

bot.run(os.getenv("BOT_TOKEN"))