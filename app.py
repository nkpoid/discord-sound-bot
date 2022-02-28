#!/usr/bin/env python

import json
import logging
import os
from asyncio import sleep

import discord
from discord import FFmpegPCMAudio, Message, VoiceClient

client = discord.Client()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord")

with open("./sounds.json") as f:
    SOUND_TABLE = json.load(f)


@client.event
async def on_message(message: Message):
    user = message.author
    if user.bot:  # type: ignore
        return

    for pattern, sound_path in SOUND_TABLE.items():
        if message.content.startswith(pattern):
            if user.voice is None:
                logger.warning("User is not on voice channel.")
                return

            vc: VoiceClient = await user.voice.channel.connect()
            vc.play(FFmpegPCMAudio(sound_path))

            while vc.is_playing():
                await sleep(1)
            await vc.disconnect()


client.run(os.environ.get("DISCORD_TOKEN"))
