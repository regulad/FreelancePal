"""
Regulad's docker-discord-template
https://github.com/regulad/docker-discord-template
"""

import asyncio
import logging
import os
from typing import Optional, List, Tuple, Type

import discord
from discord.ext import commands


bot: commands.Bot = commands.Bot(
    command_prefix=os.environ.get("COMMAND_PREFIX", "!"),
    description="A template bot",
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
    )

    bot.start(os.environ["TOKEN"])
