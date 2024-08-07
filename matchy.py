import discord
import os
import argparse
import random
from itertools import islice
from discord.ext import commands

def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='$', description="Matchy matches matchies", intents=intents)

@bot.command()
async def hello(ctx, *args):
    """Just say hello back"""
    await ctx.send(f"Hi {ctx.author.mention}")

@bot.command()
async def matchy(ctx, *args):
    """Create some random groups"""
    argparser = argparse.ArgumentParser(exit_on_error=False, add_help=False, usage='$matchy [options]')
    argparser.add_argument("--num", default=3, type=int, help="Number of people to match up")
    argparser.add_argument("--help", "-h", action='store_true', help=argparse.SUPPRESS)
    args = argparser.parse_args(args)

    # Print the help if requested
    if args.help:
        await ctx.send(argparser.format_help())
        return
    
    # Find the role
    role = None
    for r in ctx.message.guild.roles:
        if r.name == "matchy":
            role = r
            break
    if not role:
        await ctx.send("Error: server has no @matchy role!")
        return

    # Find all the members in the role
    matchies = []
    for member in ctx.channel.members:
        for r in member.roles:
            if r == role:
                matchies.append(member)
                break

    # Shuffle the people for randomness
    random.shuffle(matchies)
    
    # Chunk up the groups and share them
    for group in chunk(matchies, args.num):
        mentions = [m.mention for m in group]
        await ctx.send("A group! " + ", ".join(mentions))

bot.run(os.getenv("BOT_TOKEN"))