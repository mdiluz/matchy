"""
    matchy.py - Discord bot that matches people into groups
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
import matching
import history
import config
import re


Config = config.load()
History = history.load()

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
    return ctx.message.author.id in Config.owners


@bot.command()
@commands.dm_only()
@commands.check(owner_only)
async def sync(ctx: commands.Context):
    """Handle sync command"""
    msg = await ctx.reply("Reloading config...", ephemeral=True)
    Config.reload()
    logger.info("Reloaded config")

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


@bot.tree.command(description="Match up matchees")
@commands.guild_only()
@app_commands.describe(members_min="Minimum matchees per match (defaults to 3)",
                       matchee_role="Role for matchees (defaults to @Matchee)")
async def match(interaction: discord.Interaction, members_min: int = None, matchee_role: str = None):
    """Match groups of channel members"""

    logger.info("Handling request '/match group_min=%s matchee_role=%s'",
                members_min, matchee_role)
    logger.info("User %s from %s in #%s", interaction.user,
                interaction.guild.name, interaction.channel.name)

    # Sort out the defaults, if not specified they'll come in as None
    if not members_min:
        members_min = 3
    if not matchee_role:
        matchee_role = "Matchee"

    # Grab the roles and verify the given role
    matcher = matching.get_role_from_guild(interaction.guild, "Matcher")
    matcher = matcher and matcher in interaction.user.roles
    matchee = matching.get_role_from_guild(interaction.guild, matchee_role)
    if not matchee:
        await interaction.response.send_message(f"Server is missing '{matchee_role}' role :(", ephemeral=True)
        return

    # Create some example groups to show the user
    matchees = list(
        m for m in interaction.channel.members if matchee in m.roles)
    groups = matching.members_to_groups(
        matchees, History, members_min, allow_fallback=True)

    # Post about all the groups with a button to send to the channel
    groups_list = '\n'.join(matching.group_to_message(g) for g in groups)
    msg = f"Request accepted! I've generated some example groups for you:\n\n{groups_list}"
    view = discord.utils.MISSING

    if not matcher:
        # Let a non-matcher know why they don't have the button
        msg += "\n\nYou'll need the 'Matcher' role to post this to the channel, sorry!"
    else:
        # Otherwise set up the button
        msg += "\n\nClick the button to match up groups and send them to the channel.\n"
        view = discord.ui.View(timeout=None)
        view.add_item(DynamicGroupButton(members_min, matchee_role))

    await interaction.response.send_message(msg, ephemeral=True, silent=True, view=view)

    logger.info("Done.")


class DynamicGroupButton(discord.ui.DynamicItem[discord.ui.Button],
                         template=r'match:min:(?P<min>[0-9]+):role:(?P<role>[@\w\s]+)'):
    def __init__(self, min: int, role: str) -> None:
        super().__init__(
            discord.ui.Button(
                label='Match Groups!',
                style=discord.ButtonStyle.blurple,
                custom_id=f'match:min:{min}:role:{role}',
            )
        )
        self.min: int = min
        self.role: int = role

    # This is called when the button is clicked and the custom_id matches the template.
    @classmethod
    async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match: re.Match[str], /):
        min = int(match['min'])
        role = str(match['role'])
        return cls(min, role)

    async def callback(self, interaction: discord.Interaction) -> None:
        """Match up people when the button is pressed"""

        logger.info("Handling button press min=%s role=%s'", self.min, self.role)
        logger.info("User %s from %s in #%s", interaction.user,
                    interaction.guild.name, interaction.channel.name)
        
        # Let the user know we've recieved the message
        await interaction.response.send_message(content="Matchy is matching matchees...", ephemeral=True)

        # Grab the role
        matchee = matching.get_role_from_guild(interaction.guild, self.role)

        # Create our groups!
        matchees = list(
            m for m in interaction.channel.members if matchee in m.roles)
        groups = matching.members_to_groups(
            matchees, History, self.min, allow_fallback=True)

        # Send the groups
        for msg in (matching.group_to_message(g) for g in groups):
            await interaction.channel.send(msg)
        
        # Close off with a message
        await interaction.channel.send("That's all folks, happy matching and remember - DFTBA!")

        # Save the groups to the history
        History.save_groups_to_history(groups)

        logger.info("Done. Matched %s matchees into %s groups.",
                    len(matchees), len(groups))


if __name__ == "__main__":
    handler = logging.StreamHandler()
    bot.run(Config.token, log_handler=handler, root_logger=True)
