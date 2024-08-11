"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
import matching
import state
import config
import re


STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

Config = config.load_from_file(CONFIG_FILE)
State = state.load_from_file(STATE_FILE)

logger = logging.getLogger("matchy")
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='$',
                   description="Matchy matches matchees", intents=intents)


@bot.event
async def setup_hook():
    bot.add_dynamic_items(DynamicGroupButton)


@bot.event
async def on_ready():
    """Bot is ready and connected"""
    logger.info("Bot is up and ready!")
    activity = discord.Game("/match")
    await bot.change_presence(status=discord.Status.online, activity=activity)


def owner_only(ctx: commands.Context) -> bool:
    """Checks the author is an owner"""
    return State.get_user_has_scope(ctx.message.author.id, state.AuthScope.OWNER)


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def sync(ctx: commands.Context):
    """Handle sync command"""
    msg = await ctx.reply("Reloading state...", ephemeral=True)
    global State
    State = state.load_from_file(STATE_FILE)
    logger.info("Reloaded state")

    await msg.edit(content="Syncing commands...")
    synced = await bot.tree.sync()
    logger.info("Synced %s command(s)", len(synced))

    await msg.edit(content="Done!")


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def close(ctx: commands.Context):
    """Handle restart command"""
    await ctx.reply("Closing bot...", ephemeral=True)
    logger.info("Closing down the bot")
    await bot.close()


@bot.tree.command(description="Join the matchees for this channel")
@commands.guild_only()
async def join(interaction: discord.Interaction):
    State.set_use_active_in_channel(
        interaction.user.id, interaction.channel.id)
    state.save_to_file(State, STATE_FILE)
    await interaction.response.send_message(
        f"Roger roger {interaction.user.mention}!\n"
        + f"Added you to {interaction.channel.mention}!",
        ephemeral=True, silent=True)


@bot.tree.command(description="Leave the matchees for this channel")
@commands.guild_only()
async def leave(interaction: discord.Interaction):
    State.set_use_active_in_channel(
        interaction.user.id, interaction.channel.id, False)
    state.save_to_file(State, STATE_FILE)
    await interaction.response.send_message(
        f"No worries {interaction.user.mention}. Come back soon :)", ephemeral=True, silent=True)


@bot.tree.command(description="List the matchees for this channel")
@commands.guild_only()
async def list(interaction: discord.Interaction):
    matchees = get_matchees_in_channel(interaction.channel)
    mentions = [m.mention for m in matchees]
    msg = "Current matchees in this channel:\n" + \
        f"{', '.join(mentions[:-1])} and {mentions[-1]}"
    await interaction.response.send_message(msg, ephemeral=True, silent=True)


@bot.tree.command(description="Match up matchees")
@commands.guild_only()
@app_commands.describe(members_min="Minimum matchees per match (defaults to 3)")
async def match(interaction: discord.Interaction, members_min: int = None):
    """Match groups of channel members"""

    logger.info("Handling request '/match group_min=%s", members_min)
    logger.info("User %s from %s in #%s", interaction.user,
                interaction.guild.name, interaction.channel.name)

    # Sort out the defaults, if not specified they'll come in as None
    if not members_min:
        members_min = 3

    # Grab the groups
    groups = active_members_to_groups(interaction.channel, members_min)

    # Let the user know when there's nobody to match
    if not groups:
        await interaction.response.send_message("Nobody to match up :(", ephemeral=True, silent=True)
        return

    # Post about all the groups with a button to send to the channel
    groups_list = '\n'.join(matching.group_to_message(g) for g in groups)
    msg = f"Roger! I've generated example groups for ya:\n\n{groups_list}"
    view = discord.utils.MISSING

    if State.get_user_has_scope(interaction.user.id, state.AuthScope.MATCHER):
        # Let a non-matcher know why they don't have the button
        msg += f"\n\nYou'll need the {state.AuthScope.MATCHER} scope to post this to the channel, sorry!"
    else:
        # Otherwise set up the button
        msg += "\n\nClick the button to match up groups and send them to the channel.\n"
        view = discord.ui.View(timeout=None)
        view.add_item(DynamicGroupButton(members_min))

    await interaction.response.send_message(msg, ephemeral=True, silent=True, view=view)

    logger.info("Done.")


# Increment when adjusting the custom_id so we don't confuse old users
_BUTTON_CUSTOM_ID_VERSION = 1


class DynamicGroupButton(discord.ui.DynamicItem[discord.ui.Button],
                         template=f'match:v{_BUTTON_CUSTOM_ID_VERSION}:' + r'min:(?P<min>[0-9]+)'):
    def __init__(self, min: int) -> None:
        super().__init__(
            discord.ui.Button(
                label='Match Groups!',
                style=discord.ButtonStyle.blurple,
                custom_id=f'match:min:{min}',
            )
        )
        self.min: int = min

    # This is called when the button is clicked and the custom_id matches the template.
    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        min = int(match['min'])
        return cls(min)

    async def callback(self, interaction: discord.Interaction) -> None:
        """Match up people when the button is pressed"""

        logger.info("Handling button press min=%s", self.min)
        logger.info("User %s from %s in #%s", interaction.user,
                    interaction.guild.name, interaction.channel.name)

        # Let the user know we've recieved the message
        await interaction.response.send_message(content="Matchy is matching matchees...", ephemeral=True)

        groups = active_members_to_groups(interaction.channel, self.min)

        # Send the groups
        for msg in (matching.group_to_message(g) for g in groups):
            await interaction.channel.send(msg)

        # Close off with a message
        await interaction.channel.send("That's all folks, happy matching and remember - DFTBA!")

        # Save the groups to the history
        State.log_groups(groups)
        state.save_to_file(State, STATE_FILE)

        logger.info("Done! Matched into %s groups.", len(groups))


def get_matchees_in_channel(channel: discord.channel):
    """Fetches the matchees in a channel"""
    # Gather up the prospective matchees
    return [m for m in channel.members if State.get_user_active_in_channel(m.id, channel.id)]


def active_members_to_groups(channel: discord.channel, min_members: int):
    """Helper to create groups from channel members"""

    # Gather up the prospective matchees
    matchees = get_matchees_in_channel(channel)

    # Create our groups!
    return matching.members_to_groups(matchees, State, min_members, allow_fallback=True)


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(Config.token, log_handler=handler, root_logger=True)
