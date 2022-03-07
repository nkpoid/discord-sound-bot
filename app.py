#!/usr/bin/env python

import os

from discord import Bot

EXTENSIONS = [
    "cogs.jukebox",
]

bot = Bot()

for extension in EXTENSIONS:
    bot.load_extension(extension)

bot.run(os.environ.get("DISCORD_TOKEN"))
