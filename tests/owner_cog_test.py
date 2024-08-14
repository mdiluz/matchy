import discord
import discord.ext.commands as commands
import pytest
import pytest_asyncio
import matchy.files.state as state
import discord.ext.test as dpytest

from matchy.cogs.owner import Cog

# Primarily borrowing from https://dpytest.readthedocs.io/en/latest/tutorials/using_pytest.html
# TODO: Test more somehow, though it seems like dpytest is pretty incomplete


@pytest_asyncio.fixture
async def bot():
    # Setup
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="$",
                     intents=intents)
    await b._async_setup_hook()
    await b.add_cog(Cog(b, state.State(state._EMPTY_DICT)))
    dpytest.configure(b)
    yield b
    await dpytest.empty_queue()


@pytest.mark.asyncio
async def test_must_be_owner(bot):
    with pytest.raises(commands.errors.NotOwner):
        await dpytest.message("$sync")

    with pytest.raises(commands.errors.NotOwner):
        await dpytest.message("$close")

    with pytest.raises(commands.errors.NotOwner):
        await dpytest.message("$grant")
