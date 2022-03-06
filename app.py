#!/usr/bin/env python

import json
import logging
import os
import re
from asyncio import sleep
from typing import List

from discord import Bot, FFmpegPCMAudio, Member, Message
from discord.ext import tasks


class SoundTable:
    def __init__(self, pattern: str, filename: str):
        self.pattern: re.Pattern = re.compile(pattern, re.IGNORECASE)
        self.filename: str = filename

    @classmethod
    def load(cls, table_path: str) -> List["SoundTable"]:
        with open(table_path) as f:
            data = json.load(f)

        return [SoundTable(elem["pattern"], elem["filename"]) for elem in data]


bot = Bot()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

sound_tables: List[SoundTable] = []


@bot.event
async def on_message(message: Message):
    if message.author.bot:
        return

    if not isinstance(message.author, Member):
        return

    matched = [elem for elem in sound_tables if elem.pattern.match(message.content)]
    po = next(iter(matched), None)
    if po is None:
        return

    if message.author.voice is None:
        logger.warning("User is not on voice channel.")
        return

    if message.author.voice.channel is None:
        return

    vc = await message.author.voice.channel.connect()
    vc.play(FFmpegPCMAudio(os.path.join("./sounds", po.filename)))

    while vc.is_playing():
        await sleep(1)
    await vc.disconnect()


@tasks.loop(seconds=10)
async def config_updater():
    global sound_tables
    sound_tables = SoundTable.load("./sounds.json")


config_updater.start()
bot.run(os.environ.get("DISCORD_TOKEN"))
