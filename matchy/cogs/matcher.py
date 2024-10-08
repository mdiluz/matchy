"""
Matchy bot cog
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time
import re

import matchy.matching as matching
from matchy.state import AuthScope
import matchy.util as util
import matchy.state as state
import matchy.cogs.strings as strings


logger = logging.getLogger("cog")
logger.setLevel(logging.INFO)


class MatcherCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot is ready and connected"""
        self.run_hourly_tasks.start()
        self.bot.add_dynamic_items(MatchDynamicButton)
        activity = discord.Game("/join")
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        logger.info("Bot is up and ready!")

    @app_commands.command(description="Join the matchees for this channel")
    @commands.guild_only()
    async def join(self, interaction: discord.Interaction):
        logger.info("Handling /join in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        state.State.set_user_active_in_channel(
            interaction.user.id, interaction.channel.id)
        await interaction.response.send_message(
            strings.acknowledgement(interaction.user.mention) + "\n"
            + strings.user_added(interaction.channel.mention),
            ephemeral=True, silent=True)

    @app_commands.command(description="Leave the matchees for this channel")
    @commands.guild_only()
    async def leave(self, interaction: discord.Interaction):
        logger.info("Handling /leave in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        state.State.set_user_active_in_channel(
            interaction.user.id, interaction.channel.id, False)
        await interaction.response.send_message(
            strings.user_leave(interaction.user.mention), ephemeral=True, silent=True)

    @app_commands.command(description="Pause your matching in this channel for a number of days")
    @commands.guild_only()
    @app_commands.describe(days="Days to pause for (defaults to 7)")
    async def pause(self, interaction: discord.Interaction, days: int | None = None):
        logger.info("Handling /pause in %s %s from %s with days=%s",
                    interaction.guild.name, interaction.channel, interaction.user.name, days)

        if days is None:  # Default to a week
            days = 7
        until = datetime.now() + timedelta(days=days)
        state.State.set_user_paused_in_channel(
            interaction.user.id, interaction.channel.id, until)
        await interaction.response.send_message(
            strings.acknowledgement(interaction.user.mention) + "\n"
            + strings.paused(until),
            ephemeral=True, silent=True)

    @app_commands.command(description="List the matchees for this channel")
    @commands.guild_only()
    async def list(self, interaction: discord.Interaction):
        logger.info("Handling /list command in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        (matchees, paused) = matching.get_matchees_in_channel(interaction.channel)

        msg = ""

        if matchees:
            mentions = [m.mention for m in matchees]
            msg += strings.active_matchees(mentions) + "\n"

        if paused:
            mentions = [m.mention for m in paused]
            msg += "\n" + strings.paused_matchees(mentions) + "\n"

        tasks = state.State.get_channel_match_tasks(interaction.channel.id)
        for (day, hour, min) in tasks:
            next_run = util.get_next_datetime(day, hour)
            msg += "\n" + strings.scheduled(next_run, min)

        if not msg:
            msg = strings.no_scheduled()

        await interaction.response.send_message(msg, ephemeral=True, silent=True)

    @app_commands.command(description="Schedule a match in this channel (UTC)")
    @commands.guild_only()
    @app_commands.describe(members_min="Minimum matchees per match (defaults to 3)",
                           weekday="Day of the week to run this (defaults 0, Monday)",
                           hour="Hour in the day (defaults to 9 utc)")
    async def schedule(self,
                       interaction: discord.Interaction,
                       members_min: int | None = None,
                       weekday: int | None = None,
                       hour: int | None = None):
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
        if not state.State.get_user_has_scope(interaction.user.id, AuthScope.MATCHER):
            await interaction.response.send_message(strings.need_matcher_scope(),
                                                    ephemeral=True, silent=True)
            return

        # Add the scheduled task and save
        state.State.set_channel_match_task(
            channel_id, members_min, weekday, hour)

        # Let the user know what happened
        logger.info("Scheduled new match task in %s with min %s weekday %s hour %s",
                    channel_id, members_min, weekday, hour)
        next_run = util.get_next_datetime(weekday, hour)

        view = discord.ui.View(timeout=None)
        view.add_item(ScheduleButton())

        await interaction.response.send_message(
            strings.scheduled_success(next_run),
            ephemeral=True, silent=True, view=view)

    @app_commands.command(description="Cancel all scheduled matches in this channel")
    @commands.guild_only()
    async def cancel(self, interaction: discord.Interaction):
        """Cancel scheduled matches in this channel"""
        # Bail if not a matcher
        if not state.State.get_user_has_scope(interaction.user.id, AuthScope.MATCHER):
            await interaction.response.send_message(strings.need_matcher_scope(),
                                                    ephemeral=True, silent=True)
            return

        # Add the scheduled task and save
        channel_id = str(interaction.channel.id)
        state.State.remove_channel_match_tasks(channel_id)

        await interaction.response.send_message(
            strings.cancelled(), ephemeral=True, silent=True)

    @app_commands.command(description="Match up matchees")
    @commands.guild_only()
    @app_commands.describe(members_min="Minimum matchees per match (defaults to 3)")
    async def match(self, interaction: discord.Interaction, members_min: int | None = None):
        """Match groups of channel members"""

        logger.info("Handling request '/match group_min=%s", members_min)
        logger.info("User %s from %s in #%s", interaction.user,
                    interaction.guild.name, interaction.channel.name)

        # Sort out the defaults, if not specified they'll come in as None
        if not members_min:
            members_min = 3

        # Grab the groups
        groups = matching.active_members_to_groups(
            interaction.channel, members_min)

        # Let the user know when there's nobody to match
        if not groups:
            await interaction.response.send_message(strings.nobody_to_match(), ephemeral=True, silent=True)
            return

        # Post about all the groups with a button to send to the channel
        groups_list = '\n'.join(
            ", ".join([m.mention for m in g]) for g in groups)
        msg = strings.generated_groups(groups_list)
        view = discord.utils.MISSING

        if state.State.get_user_has_scope(interaction.user.id, AuthScope.MATCHER):
            # Otherwise set up the button
            msg += "\n\n" + strings.click_to_match() + "\n"
            view = discord.ui.View(timeout=None)
            view.add_item(MatchDynamicButton(members_min))
        else:
            # Let a non-matcher know why they don't have the button
            msg += "\n\n" + strings.need_matcher_to_post()

        await interaction.response.send_message(msg, ephemeral=True, silent=True, view=view)

        logger.info("Done.")

    @tasks.loop(time=[time(hour=h) for h in range(24)])
    async def run_hourly_tasks(self):
        """Run any hourly tasks we have"""

        for (channel, min) in state.State.get_active_match_tasks():
            logger.info("Scheduled match task triggered in %s", channel)
            msg_channel = self.bot.get_channel(int(channel))
            await match_groups_in_channel(msg_channel, min)

        for (channel, _) in state.State.get_active_match_tasks(datetime.now() + timedelta(days=1)):
            logger.info("Reminding about scheduled task in %s", channel)
            msg_channel = self.bot.get_channel(int(channel))
            await msg_channel.send(strings.reminder())


# Increment when adjusting the custom_id so we don't confuse old users
_MATCH_BUTTON_CUSTOM_ID_VERSION = 1
_MATCH_BUTTON_CUSTOM_ID_PREFIX = f'match:v{_MATCH_BUTTON_CUSTOM_ID_VERSION}:'


class MatchDynamicButton(discord.ui.DynamicItem[discord.ui.Button],
                         template=_MATCH_BUTTON_CUSTOM_ID_PREFIX + r'min:(?P<min>[0-9]+)'):
    """
    Describes a simple button that lets the user trigger a match
    """

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
        await intrctn.response.send_message(content=strings.matching(), ephemeral=True)

        # Perform the match
        await match_groups_in_channel(intrctn.channel, self.min)


async def match_groups_in_channel(channel: discord.channel, min: int):
    """Match up the groups in a given channel"""
    groups = matching.active_members_to_groups(channel, min)

    # Send the groups
    for group in groups:
        message = await channel.send(
            strings.matched_up([m.mention for m in group]))
        # Set up a thread for this match if the bot has permissions to do so
        if channel.permissions_for(channel.guild.me).create_public_threads:
            await channel.create_thread(
                name=strings.thread_title([m.display_name for m in group]),
                message=message,
                reason="Creating a matching thread")

    # Close off with a message
    await channel.send(strings.matching_done())
    # Save the groups to the history
    state.State.log_groups(groups)

    logger.info("Done! Matched into %s groups.", len(groups))


class ScheduleButton(discord.ui.Button):
    """
    Describes a simple button that lets the user post the schedule to the channel
    """

    def __init__(self) -> None:
        super().__init__(
            label='Post schedule',
            style=discord.ButtonStyle.blurple
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """Post about the current schedule when requested"""
        logger.info("Handling schedule button press byuser %s from %s in #%s",
                    interaction.user, interaction.guild.name, interaction.channel.name)

        tasks = state.State.get_channel_match_tasks(interaction.channel.id)

        msg = strings.added_schedule(interaction.user.mention) + "\n"
        msg += strings.scheduled_matches()

        if tasks:
            for (day, hour, min) in tasks:
                next_run = util.get_next_datetime(day, hour)
                msg += strings.scheduled(next_run, min)

            await interaction.channel.send(msg)
            await interaction.response.send_message(
                content=strings.acknowledgement(interaction.user.mention), ephemeral=True)
        else:
            await interaction.response.send_message(content=strings.no_scheduled(), ephemeral=True)
