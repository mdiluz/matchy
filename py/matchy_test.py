import pytest
import discord
from discord.ext import commands
from unittest.mock import AsyncMock, MagicMock

# Import your bot instance and commands module
from my_bot import bot

@pytest.fixture
def bot_instance():
    # Setup a test bot instance
    bot = commands.Bot(command_prefix="!")

    # Mock bot's guild and channel
    guild = MagicMock()
    guild.id = 1234567890

    channel = MagicMock()
    channel.id = 9876543210
    channel.guild = guild
    channel.send = AsyncMock()  # Mock send method

    bot.add_guild(guild)
    bot.add_cog(MyCog(bot))  # Example of adding a cog

    return bot, channel

@pytest.mark.asyncio
async def test_hello_command(bot_instance):
    bot, channel = bot_instance

    # Simulate sending a message
    message = MagicMock()
    message.content = "!hello"
    message.channel = channel
    message.author = MagicMock()
    message.author.bot = False  # Ensure the author is not a bot

    # Dispatch the message to trigger the command
    await bot.process_commands(message)

    # Check if the bot sent a response
    channel.send.assert_called_once_with("Hello, World!")

@pytest.mark.asyncio
async def test_on_member_join(bot_instance):
    bot, channel = bot_instance

    # Simulate a member joining
    member = MagicMock()
    member.guild = channel.guild

    await bot.on_member_join(member)

    # Check if the bot welcomed the new member
    channel.send.assert_called_once_with(f"Welcome {member.mention} to {channel.guild.name}!")
