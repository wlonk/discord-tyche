import typing
from random import choice
from discord.ext.commands import Cog, command

from ..ytdl import create_ytdl_source
from ..constants import AFFIRMATIVES, NEGATIVES


# TODO: replace with Redis brain?
VOICE_CHANNELS = {}


class Music(Cog):
    @command()
    async def play(self, ctx, url):
        """
        Play audio from YouTube.
        """
        await ctx.send(choice(AFFIRMATIVES))
        channel = ctx.message.author.voice.channel
        if channel:
            voice = await channel.connect()
            source = await create_ytdl_source(voice, url)
            VOICE_CHANNELS[channel.id] = voice, source
            source.volume = 0.1
            voice.play(source)

    @command()
    async def pause(self, ctx):
        """
        Pause playing audio.
        """
        channel = ctx.message.author.voice.channel
        if channel:
            voice, _ = VOICE_CHANNELS.get(channel.id)
            if voice:
                await ctx.send(choice(AFFIRMATIVES))
                voice.pause()
            else:
                await ctx.send(choice(NEGATIVES))

    @command()
    async def resume(self, ctx):
        """
        Resume playing audio.
        """
        channel = ctx.message.author.voice.channel
        if channel:
            voice, _ = VOICE_CHANNELS.get(channel.id)
            if voice:
                await ctx.send(choice(AFFIRMATIVES))
                voice.resume()
            else:
                await ctx.send(choice(NEGATIVES))

    @command()
    async def stop(self, ctx):
        """
        Stop playing audio.
        """
        channel = ctx.message.author.voice.channel
        if channel:
            voice, _ = VOICE_CHANNELS.get(channel.id)
            if voice:
                await ctx.send(choice(AFFIRMATIVES))
                voice.stop()
            else:
                await ctx.send(choice(NEGATIVES))

    @command()
    async def vol(self, ctx, volume: typing.Optional[float]):
        """
        Adjust Tyche's volume.

        Valid values are between 0.0 and 2.0, inclusive.
        """
        channel = ctx.message.author.voice.channel
        if channel:
            _, source = VOICE_CHANNELS.get(channel.id)
            if source and volume is not None and 0.0 <= volume <= 2.0:
                await ctx.send(choice(AFFIRMATIVES))
                source.volume = volume
            elif source:
                await ctx.send(f"Currently playing at {source.volume}.")
            else:
                await ctx.send(choice(NEGATIVES))

    @command()
    async def leave(self, ctx):
        """
        Leave the current user's voice channel.
        """
        channel = ctx.message.author.voice.channel
        if channel:
            voice, _ = VOICE_CHANNELS.get(channel.id)
            if voice:
                await voice.disconnect()
                VOICE_CHANNELS.pop(channel.id)
