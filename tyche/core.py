import typing
import asyncio
import json
import os
from random import choice
# When we're 3.7:
# from contextlib import AsyncExitStack

import aiohttp
import discord
from discord.ext.commands import Bot, Cog, command

from .ytdl import create_ytdl_source
from .errors import ParseError
from .generic import Generic
from .pbta import PbtA
from .wod import WoD

if not discord.opus.is_loaded():
    # Default on OS X installed by brew install opus
    default = "/usr/local/Cellar/opus/1.2.1/lib/libopus.dylib"
    discord.opus.load_opus(os.environ.get("LIBOPUS", default))


API_ROOT = os.environ.get("API_ROOT", "http://localhost:8000/api/")
API_KEY = os.environ.get("API_KEY", "invalid key")


BACKENDS = [Generic(), WoD(), PbtA()]


AFFIRMATIVES = [
    "Cool.",
    "On it.",
    "Sure thing.",
    "Aye aye.",
    "I'll try my best.",
    "You betcha!",
    "But of course.",
]


NEGATIVES = [
    "I'm so, so sorry, but no.",
    "I can't do that, Dave.",
    "Nah.",
    "Pffff. No.",
    "It is with the greatest regret that I inform you I cannot.",
    "Nuh-uh.",
    "ope nope nope nope nope nope nope nope nope nope nope nop",
]


# TODO: replace with Redis brain?
VOICE_CHANNELS = {}


async def fetch(url, guild_id):
    headers = {
        "Authorization": f"Token {API_KEY}",
    }
    params = {
        "server_id": guild_id,
    }
    full_url = f"{API_ROOT}{url}/"
    # When we're 3.7:
    # async with AsyncExitStack() as stack:
    #     session = await stack.enter_async_context(aiohttp.ClientSession())
    #     response = await stack.enter_async_context(
    #         session.get(url, params={"guild_id": guild_id})
    #     )
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url, headers=headers, params=params) as response:
            return await response.text()


async def get_prefix(bot, message):
    payload = await fetch("prefix", message.guild.id)
    return json.loads(payload)["prefix"]


async def is_acceptable(role_name, context):
    guild_acceptable_roles = await fetch("roles", context.message.guild.id)
    acceptable_roles = [
        r
        for r in context.message.guild.roles
        if r.name in guild_acceptable_roles
    ]
    try:
        return next(r for r in acceptable_roles if r.name == role_name)
    except StopIteration:
        return None


# Ready Bot One!

client = Bot(description="Tyche, the diceroller", command_prefix=get_prefix)


@client.event
async def on_ready():
    print(
        f"Logged in as {client.user.name} (ID:{client.user.id}) | "
        f"Connected to {str(len(client.guilds))} guilds"
    )
    print(f"Communicating with {API_ROOT}")
    print("--------")
    print(f"Current Discord.py Version: {discord.__version__}")
    print("--------")
    print(f"Use this link to invite {client.user.name}:")
    print(
        f"https://discordapp.com/oauth2/authorize"
        f"?client_id={client.user.id}&scope=bot&permissions=8"
    )


def _is_streaming(member):
    return any(isinstance(act, discord.Streaming) for act in member.activities)


@client.event
async def on_member_update(before, after):
    """
    This does a few things:
        1. Detects if there's a change in streaming status. If not, it
           bails.
        2. Detects if the server has a streaming role configured. If
           not, it bails.
        3. If the user has begun streaming, it applies the streaming
           role to them (only if they have the prerequisite role, if any
           such is configured).
        4. If the user has ceased streaming, it removes the streaming
           role from them.
    """
    is_before_streaming = _is_streaming(before)
    is_after_streaming = _is_streaming(after)
    change_in_streaming = is_before_streaming != is_after_streaming

    if not change_in_streaming:
        return

    response = await fetch("streaming_role", after.guild.id)
    response = json.loads(response)
    streaming_role_name = response["streaming_role"]
    streaming_role_requires = response["streaming_role_requires"]
    if streaming_role_name:
        avilable_roles = {
            r.name: r
            for r
            in after.guild.roles
        }
        streaming_role = avilable_roles.get(streaming_role_name, None)
        if not streaming_role:
            # Bail early if role missing:
            return
        if not _is_streaming(after):
            await after.remove_roles(streaming_role)
        user_roles = [
            role.name
            for role
            in after.roles
        ]
        if streaming_role_requires and streaming_role_requires not in user_roles:
            return
        if _is_streaming(after):
            await after.add_roles(streaming_role)


@client.command()
async def ping(ctx):
    """
    Respond with pong.
    """
    await ctx.send("pong")


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


class Roles(Cog):
    @command()
    async def list(self, ctx):
        """
        List all cosmetic roles on the current server.
        """
        guild_acceptable_roles = await fetch("roles", ctx.message.guild.id)
        acceptable_roles = ", ".join(sorted(
            f"`{r.name}`"
            for r in ctx.message.guild.roles
            if r.name in guild_acceptable_roles
        ))
        message = f"I can add or remove these roles from you: {acceptable_roles}"
        await ctx.send(message)

    @command()
    async def role(self, ctx, desired_role):
        """
        Add a cosmetic role to the current user.
        """
        role = await is_acceptable(desired_role, ctx)
        if role:
            await ctx.send(choice(AFFIRMATIVES))
            await ctx.message.author.add_roles(role)
        else:
            await ctx.send(choice(NEGATIVES))

    @command()
    async def unrole(self, ctx, desired_role):
        """
        Remove a cosmetic role from the current user.
        """
        role = await is_acceptable(desired_role, ctx)
        if role:
            await ctx.send(choice(AFFIRMATIVES))
            await ctx.message.author.remove_roles(role)
        else:
            await ctx.send(choice(NEGATIVES))


class Rolls(Cog):
    @command()
    async def roll(self, ctx, *dice):
        """
        Roll dice.

        XdY(+/-Z)  generic dice roller
        X(eY)(r)   Chronicles of Darkness roller
        +/-X       Powered by the Apocalypse roller
        """
        result = ""
        for backend in BACKENDS:
            try:
                result = backend.roll(" ".join(dice))
                if result:
                    await ctx.send(result)
                    return
            except ParseError:
                pass


def _format_lfc_message(obj):
    header = "**Currently looking for crew:**"
    message = '\n'.join(
        "{username} looking for {number} {activity}".format(
            username=msg["username"],
            number=msg["number"],
            activity=msg["activity"],
        )
        for msg
        in obj
    ) or "No one looking for crew."
    return f">>> {header}\n{message}"


# TODO: Store this in Redis
LFCS = []

class LookingForCrew(Cog):
    @command()
    async def looking(self, ctx, number, *activity):
        """
        Temporary command for testing.
        """
        # Create lfc JSON object
        obj = {
            "username": ctx.message.author.name,
            "number": number,
            "activity": " ".join(activity),
        }
        # Put it in Redis
        LFCS.append(obj)
        # Print whole lfc list to lfc channel (gotten from API)
        await ctx.send(_format_lfc_message(LFCS))

    @command()
    async def done(self, ctx, *args):
        """
        Temporary command for testing.
        """
        # Remove lfc object from Redis
        global LFCS
        LFCS = [
            lfc
            for lfc
            in LFCS
            if lfc["username"] != ctx.message.author.name
        ]
        # Print whole lfc list to lfc channel (gotten from API)
        await ctx.send(_format_lfc_message(LFCS))


# TODO: On Redis timeout:
# Print whole lfc list to lfc channel (gotten from API)


class Admin(Cog):
    def _is_admin(self, member, channel):
        return member.permissions_in(channel).administrator

    @command(hidden=True)
    async def clear(self, ctx):
        if self._is_admin(ctx.author, ctx.channel):
            async for message in ctx.channel.history(oldest_first=False):
                if not message.pinned:
                    print(f"Deleting message {message.id}")
                    await message.delete()
                    await asyncio.sleep(2)


client.add_cog(Music(client))
client.add_cog(Roles(client))
client.add_cog(Rolls(client))
client.add_cog(LookingForCrew(client))
client.add_cog(Admin(client))


def run():
    client.run(os.environ["DISCORD_TOKEN"])
