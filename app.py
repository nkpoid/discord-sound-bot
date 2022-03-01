#!/usr/bin/env python

import json
import logging
import os
from asyncio import sleep
from random import choice
from typing import Dict, List, Union

from discord import Bot, FFmpegPCMAudio, Member, Message
from discord.ext import tasks

bot = Bot()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

sound_map: Dict[str, Union[str, List[str]]] = {}


@bot.event
async def on_message(message: Message):
    if message.author.bot:
        return

    if not isinstance(message.author, Member):
        return

    matched = [v for k, v in sound_map.items() if message.content.startswith(k)]
    path_candidate = next(iter(matched), None)
    if path_candidate is None:
        return

    path = choice(path_candidate) if isinstance(path_candidate, list) else path_candidate

    if message.author.voice is None:
        logger.warning("User is not on voice channel.")
        return

    if message.author.voice.channel is None:
        return

    vc = await message.author.voice.channel.connect()
    vc.play(FFmpegPCMAudio(path))

    while vc.is_playing():
        await sleep(1)
    await vc.disconnect()


@tasks.loop(seconds=10)
async def config_updater():
    with open("./sounds.json") as f:
        global sound_map
        sound_map = json.load(f)


config_updater.start()
bot.run(os.environ.get("DISCORD_TOKEN"))
