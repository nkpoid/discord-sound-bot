import json
import logging
import os
import re
import subprocess
from asyncio import sleep
from typing import List

from discord import Bot, Embed, FFmpegPCMAudio, Member, Message, PCMVolumeTransformer, VoiceChannel
from discord.commands import slash_command
from discord.commands.context import ApplicationContext
from discord.errors import ClientException
from discord.ext import commands, tasks

SOUNDS_TABLE_FILE = "./sounds.json"


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


def get_media_duration(path: str):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return float(result.stdout)


class JukeBoxCog(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        logging.basicConfig(level=logging.INFO)

        self.bot = bot
        self.logger = logging.getLogger("discord")

        self.last_update_time: float = 0
        self.sound_tables: List[SoundTable] = []

        self.config_updater.start()

    def cog_unload(self):
        self.config_updater.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot:
            return

        if not isinstance(message.author, Member):
            return

        matched = [elem for elem in self.sound_tables if elem.pattern.match(message.content)]
        table = next(iter(matched), None)
        if table is None:
            return

        mentioned_user = next(iter(message.mentions), None)
        mentioned_voice_channel = next(iter([v for v in message.channel_mentions if isinstance(v, VoiceChannel)]), None)
        if isinstance(mentioned_user, Member) and mentioned_user.voice is not None:
            voice_channel = mentioned_user.voice.channel
        elif mentioned_voice_channel is not None:
            voice_channel = mentioned_voice_channel
        elif message.author.voice is not None:
            voice_channel = message.author.voice.channel
        else:
            return

        if voice_channel is None:
            return

        try:
            vc = await voice_channel.connect()
        except ClientException as e:
            await message.reply(f"Error: {e}")
            return

        path = os.path.join("./sounds", table.filename)
        duration = get_media_duration(path)
        vc.play(PCMVolumeTransformer(FFmpegPCMAudio(path), volume=table.volume))
        await sleep(duration)
        await vc.disconnect()

    @slash_command()
    async def list(self, ctx: ApplicationContext):
        """現在Botに登録されているメッセージトリガーの正規表現を一覧します"""

        embed = Embed(
            title=f"Total {len(self.sound_tables)} conditions",
            description="\n".join([f"・`{table.pattern.pattern}`" for table in self.sound_tables]),
        )

        await ctx.respond(embed=embed, ephemeral=True)

    @tasks.loop(seconds=1)
    async def config_updater(self):
        t = os.path.getmtime(SOUNDS_TABLE_FILE)
        if t == self.last_update_time:
            return

        self.last_update_time = t
        self.sound_tables = SoundTable.load(SOUNDS_TABLE_FILE)


def setup(bot: Bot):
    bot.add_cog(JukeBoxCog(bot))
