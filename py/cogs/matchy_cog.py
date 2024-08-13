"""
Matchy bot cog
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, time

import match_button
import matching
from state import State, save_to_file, AuthScope
import util

logger = logging.getLogger("cog")
logger.setLevel(logging.INFO)


class MatchyCog(commands.Cog):
    def __init__(self, bot: commands.Bot, state: State):
        self.bot = bot
        self.state = state

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot is ready and connected"""
        self.run_hourly_tasks.start()
        activity = discord.Game("/join")
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        logger.info("Bot is up and ready!")

    @app_commands.command(description="Join the matchees for this channel")
    @commands.guild_only()
    async def join(self, interaction: discord.Interaction):
        logger.info("Handling /join in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        self.state.set_user_active_in_channel(
            interaction.user.id, interaction.channel.id)
        save_to_file(self.state)
        await interaction.response.send_message(
            f"Roger roger {interaction.user.mention}!\n"
            + f"Added you to {interaction.channel.mention}!",
            ephemeral=True, silent=True)

    @app_commands.command(description="Leave the matchees for this channel")
    @commands.guild_only()
    async def leave(self, interaction: discord.Interaction):
        logger.info("Handling /leave in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        self.state.set_user_active_in_channel(
            interaction.user.id, interaction.channel.id, False)
        save_to_file(self.state)
        await interaction.response.send_message(
            f"No worries {interaction.user.mention}. Come back soon :)", ephemeral=True, silent=True)

    @app_commands.command(description="Pause your matching in this channel for a number of days")
    @commands.guild_only()
    @app_commands.describe(days="Days to pause for (defaults to 7)")
    async def pause(self, interaction: discord.Interaction, days: int | None = None):
        logger.info("Handling /pause in %s %s from %s with days=%s",
                    interaction.guild.name, interaction.channel, interaction.user.name, days)

        if days is None:  # Default to a week
            days = 7
        until = datetime.now() + timedelta(days=days)
        self.state.set_user_paused_in_channel(
            interaction.user.id, interaction.channel.id, until)
        save_to_file(self.state)
        await interaction.response.send_message(
            f"Sure thing {interaction.user.mention}!\n"
            + f"Paused you until {util.format_day(until)}!",
            ephemeral=True, silent=True)

    @app_commands.command(description="List the matchees for this channel")
    @commands.guild_only()
    async def list(self, interaction: discord.Interaction):
        logger.info("Handling /list command in %s %s from %s",
                    interaction.guild.name, interaction.channel, interaction.user.name)

        matchees = matching.get_matchees_in_channel(self.state, interaction.channel)
        mentions = [m.mention for m in matchees]
        msg = "Current matchees in this channel:\n" + \
            f"{util.format_list(mentions)}"

        tasks = self.state.get_channel_match_tasks(interaction.channel.id)
        for (day, hour, min) in tasks:
            next_run = util.get_next_datetime(day, hour)
            date_str = util.format_day(next_run)
            msg += f"\nNext scheduled for {date_str} at {hour:02d}:00"
            msg += f" with {min} members per group"

        await interaction.response.send_message(msg, ephemeral=True, silent=True)

    @app_commands.command(description="Schedule a match in this channel (UTC)")
    @commands.guild_only()
    @app_commands.describe(members_min="Minimum matchees per match (defaults to 3)",
                           weekday="Day of the week to run this (defaults 0, Monday)",
                           hour="Hour in the day (defaults to 9 utc)",
                           cancel="Cancel the scheduled match at this time")
    async def schedule(self,
                       interaction: discord.Interaction,
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
        if not self.state.get_user_has_scope(interaction.user.id, AuthScope.MATCHER):
            await interaction.response.send_message("You'll need the 'matcher' scope to schedule a match",
                                                    ephemeral=True, silent=True)
            return

        # Add the scheduled task and save
        success = self.state.set_channel_match_task(
            channel_id, members_min, weekday, hour, not cancel)
        save_to_file(self.state)

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
            self.state, interaction.channel, members_min)

        # Let the user know when there's nobody to match
        if not groups:
            await interaction.response.send_message("Nobody to match up :(", ephemeral=True, silent=True)
            return

        # Post about all the groups with a button to send to the channel
        groups_list = '\n'.join(
            ", ".join([m.mention for m in g]) for g in groups)
        msg = f"Roger! I've generated example groups for ya:\n\n{groups_list}"
        view = discord.utils.MISSING

        if self.state.get_user_has_scope(interaction.user.id, AuthScope.MATCHER):
            # Otherwise set up the button
            msg += "\n\nClick the button to match up groups and send them to the channel.\n"
            view = discord.ui.View(timeout=None)
            view.add_item(match_button.DynamicGroupButton(members_min))
        else:
            # Let a non-matcher know why they don't have the button
            msg += f"\n\nYou'll need the {AuthScope.MATCHER}"
            + " scope to post this to the channel, sorry!"

        await interaction.response.send_message(msg, ephemeral=True, silent=True, view=view)

        logger.info("Done.")

    @tasks.loop(time=[time(hour=h) for h in range(24)])
    async def run_hourly_tasks(self):
        """Run any hourly tasks we have"""
        
        for (channel, min) in self.state.get_active_match_tasks():
            logger.info("Scheduled match task triggered in %s", channel)
            msg_channel = self.bot.get_channel(int(channel))
            await matching.match_groups_in_channel(self.state, msg_channel, min)

        for (channel, _) in self.state.get_active_match_tasks(datetime.now() + timedelta(days=1)):
            logger.info("Reminding about scheduled task in %s", channel)
            msg_channel = self.bot.get_channel(int(channel))
            await msg_channel.send("Arf arf! just a reminder I'll be doin a matcherino in here in T-24hrs!"
                                   + "\nUse /join if you haven't already, or /pause if you want to skip a week :)")
