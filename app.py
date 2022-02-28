#!/usr/bin/env python

import json
import logging
import os
from asyncio import sleep
from typing import Dict

import discord
from discord import FFmpegPCMAudio, Message, VoiceClient
from discord.ext import tasks

client = discord.Client()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

SOUND_MAP: Dict


@client.event
async def on_message(message: Message):
    user = message.author
    if user.bot:  # type: ignore
        return

    for pattern, sound_path in SOUND_MAP.items():
        if message.content.startswith(pattern):
            if user.voice is None:
                logger.warning("User is not on voice channel.")
                return

            vc: VoiceClient = await user.voice.channel.connect()
            vc.play(FFmpegPCMAudio(sound_path))

            while vc.is_playing():
                await sleep(1)
            await vc.disconnect()


@tasks.loop(seconds=10)
async def config_updater():
    with open("./sounds/map.json") as f:
        global SOUND_MAP
        SOUND_MAP = json.load(f)


config_updater.start()
client.run(os.environ.get("DISCORD_TOKEN"))
