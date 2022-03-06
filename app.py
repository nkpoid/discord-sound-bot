#!/usr/bin/env python

import json
import logging
import os
import re
from asyncio import sleep
from typing import List

from discord import Bot, FFmpegPCMAudio, Member, Message, PCMVolumeTransformer, VoiceChannel
from discord.commands.context import ApplicationContext
from discord.ext import tasks


class SoundTable:
    def __init__(self, pattern: str, filename: str, volume: float):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.filename = filename
        self.volume = volume

    @classmethod
    def load(cls, table_path: str) -> List["SoundTable"]:
        with open(table_path) as f:
            data = json.load(f)

        return [SoundTable(elem["pattern"], elem["filename"], elem.get("volume", 1)) for elem in data]


bot = Bot()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

last_update_time: float = 0
sound_tables: List[SoundTable] = []


@bot.event
async def on_message(message: Message):
    if message.author.bot:
        return

    if not isinstance(message.author, Member):
        return

    matched = [elem for elem in sound_tables if elem.pattern.match(message.content)]
    item = next(iter(matched), None)
    if item is None:
        return

    if message.author.voice is None:
        logger.warning("User is not on voice channel.")
        return

    mentioned_user = next(iter(message.mentions), None)
    mentioned_voice_channel = next(iter([v for v in message.channel_mentions if isinstance(v, VoiceChannel)]), None)
    if isinstance(mentioned_user, Member) and mentioned_user.voice is not None:
        voice_channel = mentioned_user.voice.channel
        if voice_channel is None:
            return
    elif mentioned_voice_channel is not None:
        voice_channel = mentioned_voice_channel
    elif message.author.voice.channel is not None:
        voice_channel = message.author.voice.channel
    else:
        return

    vc = await voice_channel.connect()
    vc.play(PCMVolumeTransformer(FFmpegPCMAudio(os.path.join("./sounds", item.filename)), volume=item.volume))

    while vc.is_playing():
        await sleep(1)
    await vc.disconnect()


@bot.slash_command()
async def list(ctx: ApplicationContext):
    text = "\n".join([f"`{table.pattern.pattern}`" for table in sound_tables])
    await ctx.respond(text)


@tasks.loop(seconds=1)
async def config_updater():
    global last_update_time, sound_tables

    t = os.path.getmtime("./sounds.json")
    if t == last_update_time:
        return

    last_update_time = t
    sound_tables = SoundTable.load("./sounds.json")


config_updater.start()
bot.run(os.environ.get("DISCORD_TOKEN"))
