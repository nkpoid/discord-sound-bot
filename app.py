#!/usr/bin/env python

import json
import logging
import os
from asyncio import sleep
from random import choice
from typing import Dict, List, Union

import discord
from discord import FFmpegPCMAudio, Member, Message
from discord.ext import tasks

bot = discord.Bot()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

SOUND_MAP: Dict[str, Union[str, List[str]]]


@bot.event
async def on_message(message: Message):
    if message.author.bot:
        return

    if not isinstance(message.author, Member):
        return

    for pattern, path_candidate in SOUND_MAP.items():
        if message.content.startswith(pattern):
            if message.author.voice is None:
                logger.warning("User is not on voice channel.")
                return

            if message.author.voice.channel is None:
                return

            vc = await message.author.voice.channel.connect()
            path = choice(path_candidate) if isinstance(path_candidate, list) else path_candidate
            vc.play(FFmpegPCMAudio(path))

            while vc.is_playing():
                await sleep(1)
            await vc.disconnect()


@tasks.loop(seconds=10)
async def config_updater():
    with open("./sounds.json") as f:
        global SOUND_MAP
        SOUND_MAP = json.load(f)


config_updater.start()
bot.run(os.environ.get("DISCORD_TOKEN"))
