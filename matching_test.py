"""
    Test functions for Matchy
"""
import discord
import pytest
import matching


@pytest.mark.parametrize("matchees, per_group", [
    ([discord.Member.__new__(discord.Member)] * 100, 3),
    ([discord.Member.__new__(discord.Member)] * 12, 5),
    ([discord.Member.__new__(discord.Member)] * 11, 2),
    ([discord.Member.__new__(discord.Member)] * 356, 8),
])
def test_matchees_to_groups(matchees, per_group):
    """Test simple group matching works"""
    groups = matching.members_to_groups(matchees, per_group)
    for group in groups:
        # Ensure the group contains the right number of members
        assert len(group) >= per_group
        assert len(group) < per_group*2
