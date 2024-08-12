"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time
import matching
import state
import config
import re
import util


STATE_FILE = "state.json"

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
    run_hourly_tasks.start()
    activity = discord.Game("/join")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    logger.info("Bot is up and ready!")


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
    State.set_user_active_in_channel(
        interaction.user.id, interaction.channel.id)
    state.save_to_file(State, STATE_FILE)
    await interaction.response.send_message(
        f"Roger roger {interaction.user.mention}!\n"
        + f"Added you to {interaction.channel.mention}!",
        ephemeral=True, silent=True)


@bot.tree.command(description="Leave the matchees for this channel")
@commands.guild_only()
async def leave(interaction: discord.Interaction):
    State.set_user_active_in_channel(
        interaction.user.id, interaction.channel.id, False)
    state.save_to_file(State, STATE_FILE)
    await interaction.response.send_message(
        f"No worries {interaction.user.mention}. Come back soon :)", ephemeral=True, silent=True)


@bot.tree.command(description="Pause your matching in this channel for a number of days")
@commands.guild_only()
@app_commands.describe(days="Days to pause for (defaults to 7)")
async def pause(interaction: discord.Interaction, days: int = None):
    if not days:  # Default to a week
        days = 7
    State.set_user_paused_in_channel(
        interaction.user.id, interaction.channel.id, days)
    state.save_to_file(State, STATE_FILE)
    await interaction.response.send_message(
        f"Sure thing {interaction.user.mention}. Paused you for {days} days!", ephemeral=True, silent=True)


@bot.tree.command(description="List the matchees for this channel")
@commands.guild_only()
async def list(interaction: discord.Interaction):

    matchees = get_matchees_in_channel(interaction.channel)
    mentions = [m.mention for m in matchees]
    msg = "Current matchees in this channel:\n" + \
        f"{', '.join(mentions[:-1])} and {mentions[-1]}"

    tasks = State.get_channel_match_tasks(interaction.channel.id)
    for (day, hour, min) in tasks:
        next_run = util.get_next_datetime(day, hour)
        date_str = util.format_day(next_run)
        msg += f"\nNext scheduled for {date_str} at {hour:02d}:00"
        + "with {min} members per group"

    await interaction.response.send_message(msg, ephemeral=True, silent=True)


@bot.tree.command(description="Schedule a match in this channel (UTC)")
@commands.guild_only()
@app_commands.describe(members_min="Minimum matchees per match (defaults to 3)",
                       weekday="Day of the week to run this (defaults 0, Monday)",
                       hour="Hour in the day (defaults to 9 utc)",
                       cancel="Cancel the scheduled match at this time")
async def schedule(interaction: discord.Interaction,
                   members_min: int | None = None,
                   weekday: int | None = None,
                   hour: int | None = None,
                   cancel: bool = False):
    """Schedule a match using the input parameters"""

    # Set all the defaults
    if not members_min:
        members_min = 3
    if weekday is None:
        weekday = 0
    if hour is None:
        hour = 9
    channel_id = str(interaction.channel.id)

    # Bail if not a matcher
    if not State.get_user_has_scope(interaction.user.id, state.AuthScope.MATCHER):
        await interaction.response.send_message("You'll need the 'matcher' scope to schedule a match",
                                                ephemeral=True, silent=True)
        return

    # Add the scheduled task and save
    success = State.set_channel_match_task(
        channel_id, members_min, weekday, hour, not cancel)
    state.save_to_file(State, STATE_FILE)

    # Let the user know what happened
    if not cancel:
        logger.info("Scheduled new match task in %s with min %s weekday %s hour %s",
                    channel_id, members_min, weekday, hour)
        next_run = util.get_next_datetime(weekday, hour)
        date_str = util.format_day(next_run)

        await interaction.response.send_message(
            f"Done :) Next run will be on {date_str} at {hour:02d}:00\n"
            + "Cancel this by re-sending the command with cancel=True",
            ephemeral=True, silent=True)

    elif success:
        logger.info("Removed task in %s on weekday %s hour %s",
                    channel_id, weekday, hour)
        await interaction.response.send_message(
            f"Done :) Schedule on day {weekday} and hour {hour} removed!", ephemeral=True, silent=True)

    else:
        await interaction.response.send_message(
            f"No schedule for this channel on day {weekday} and hour {hour} found :(", ephemeral=True, silent=True)


@bot.tree.command(description="Match up matchees")
@commands.guild_only()
@app_commands.describe(members_min="Minimum matchees per match (defaults to 3)")
async def match(interaction: discord.Interaction, members_min: int | None = None):
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
    groups_list = '\n'.join(", ".join([m.mention for m in g]) for g in groups)
    msg = f"Roger! I've generated example groups for ya:\n\n{groups_list}"
    view = discord.utils.MISSING

    if State.get_user_has_scope(interaction.user.id, state.AuthScope.MATCHER):
        # Otherwise set up the button
        msg += "\n\nClick the button to match up groups and send them to the channel.\n"
        view = discord.ui.View(timeout=None)
        view.add_item(DynamicGroupButton(members_min))
    else:
        # Let a non-matcher know why they don't have the button
        msg += f"\n\nYou'll need the {state.AuthScope.MATCHER}"
        + " scope to post this to the channel, sorry!"

    await interaction.response.send_message(msg, ephemeral=True, silent=True, view=view)

    logger.info("Done.")


# Increment when adjusting the custom_id so we don't confuse old users
_MATCH_BUTTON_CUSTOM_ID_VERSION = 1
_MATCH_BUTTON_CUSTOM_ID_PREFIX = f'match:v{_MATCH_BUTTON_CUSTOM_ID_VERSION}:'


class DynamicGroupButton(discord.ui.DynamicItem[discord.ui.Button],
                         template=_MATCH_BUTTON_CUSTOM_ID_PREFIX + r'min:(?P<min>[0-9]+)'):
    def __init__(self, min: int) -> None:
        super().__init__(
            discord.ui.Button(
                label='Match Groups!',
                style=discord.ButtonStyle.blurple,
                custom_id=_MATCH_BUTTON_CUSTOM_ID_PREFIX + f'min:{min}',
            )
        )
        self.min: int = min

    # This is called when the button is clicked and the custom_id matches the template.
    @classmethod
    async def from_custom_id(cls, intrctn: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        min = int(match['min'])
        return cls(min)

    async def callback(self, intrctn: discord.Interaction) -> None:
        """Match up people when the button is pressed"""

        logger.info("Handling button press min=%s", self.min)
        logger.info("User %s from %s in #%s", intrctn.user,
                    intrctn.guild.name, intrctn.channel.name)

        # Let the user know we've recieved the message
        await intrctn.response.send_message(content="Matchy is matching matchees...", ephemeral=True)

        # Perform the match
        await match_groups_in_channel(intrctn.channel, self.min)


async def match_groups_in_channel(channel: discord.channel, min: int):
    """Match up the groups in a given channel"""
    groups = active_members_to_groups(channel, min)

    # Send the groups
    for group in groups:

        message = await channel.send(
            f"Matched up {util.format_list([m.mention for m in group])}!")

        # Set up a thread for this match if the bot has permissions to do so
        if channel.permissions_for(channel.guild.me).create_public_threads:
            await channel.create_thread(
                name=util.format_list([m.display_name for m in group]),
                message=message,
                reason="Creating a matching thread")

    # Close off with a message
    await channel.send("That's all folks, happy matching and remember - DFTBA!")

    # Save the groups to the history
    State.log_groups(groups)
    state.save_to_file(State, STATE_FILE)

    logger.info("Done! Matched into %s groups.", len(groups))


@tasks.loop(time=[time(hour=h) for h in range(24)])
async def run_hourly_tasks():
    """Run any hourly tasks we have"""
    for (channel, min) in State.get_active_match_tasks():
        logger.info("Scheduled match task triggered in %s", channel)
        msg_channel = bot.get_channel(int(channel))
        await match_groups_in_channel(msg_channel, min)

    for (channel, _) in State.get_active_match_tasks(datetime.now() + timedelta(days=1)):
        logger.info("Reminding about scheduled task in %s", channel)
        msg_channel = bot.get_channel(int(channel))
        await msg_channel.send("Arf arf! just a reminder I'll be doin a matcherino in here in T-24hrs!"
                               + "\nUse /join if you haven't already, or /pause if you want to skip a week :)")


def get_matchees_in_channel(channel: discord.channel):
    """Fetches the matchees in a channel"""
    # Reactivate any unpaused users
    State.reactivate_users(channel.id)

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
    bot.run(config.Config.token, log_handler=handler, root_logger=True)
