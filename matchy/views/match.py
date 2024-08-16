"""
Class for a button that matches groups in a channel
"""
import logging
import discord
import re

import matchy.files.state as state
import matchy.matching as matching

logger = logging.getLogger("match_button")
logger.setLevel(logging.INFO)

# Increment when adjusting the custom_id so we don't confuse old users
_MATCH_BUTTON_CUSTOM_ID_VERSION = 1
_MATCH_BUTTON_CUSTOM_ID_PREFIX = f'match:v{_MATCH_BUTTON_CUSTOM_ID_VERSION}:'


class DynamicGroupButton(discord.ui.DynamicItem[discord.ui.Button],
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
        self.state = state.load_from_file()

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
        await matching.match_groups_in_channel(self.state, intrctn.channel, self.min)
